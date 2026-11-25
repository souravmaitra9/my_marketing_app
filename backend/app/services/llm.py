import json

import httpx

from app.config import Settings

SYSTEM_PROMPT = (
    "You write short marketing copy for independent businesses. "
    'Respond with JSON only: {"variants":[{"subject":"","body":""}]}. '
    "For social posts leave subject empty. Keep each body under 500 characters. "
    "Do not invent prices, dates, or offers that are not in the brief."
)


class LlmClient:
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self._settings = settings
        self._transport = transport

    def configured(self) -> bool:
        return bool(self._settings.llm_base_url.strip())

    def complete(self, prompt: str) -> str:
        url = self._settings.llm_base_url.rstrip("/") + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self._settings.llm_api_key:
            headers["Authorization"] = f"Bearer {self._settings.llm_api_key}"
        payload = {
            "model": self._settings.llm_model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        }
        timeout = self._settings.llm_timeout_seconds
        with httpx.Client(timeout=timeout, transport=self._transport) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("unexpected completion payload") from exc
        if not isinstance(content, str) or not content.strip():
            raise ValueError("empty completion")
        return content


def parse_variants(raw: str) -> list[dict[str, str]]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("completion did not contain JSON")
    data = json.loads(text[start : end + 1])
    variants = data.get("variants") if isinstance(data, dict) else None
    if not isinstance(variants, list) or not variants:
        raise ValueError("completion did not contain variants")
    cleaned: list[dict[str, str]] = []
    for item in variants:
        if not isinstance(item, dict):
            continue
        body = str(item.get("body", "")).strip()
        if not body:
            continue
        subject = str(item.get("subject") or "").strip()
        cleaned.append({"subject": subject[:200], "body": body[:8000]})
    if not cleaned:
        raise ValueError("completion variants were empty")
    return cleaned
