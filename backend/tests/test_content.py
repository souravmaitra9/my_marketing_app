import json

import httpx


def _campaign(client, **extra):
    payload = {
        "name": "Spring loaf",
        "channel": "instagram",
        "brief": "Rosemary loaf returns Thursday.",
        "segment_id": None,
    }
    payload.update(extra)
    response = client.post("/api/campaigns", json=payload)
    assert response.status_code == 201
    return response.json()


def test_fallback_is_deterministic(client):
    campaign = _campaign(client)
    path = f"/api/campaigns/{campaign['id']}/generate"
    body = {"kind": "social", "tone": "direct", "variants": 2}
    first = client.post(path, json=body).json()
    second = client.post(path, json=body).json()
    assert [item["body"] for item in first] == [item["body"] for item in second]
    assert first[0]["provider"] == "fallback"
    assert first[0]["body"] != first[1]["body"]
    assert "Rosemary loaf returns Thursday." in first[0]["body"]
    assert "local customers" in first[0]["body"]
    drafts = client.get(f"/api/campaigns/{campaign['id']}/drafts").json()
    assert len(drafts) == 4


def test_email_fallback_includes_subject(client):
    campaign = _campaign(client)
    drafts = client.post(
        f"/api/campaigns/{campaign['id']}/generate",
        json={"kind": "email", "tone": "formal", "variants": 1},
    ).json()
    assert drafts[0]["subject"]
    assert "Contact us to reserve a place." in drafts[0]["body"]


def test_llm_draft_uses_endpoint(client):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["auth"] = request.headers.get("authorization")
        seen["body"] = json.loads(request.content)
        payload = {"variants": [{"subject": "", "body": "Counter pickup before noon."}]}
        message = {"content": json.dumps(payload)}
        return httpx.Response(200, json={"choices": [{"message": message}]})

    client.app.state.settings.llm_base_url = "http://llm.test/v1"
    client.app.state.settings.llm_api_key = "test-key"
    client.app.state.settings.llm_model = "test-model"
    client.app.state.llm_transport = httpx.MockTransport(handler)

    campaign = _campaign(client)
    drafts = client.post(
        f"/api/campaigns/{campaign['id']}/generate",
        json={"kind": "social", "tone": "warm", "variants": 1},
    ).json()
    assert seen["path"] == "/v1/chat/completions"
    assert seen["auth"] == "Bearer test-key"
    assert seen["body"]["model"] == "test-model"
    assert drafts[0]["provider"] == "llm"
    assert drafts[0]["body"] == "Counter pickup before noon."


def test_llm_failure_falls_back(client):
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "down"})

    client.app.state.settings.llm_base_url = "http://llm.test/v1"
    client.app.state.llm_transport = httpx.MockTransport(handler)
    campaign = _campaign(client)
    drafts = client.post(
        f"/api/campaigns/{campaign['id']}/generate",
        json={"kind": "social", "tone": "direct", "variants": 1},
    ).json()
    assert drafts[0]["provider"] == "fallback"
    assert "Spring loaf." in drafts[0]["body"]
