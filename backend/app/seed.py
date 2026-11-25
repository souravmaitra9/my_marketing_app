from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.clock import utcnow
from app.models import Campaign, Contact, ScheduledPost, Segment


def seed(session: Session) -> None:
    existing = session.scalar(select(func.count()).select_from(Campaign))
    if existing:
        return
    segment = Segment(
        name="Neighborhood regulars",
        description="People who already buy from the shop and live nearby.",
        rules={
            "industries": ["food"],
            "regions": ["city"],
            "tags_any": ["loyalty"],
            "employee_bands": [],
        },
    )
    session.add(segment)
    session.flush()
    session.add_all(
        [
            Contact(
                email="amina@northbakery.example",
                name="Amina Shah",
                company="North Bakery",
                industry="food",
                region="city",
                employee_band="1-10",
                tags=["loyalty", "wholesale"],
            ),
            Contact(
                email="leo@harborcycles.example",
                name="Leo Park",
                company="Harbor Cycles",
                industry="retail",
                region="city",
                employee_band="1-10",
                tags=["loyalty"],
            ),
            Contact(
                email="priya@lantern.example",
                name="Priya Raman",
                company="Lantern Cafe",
                industry="food",
                region="city",
                employee_band="11-50",
                tags=["loyalty"],
            ),
            Contact(
                email="owen@ridge.example",
                name="Owen Blake",
                company="Ridge Supply",
                industry="food",
                region="county",
                employee_band="11-50",
                tags=["prospect"],
            ),
        ]
    )
    campaign = Campaign(
        name="Spring loaf launch",
        objective="awareness",
        channel="instagram",
        status="active",
        brief=(
            "Tell regulars the rosemary loaf is back on Thursdays. "
            "No discount. Pickup at the counter before noon."
        ),
        segment_id=segment.id,
    )
    session.add(campaign)
    session.flush()
    session.add(
        ScheduledPost(
            campaign_id=campaign.id,
            channel="instagram",
            subject="",
            body="Rosemary loaf is back on Thursdays. Counter pickup before noon.",
            scheduled_for=utcnow() + timedelta(days=1),
            status="queued",
        )
    )
    session.flush()
