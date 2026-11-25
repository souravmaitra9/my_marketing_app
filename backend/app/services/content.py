import logging

import httpx
from sqlalchemy.orm import Session

from app.clock import utcnow
from app.metrics import CONTENT_GENERATED
from app.models import Campaign, ContentDraft
from app.services.llm import LlmClient, parse_variants

logger = logging.getLogger("leaflet.content")

_CTA = {
    "direct": "Tell us if you want in.",
    "warm": "Come by this week and say hello.",
    "formal": "Contact us to reserve a place.",
}


def fallback_variants(
    campaign: Campaign,
    kind: str,
    tone: str,
    audience: str,
    count: int,
) -> list[dict[str, str]]:
    cta = _CTA.get(tone, _CTA["direct"])
    brief = _clip(campaign.brief)
    audience = audience or "local customers"
    name = campaign.name.strip() or "Our shop"
    rows: list[dict[str, str]] = []
    for index in range(count):
        if kind == "email":
            subject, body = _email(index, name, brief, audience, cta)
        else:
            subject, body = "", _social(index, name, brief, audience, cta)
        rows.append({"subject": subject, "body": body})
    return rows


def generate_drafts(
    session: Session,
    campaign: Campaign,
    *,
    kind: str,
    tone: str,
    variants: int,
    llm: LlmClient,
    audience: str,
) -> list[ContentDraft]:
    provider = "fallback"
    parsed: list[dict[str, str]] | None = None
    if llm.configured():
        prompt = _prompt(campaign, kind, tone, variants, audience)
        try:
            parsed = parse_variants(llm.complete(prompt))[:variants]
            if parsed:
                provider = "llm"
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            logger.warning("model endpoint failed; using the local writer")
            parsed = None
    if not parsed:
        parsed = fallback_variants(campaign, kind, tone, audience, variants)
        provider = "fallback"

    rows: list[ContentDraft] = []
    for item in parsed:
        row = ContentDraft(
            campaign_id=campaign.id,
            kind=kind,
            tone=tone,
            subject=item["subject"],
            body=item["body"],
            provider=provider,
        )
        session.add(row)
        rows.append(row)
        CONTENT_GENERATED.labels(provider=provider, kind=kind).inc()
    campaign.updated_at = utcnow()
    session.flush()
    return rows


def _prompt(campaign: Campaign, kind: str, tone: str, variants: int, audience: str) -> str:
    return (
        f"Business campaign: {campaign.name}\n"
        f"Channel: {campaign.channel}\n"
        f"Kind: {kind}\n"
        f"Tone: {tone}\n"
        f"Audience: {audience}\n"
        f"Variants: {variants}\n"
        f"Brief: {campaign.brief or 'No extra brief.'}"
    )


def _clip(brief: str) -> str:
    text = " ".join((brief or "").split())
    if not text:
        return "We have something new in the shop."
    if len(text) > 320:
        text = text[:317].rstrip() + "..."
    if text[-1] not in ".!?":
        text += "."
    return text


def _social(index: int, name: str, brief: str, audience: str, cta: str) -> str:
    if index % 2 == 0:
        return f"{name}. {brief} Written for {audience}. {cta}"
    return f"{brief} {name} is sharing this with {audience}. {cta}"


def _email(index: int, name: str, brief: str, audience: str, cta: str) -> tuple[str, str]:
    if index % 2 == 0:
        subject = f"{name}: a note for {audience}"
        body = f"Hello,\n\n{brief}\n\nThis note is for {audience}. {cta}\n\n{name}"
    else:
        subject = f"From {name}"
        body = f"Hello,\n\nWe wanted {audience} to hear this directly. {brief}\n\n{cta}\n\n{name}"
    return subject, body
