def _contact(**extra):
    payload = {
        "email": "amina@northbakery.example",
        "name": "Amina Shah",
        "company": "North Bakery",
        "industry": "Food",
        "region": "City",
        "employee_band": "1-10",
        "tags": ["Loyalty"],
    }
    payload.update(extra)
    return payload


def test_segment_matches_rules(client):
    segment = client.post(
        "/api/segments",
        json={
            "name": "Neighborhood regulars",
            "description": "Nearby loyalty customers",
            "rules": {
                "industries": ["food"],
                "regions": ["city"],
                "tags_any": ["loyalty"],
                "employee_bands": [],
            },
        },
    )
    assert segment.status_code == 201
    segment_id = segment.json()["id"]

    assert client.post("/api/contacts", json=_contact()).status_code == 201
    assert (
        client.post(
            "/api/contacts",
            json=_contact(
                email="leo@harborcycles.example",
                name="Leo Park",
                company="Harbor Cycles",
                industry="retail",
            ),
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/contacts",
            json=_contact(
                email="owen@ridge.example",
                name="Owen Blake",
                company="Ridge Supply",
                region="county",
            ),
        ).status_code
        == 201
    )

    matched = client.post(f"/api/segments/{segment_id}/match")
    assert matched.status_code == 200
    body = matched.json()
    assert body["count"] == 1
    assert body["sample"][0]["name"] == "Amina Shah"


def test_empty_rules_match_everyone(client):
    segment = client.post(
        "/api/segments",
        json={"name": "Everyone", "rules": {}},
    ).json()
    client.post("/api/contacts", json=_contact())
    client.post(
        "/api/contacts",
        json=_contact(email="leo@harborcycles.example", name="Leo Park", industry="retail"),
    )
    matched = client.post(f"/api/segments/{segment['id']}/match").json()
    assert matched["count"] == 2


def test_duplicate_contact_is_rejected(client):
    assert client.post("/api/contacts", json=_contact()).status_code == 201
    again = client.post("/api/contacts", json=_contact())
    assert again.status_code == 409


def test_delete_segment_clears_campaign_link(client):
    segment = client.post("/api/segments", json={"name": "Regulars", "rules": {}}).json()
    campaign = client.post(
        "/api/campaigns",
        json={
            "name": "Launch",
            "channel": "email",
            "segment_id": segment["id"],
        },
    ).json()
    assert client.delete(f"/api/segments/{segment['id']}").status_code == 204
    fetched = client.get(f"/api/campaigns/{campaign['id']}").json()
    assert fetched["segment_id"] is None
