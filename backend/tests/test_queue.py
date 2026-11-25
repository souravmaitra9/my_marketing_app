from datetime import UTC, datetime, timedelta

from app.services.dispatch import LoggingSender, MemoryBroker, run_once


class RejectingSender:
    def send(self, _post) -> None:
        raise RuntimeError("mailbox rejected the message")


def _campaign(client):
    response = client.post(
        "/api/campaigns",
        json={"name": "Spring loaf", "channel": "linkedin", "brief": "Thursday loaf."},
    )
    assert response.status_code == 201
    return response.json()


def _schedule(client, campaign_id, when):
    response = client.post(
        "/api/posts",
        json={
            "campaign_id": campaign_id,
            "body": "Rosemary loaf is back on Thursday.",
            "scheduled_for": when,
        },
    )
    assert response.status_code == 201
    return response.json()


def _dispatch(client, sender=None, now=None):
    with client.app.state.sessionmaker() as session:
        count = run_once(session, MemoryBroker(), sender or LoggingSender(), now=now)
    return count


def test_due_post_is_sent(client):
    campaign = _campaign(client)
    when = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
    post = _schedule(client, campaign["id"], when)
    assert post["channel"] == "linkedin"
    assert _dispatch(client) == 1
    listed = client.get("/api/posts", params={"status": "sent"}).json()
    assert listed["total"] == 1
    assert listed["items"][0]["id"] == post["id"]
    assert listed["items"][0]["sent_at"] is not None


def test_future_post_stays_queued(client):
    campaign = _campaign(client)
    when = (datetime.now(UTC) + timedelta(hours=3)).isoformat()
    _schedule(client, campaign["id"], when)
    assert _dispatch(client, now=datetime.now(UTC)) == 0
    assert client.get("/api/posts", params={"status": "queued"}).json()["total"] == 1


def test_cancelled_post_is_not_sent(client):
    campaign = _campaign(client)
    when = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
    post = _schedule(client, campaign["id"], when)
    cancelled = client.post(f"/api/posts/{post['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert _dispatch(client) == 0


def test_failed_send_can_be_retried(client):
    campaign = _campaign(client)
    when = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
    post = _schedule(client, campaign["id"], when)
    assert _dispatch(client, sender=RejectingSender()) == 0
    failed = client.get("/api/posts", params={"status": "failed"}).json()
    assert failed["items"][0]["last_error"] == "mailbox rejected the message"
    retried = client.post(f"/api/posts/{post['id']}/retry")
    assert retried.status_code == 200
    assert retried.json()["status"] == "queued"
    assert _dispatch(client) == 1


def test_second_worker_does_not_take_the_lock():
    locks: set[str] = set()
    first = MemoryBroker(locks)
    second = MemoryBroker(locks)
    assert first.acquire("leaflet:dispatch:1") is True
    assert second.acquire("leaflet:dispatch:1") is False
    first.release("leaflet:dispatch:1")
    assert second.acquire("leaflet:dispatch:1") is True
