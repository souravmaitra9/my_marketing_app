from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.clock import utcnow
from app.metrics import CAMPAIGNS_CREATED
from app.models import Campaign, Segment
from app.schemas import (
    CampaignCreate,
    CampaignOut,
    CampaignStatus,
    CampaignUpdate,
    Page,
)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _get_campaign(db: Session, campaign_id: str) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="campaign not found")
    return campaign


def _require_segment(db: Session, segment_id: str | None) -> None:
    if segment_id is None:
        return
    if db.get(Segment, segment_id) is None:
        raise HTTPException(status_code=404, detail="segment not found")


@router.post("", response_model=CampaignOut, status_code=201)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)) -> CampaignOut:
    _require_segment(db, payload.segment_id)
    campaign = Campaign(
        name=payload.name,
        objective=payload.objective.value,
        channel=payload.channel.value,
        status=payload.status.value,
        brief=payload.brief,
        segment_id=payload.segment_id,
    )
    db.add(campaign)
    db.flush()
    CAMPAIGNS_CREATED.inc()
    return CampaignOut.model_validate(campaign)


@router.get("", response_model=Page[CampaignOut])
def list_campaigns(
    status: CampaignStatus | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> Page[CampaignOut]:
    stmt = select(Campaign)
    count_stmt = select(func.count()).select_from(Campaign)
    if status is not None:
        stmt = stmt.where(Campaign.status == status.value)
        count_stmt = count_stmt.where(Campaign.status == status.value)
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(stmt.order_by(Campaign.updated_at.desc()).limit(limit).offset(offset)).all()
    return Page(items=[CampaignOut.model_validate(row) for row in rows], total=total)


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(campaign_id: str, db: Session = Depends(get_db)) -> CampaignOut:
    return CampaignOut.model_validate(_get_campaign(db, campaign_id))


@router.patch("/{campaign_id}", response_model=CampaignOut)
def update_campaign(
    campaign_id: str, payload: CampaignUpdate, db: Session = Depends(get_db)
) -> CampaignOut:
    campaign = _get_campaign(db, campaign_id)
    changes = payload.model_dump(exclude_unset=True)
    if "segment_id" in changes:
        _require_segment(db, changes["segment_id"])
        campaign.segment_id = changes["segment_id"]
    for field in ("name", "brief"):
        if field in changes:
            setattr(campaign, field, changes[field])
    for field in ("objective", "channel", "status"):
        if field in changes and changes[field] is not None:
            setattr(campaign, field, changes[field].value)
    campaign.updated_at = utcnow()
    db.flush()
    return CampaignOut.model_validate(campaign)


@router.delete("/{campaign_id}", status_code=204)
def delete_campaign(campaign_id: str, db: Session = Depends(get_db)) -> Response:
    campaign = _get_campaign(db, campaign_id)
    db.delete(campaign)
    db.flush()
    return Response(status_code=204)
