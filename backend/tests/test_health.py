def test_health_and_metrics(client):
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").json() == {"status": "ready"}
    assert client.get("/").json()["service"] == "leaflet"

    created = client.post(
        "/api/campaigns",
        json={"name": "Metric", "channel": "email", "brief": "Hello."},
    )
    assert created.status_code == 201
    body = client.get("/metrics").text
    assert "leaflet_campaigns_created_total" in body
    assert "leaflet_http_requests_total" in body
    assert 'path="/healthz"' in body
