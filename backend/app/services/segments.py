from app.models import Contact
from app.schemas import SegmentRules


def contact_matches(contact: Contact, rules: SegmentRules) -> bool:
    """Match in process. Fine for a few thousand contacts."""
    if rules.industries and (contact.industry or "").lower() not in rules.industries:
        return False
    if rules.regions and (contact.region or "").lower() not in rules.regions:
        return False
    if rules.employee_bands and (contact.employee_band or "").lower() not in rules.employee_bands:
        return False
    if rules.tags_any:
        tags = {str(tag).lower() for tag in (contact.tags or [])}
        if tags.isdisjoint(rules.tags_any):
            return False
    return True
