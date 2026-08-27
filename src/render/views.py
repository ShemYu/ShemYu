"""Resume/view documents. These select graph ids; they are not career facts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.schema import validate_slug


class ClaimView(BaseModel):
    """A sourced bullet with an optional document-specific editorial rewrite.

    ``id`` remains the primary claim for compatibility and axis labels.  A
    polished bullet may cite additional public facts through
    ``supporting_claims`` so implementation and outcome do not have to be
    rendered as disconnected bullets.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str
    supporting_claims: list[str] = Field(default_factory=list)
    text: str = ""
    text_ja: str = ""

    _id = field_validator("id", mode="before")(validate_slug)

    @field_validator("supporting_claims", mode="before")
    @classmethod
    def _validate_supporting_claims(cls, values: Any) -> Any:
        if values is None:
            return []
        if not isinstance(values, list):
            return values  # Let Pydantic report the invalid container type.
        return [validate_slug(value) for value in values]

    @model_validator(mode="after")
    def _claim_ids_are_unique(self) -> "ClaimView":
        if len(self.claim_ids) != len(set(self.claim_ids)):
            raise ValueError("a bullet cannot cite the same claim more than once")
        return self

    @property
    def claim_ids(self) -> list[str]:
        return [self.id, *self.supporting_claims]


class RoleView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str = ""
    title_ja: str = ""
    summary: str = ""
    summary_ja: str = ""
    claims: list[Union[str, ClaimView]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    include_summary: bool = True
    include_awards: bool = False

    _id = field_validator("id", mode="before")(validate_slug)


class ProjectView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    claims: list[Union[str, ClaimView]] = Field(default_factory=list)

    _id = field_validator("id", mode="before")(validate_slug)


class ContactView(BaseModel):
    """Contact items printed by a view, in addition to the person's name."""

    model_config = ConfigDict(extra="forbid")

    email: bool = True
    phone: bool = True
    location: bool = True
    profiles: list[str] = Field(default_factory=list)


class SkillRowView(BaseModel):
    """A curated, presentation-only skill row for concise documents."""

    model_config = ConfigDict(extra="forbid")

    title: str
    title_ja: str = ""
    skills: list[str]

    _skills = field_validator("skills", mode="before")(
        lambda values: [validate_slug(value) for value in values]
    )


class EducationView(BaseModel):
    """Education selection plus view-only display controls."""

    model_config = ConfigDict(extra="forbid")

    id: str
    include_score: bool = True

    _id = field_validator("id", mode="before")(validate_slug)


class CareerView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    locale: Literal["en", "ja"] = "en"
    editorial_standard: Literal["none", "senior-impact-v1"] = "none"
    person: str = "shem"
    headline: str = ""
    headline_ja: str = ""
    summary: str = ""
    summary_ja: str = ""
    contact: ContactView = Field(default_factory=ContactView)
    roles: list[RoleView]
    projects: list[ProjectView] = Field(default_factory=list)
    skill_groups: list[str] = Field(default_factory=list)
    skill_rows: list[SkillRowView] = Field(default_factory=list)
    education: list[Union[str, EducationView]] = Field(default_factory=list)
    certificates: list[str] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)
    publications: list[str] = Field(default_factory=list)
    axis: dict[str, str] = Field(default_factory=dict)

    _id = field_validator("id", "person", mode="before")(validate_slug)


def load_view(path: str | Path) -> CareerView:
    document = Path(path)
    raw: Any = yaml.safe_load(document.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{document}: view must be a mapping")
    return CareerView.model_validate(raw)


__all__ = [
    "CareerView",
    "ClaimView",
    "ContactView",
    "EducationView",
    "ProjectView",
    "RoleView",
    "SkillRowView",
    "load_view",
]
