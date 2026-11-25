from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.clock import utcnow
from app.models import Campaign, Contact, Segment
from app.schemas import (
    ContactCreate,
    ContactOut,
    MatchOut,
    Page,
    SegmentCreate,
    SegmentOut,
    SegmentRules,
    SegmentUpdate,
)
from app.services.segments import contact_matches

router = APIRouter(tags=["audience"])


def _segment_out(row: Segment) -> SegmentOut:
    return SegmentOut.model_validate(row)


def _get_segment(db: Session, segment_id: str) -> Segment:
    segment = db.get(Segment, segment_id)
    if segment is None:
        raise HTTPException(status_code=404, detail="segment not found")
    return segment


@router.post("/segments", response_model=SegmentOut, status_code=201)
def create_segment(payload: SegmentCreate, db: Session = Depends(get_db)) -> SegmentOut:
    segment = Segment(
        name=payload.name.strip(),
        description=payload.description.strip(),
        rules=payload.rules.model_dump(),
    )
    db.add(segment)
    db.flush()
    return _segment_out(segment)


@router.get("/segments", response_model=Page[SegmentOut])
def list_segments(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> Page[SegmentOut]:
    total = db.scalar(select(func.count()).select_from(Segment)) or 0
    rows = db.scalars(
        select(Segment).order_by(Segment.updated_at.desc()).limit(limit).offset(offset)
    ).all()
    return Page(items=[_segment_out(row) for row in rows], total=total)


@router.get("/segments/{segment_id}", response_model=SegmentOut)
def get_segment(segment_id: str, db: Session = Depends(get_db)) -> SegmentOut:
    return _segment_out(_get_segment(db, segment_id))


@router.patch("/segments/{segment_id}", response_model=SegmentOut)
def update_segment(
    segment_id: str, payload: SegmentUpdate, db: Session = Depends(get_db)
) -> SegmentOut:
    segment = _get_segment(db, segment_id)
    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes and changes["name"] is not None:
        segment.name = changes["name"].strip()
    if "description" in changes and changes["description"] is not None:
        segment.description = changes["description"].strip()
    if "rules" in changes and changes["rules"] is not None:
        segment.rules = SegmentRules.model_validate(changes["rules"]).model_dump()
    segment.updated_at = utcnow()
    db.flush()
    return _segment_out(segment)


@router.delete("/segments/{segment_id}", status_code=204)
def delete_segment(segment_id: str, db: Session = Depends(get_db)) -> Response:
    segment = _get_segment(db, segment_id)
    db.execute(update(Campaign).where(Campaign.segment_id == segment.id).values(segment_id=None))
    db.delete(segment)
    db.flush()
    return Response(status_code=204)


@router.post("/segments/{segment_id}/match", response_model=MatchOut)
def match_segment(segment_id: str, db: Session = Depends(get_db)) -> MatchOut:
    segment = _get_segment(db, segment_id)
    rules = SegmentRules.model_validate(segment.rules or {})
    contacts = db.scalars(select(Contact).order_by(Contact.name)).all()
    matched = [contact for contact in contacts if contact_matches(contact, rules)]
    sample = [ContactOut.model_validate(contact) for contact in matched[:5]]
    return MatchOut(count=len(matched), sample=sample)


@router.post("/contacts", response_model=ContactOut, status_code=201)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db)) -> ContactOut:
    contact = Contact(
        email=payload.email,
        name=payload.name,
        company=payload.company,
        industry=payload.industry.lower(),
        region=payload.region.lower(),
        employee_band=payload.employee_band.lower(),
        tags=payload.tags,
    )
    db.add(contact)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="contact already exists") from exc
    return ContactOut.model_validate(contact)


@router.get("/contacts", response_model=Page[ContactOut])
def list_contacts(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> Page[ContactOut]:
    total = db.scalar(select(func.count()).select_from(Contact)) or 0
    rows = db.scalars(select(Contact).order_by(Contact.name).limit(limit).offset(offset)).all()
    return Page(items=[ContactOut.model_validate(row) for row in rows], total=total)


@router.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: str, db: Session = Depends(get_db)) -> Response:
    contact = db.get(Contact, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="contact not found")
    db.delete(contact)
    db.flush()
    return Response(status_code=204)
