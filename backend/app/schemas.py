from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.clock import as_utc


class Objective(StrEnum):
    awareness = "awareness"
    conversion = "conversion"
    retention = "retention"


class Channel(StrEnum):
    email = "email"
    instagram = "instagram"
    linkedin = "linkedin"
    facebook = "facebook"


class CampaignStatus(StrEnum):
    draft = "draft"
    active = "active"
    paused = "paused"
    completed = "completed"


class ContentKind(StrEnum):
    social = "social"
    email = "email"


class Tone(StrEnum):
    direct = "direct"
    warm = "warm"
    formal = "formal"


class PostStatus(StrEnum):
    queued = "queued"
    sending = "sending"
    sent = "sent"
    failed = "failed"
    cancelled = "cancelled"


class Page[T](BaseModel):
    items: list[T]
    total: int


class SegmentRules(BaseModel):
    industries: list[str] = Field(default_factory=list, max_length=20)
    regions: list[str] = Field(default_factory=list, max_length=20)
    tags_any: list[str] = Field(default_factory=list, max_length=20)
    employee_bands: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("industries", "regions", "tags_any", "employee_bands")
    @classmethod
    def _clean(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            item = value.strip().lower()
            if item and item not in cleaned:
                cleaned.append(item[:80])
        return cleaned


class SegmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    rules: SegmentRules = Field(default_factory=SegmentRules)


class SegmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    rules: SegmentRules | None = None


class SegmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    rules: SegmentRules
    created_at: datetime
    updated_at: datetime


class ContactCreate(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    name: str = Field(min_length=1, max_length=120)
    company: str = Field(default="", max_length=120)
    industry: str = Field(default="", max_length=80)
    region: str = Field(default="", max_length=80)
    employee_band: str = Field(default="", max_length=32)
    tags: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError("invalid email")
        return email

    @field_validator("industry", "region", "employee_band", "company", "name")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()

    @field_validator("tags")
    @classmethod
    def _tags(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            item = value.strip().lower()
            if item and item not in cleaned:
                cleaned.append(item[:32])
        return cleaned


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str
    company: str
    industry: str
    region: str
    employee_band: str
    tags: list[str]
    created_at: datetime


class MatchOut(BaseModel):
    count: int
    sample: list[ContactOut]


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    objective: Objective = Objective.awareness
    channel: Channel
    status: CampaignStatus = CampaignStatus.draft
    brief: str = Field(default="", max_length=4000)
    segment_id: str | None = None

    @field_validator("name", "brief")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    objective: Objective | None = None
    channel: Channel | None = None
    status: CampaignStatus | None = None
    brief: str | None = Field(default=None, max_length=4000)
    segment_id: str | None = None

    @field_validator("name", "brief")
    @classmethod
    def _strip(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class CampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    objective: str
    channel: str
    status: str
    brief: str
    segment_id: str | None
    created_at: datetime
    updated_at: datetime


class GenerateIn(BaseModel):
    kind: ContentKind
    tone: Tone = Tone.direct
    variants: int = Field(default=2, ge=1, le=3)


class DraftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    campaign_id: str
    kind: str
    tone: str
    subject: str
    body: str
    provider: str
    created_at: datetime


class PostCreate(BaseModel):
    campaign_id: str
    channel: Channel | None = None
    subject: str = Field(default="", max_length=200)
    body: str = Field(min_length=1, max_length=8000)
    scheduled_for: datetime

    @field_validator("subject", "body")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()

    @field_validator("body")
    @classmethod
    def _body(cls, value: str) -> str:
        if not value:
            raise ValueError("body is required")
        return value

    @field_validator("scheduled_for")
    @classmethod
    def _when(cls, value: datetime) -> datetime:
        return as_utc(value)


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    campaign_id: str
    channel: str
    subject: str
    body: str
    scheduled_for: datetime
    status: str
    attempts: int
    last_error: str
    created_at: datetime
    updated_at: datetime
    sent_at: datetime | None
