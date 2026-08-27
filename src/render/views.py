"""Resume/view documents. These select graph ids; they are not career facts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.schema import validate_slug


class RoleView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    claims: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    include_awards: bool = False

    _id = field_validator("id", mode="before")(validate_slug)


class ProjectView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    claims: list[str] = Field(default_factory=list)

    _id = field_validator("id", mode="before")(validate_slug)


class CareerView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    locale: str = "en"
    person: str = "shem"
    roles: list[RoleView]
    projects: list[ProjectView] = Field(default_factory=list)
    skill_groups: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    certificates: list[str] = Field(default_factory=list)
    publications: list[str] = Field(default_factory=list)
    axis: dict[str, str] = Field(default_factory=dict)

    _id = field_validator("id", "person", mode="before")(validate_slug)


def load_view(path: str | Path) -> CareerView:
    document = Path(path)
    raw: Any = yaml.safe_load(document.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{document}: view must be a mapping")
    return CareerView.model_validate(raw)


__all__ = ["CareerView", "ProjectView", "RoleView", "load_view"]
