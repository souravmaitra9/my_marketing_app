from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Campaign, ContentDraft, Segment
from app.schemas import DraftOut, GenerateIn
from app.services.content import generate_drafts
from app.services.llm import LlmClient

router = APIRouter(prefix="/campaigns", tags=["content"])


def _audience(db: Session, campaign: Campaign) -> str:
    if not campaign.segment_id:
        return "local customers"
    segment = db.get(Segment, campaign.segment_id)
    if segment is None or not segment.name.strip():
        return "local customers"
    return segment.name.strip()


@router.post("/{campaign_id}/generate", response_model=list[DraftOut])
def generate(
    campaign_id: str,
    payload: GenerateIn,
    request: Request,
    db: Session = Depends(get_db),
) -> list[DraftOut]:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="campaign not found")
    llm = LlmClient(
        request.app.state.settings,
        transport=getattr(request.app.state, "llm_transport", None),
    )
    rows = generate_drafts(
        db,
        campaign,
        kind=payload.kind.value,
        tone=payload.tone.value,
        variants=payload.variants,
        llm=llm,
        audience=_audience(db, campaign),
    )
    return [DraftOut.model_validate(row) for row in rows]


@router.get("/{campaign_id}/drafts", response_model=list[DraftOut])
def list_drafts(campaign_id: str, db: Session = Depends(get_db)) -> list[DraftOut]:
    if db.get(Campaign, campaign_id) is None:
        raise HTTPException(status_code=404, detail="campaign not found")
    rows = db.scalars(
        select(ContentDraft)
        .where(ContentDraft.campaign_id == campaign_id)
        .order_by(ContentDraft.created_at.desc())
    ).all()
    return [DraftOut.model_validate(row) for row in rows]
