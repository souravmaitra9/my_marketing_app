import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clock import as_utc, utcnow
from app.metrics import POSTS_DISPATCHED
from app.models import ScheduledPost

logger = logging.getLogger("leaflet.dispatch")


class LoggingSender:
    def send(self, post: ScheduledPost) -> None:
        if not str(post.body or "").strip():
            raise ValueError("post body is empty")
        logger.info(
            "dispatched post=%s channel=%s campaign=%s bytes=%s",
            post.id,
            post.channel,
            post.campaign_id,
            len(post.body),
        )


class MemoryBroker:
    """Process-local lock used in tests and single-process runs."""

    def __init__(self, locks: set[str] | None = None):
        self.locks = locks if locks is not None else set()

    def acquire(self, key: str) -> bool:
        if key in self.locks:
            return False
        self.locks.add(key)
        return True

    def release(self, key: str) -> None:
        self.locks.discard(key)


class RedisBroker:
    """Redis lock so two workers do not dispatch the same row.

    Postgres remains the queue. A lock that expires after a crash lets the
    next pass retry a post left in `sending`.
    """

    def __init__(self, client, ttl: int = 60):
        self.client = client
        self.ttl = ttl

    def acquire(self, key: str) -> bool:
        return bool(self.client.set(key, "1", nx=True, ex=self.ttl))

    def release(self, key: str) -> None:
        self.client.delete(key)

    def ping(self) -> None:
        self.client.ping()


def run_once(session: Session, broker, sender, now: datetime | None = None) -> int:
    moment = now or utcnow()
    posts = session.scalars(
        select(ScheduledPost)
        .where(ScheduledPost.status == "queued")
        .where(ScheduledPost.scheduled_for <= moment)
        .order_by(ScheduledPost.scheduled_for)
        .limit(50)
    ).all()
    finished = 0
    for post in posts:
        key = f"leaflet:dispatch:{post.id}"
        if not broker.acquire(key):
            continue
        try:
            if _dispatch(session, post.id, sender, moment):
                finished += 1
        finally:
            broker.release(key)
    return finished


def _dispatch(session: Session, post_id: str, sender, now: datetime) -> bool:
    post = session.get(ScheduledPost, post_id)
    if post is None or post.status != "queued":
        return False
    if as_utc(post.scheduled_for) > now:
        return False
    post.status = "sending"
    post.attempts += 1
    post.updated_at = now
    session.commit()
    try:
        sender.send(post)
    except Exception as exc:
        post.status = "failed"
        post.last_error = str(exc)[:500]
        post.updated_at = utcnow()
        session.commit()
        POSTS_DISPATCHED.labels(status="failed").inc()
        logger.warning("dispatch failed post=%s error=%s", post.id, post.last_error)
        return False
    post.status = "sent"
    post.sent_at = now
    post.last_error = ""
    post.updated_at = utcnow()
    session.commit()
    POSTS_DISPATCHED.labels(status="sent").inc()
    return True
