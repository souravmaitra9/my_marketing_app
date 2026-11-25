def _campaign(name="Spring loaf", **extra):
    payload = {
        "name": name,
        "objective": "awareness",
        "channel": "instagram",
        "brief": "Rosemary loaf returns Thursday.",
        "status": "draft",
    }
    payload.update(extra)
    return payload


def test_campaign_crud(client):
    created = client.post("/api/campaigns", json=_campaign())
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "draft"
    assert body["channel"] == "instagram"

    listed = client.get("/api/campaigns")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    filtered = client.get("/api/campaigns", params={"status": "active"})
    assert filtered.json()["total"] == 0

    patched = client.patch(
        f"/api/campaigns/{body['id']}",
        json={"status": "active", "brief": "Pickup before noon."},
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "active"
    assert patched.json()["brief"] == "Pickup before noon."

    fetched = client.get(f"/api/campaigns/{body['id']}")
    assert fetched.json()["status"] == "active"

    deleted = client.delete(f"/api/campaigns/{body['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/campaigns/{body['id']}").status_code == 404


def test_campaign_rejects_unknown_channel(client):
    response = client.post("/api/campaigns", json=_campaign(channel="fax"))
    assert response.status_code == 422


def test_campaign_requires_known_segment(client):
    response = client.post(
        "/api/campaigns",
        json=_campaign(segment_id="00000000-0000-0000-0000-000000000000"),
    )
    assert response.status_code == 404


def test_delete_campaign_removes_drafts_and_posts(client):
    campaign = client.post("/api/campaigns", json=_campaign()).json()
    generated = client.post(
        f"/api/campaigns/{campaign['id']}/generate",
        json={"kind": "social", "tone": "direct", "variants": 1},
    )
    assert generated.status_code == 200
    scheduled = client.post(
        "/api/posts",
        json={
            "campaign_id": campaign["id"],
            "body": "Thursday loaf.",
            "scheduled_for": "2026-12-01T15:00:00Z",
        },
    )
    assert scheduled.status_code == 201
    assert client.delete(f"/api/campaigns/{campaign['id']}").status_code == 204
    assert client.get("/api/posts").json()["total"] == 0
    assert client.get(f"/api/campaigns/{campaign['id']}/drafts").status_code == 404
