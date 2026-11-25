from app.seed import seed


def test_seed_loads_demo_once(client):
    with client.app.state.sessionmaker() as session:
        seed(session)
        session.commit()
    with client.app.state.sessionmaker() as session:
        seed(session)
        session.commit()

    campaigns = client.get("/api/campaigns").json()
    assert campaigns["total"] == 1
    campaign = campaigns["items"][0]
    assert campaign["name"] == "Spring loaf launch"
    assert campaign["segment_id"]

    contacts = client.get("/api/contacts").json()
    assert contacts["total"] == 4
    posts = client.get("/api/posts").json()
    assert posts["total"] == 1
    assert posts["items"][0]["status"] == "queued"

    matched = client.post(f"/api/segments/{campaign['segment_id']}/match").json()
    assert matched["count"] == 2
    assert {item["name"] for item in matched["sample"]} == {"Amina Shah", "Priya Raman"}
