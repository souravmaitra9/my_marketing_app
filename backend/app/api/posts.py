from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.clock import utcnow
from app.models import Campaign, ScheduledPost
from app.schemas import Page, PostCreate, PostOut, PostStatus

router = APIRouter(prefix="/posts", tags=["posts"])


def _get_post(db: Session, post_id: str) -> ScheduledPost:
    post = db.get(ScheduledPost, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    return post


@router.post("", response_model=PostOut, status_code=201)
def create_post(payload: PostCreate, db: Session = Depends(get_db)) -> PostOut:
    campaign = db.get(Campaign, payload.campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="campaign not found")
    channel = payload.channel.value if payload.channel is not None else campaign.channel
    post = ScheduledPost(
        campaign_id=campaign.id,
        channel=channel,
        subject=payload.subject,
        body=payload.body,
        scheduled_for=payload.scheduled_for,
        status=PostStatus.queued.value,
    )
    db.add(post)
    campaign.updated_at = utcnow()
    db.flush()
    return PostOut.model_validate(post)


@router.get("", response_model=Page[PostOut])
def list_posts(
    status: PostStatus | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> Page[PostOut]:
    stmt = select(ScheduledPost)
    count_stmt = select(func.count()).select_from(ScheduledPost)
    if status is not None:
        stmt = stmt.where(ScheduledPost.status == status.value)
        count_stmt = count_stmt.where(ScheduledPost.status == status.value)
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(
        stmt.order_by(ScheduledPost.scheduled_for.asc()).limit(limit).offset(offset)
    ).all()
    return Page(items=[PostOut.model_validate(row) for row in rows], total=total)


@router.post("/{post_id}/cancel", response_model=PostOut)
def cancel_post(post_id: str, db: Session = Depends(get_db)) -> PostOut:
    post = _get_post(db, post_id)
    if post.status != PostStatus.queued.value:
        raise HTTPException(status_code=409, detail="only queued posts can be cancelled")
    post.status = PostStatus.cancelled.value
    post.updated_at = utcnow()
    db.flush()
    return PostOut.model_validate(post)


@router.post("/{post_id}/retry", response_model=PostOut)
def retry_post(post_id: str, db: Session = Depends(get_db)) -> PostOut:
    post = _get_post(db, post_id)
    if post.status not in {PostStatus.failed.value, PostStatus.sending.value}:
        raise HTTPException(status_code=409, detail="only failed or stuck posts can be retried")
    post.status = PostStatus.queued.value
    post.last_error = ""
    post.updated_at = utcnow()
    db.flush()
    return PostOut.model_validate(post)
