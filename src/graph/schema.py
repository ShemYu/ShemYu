"""Career graph node contracts. Resume clip/order is not modeled here."""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from src.schema import validate_date, validate_slug, validate_url


NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

Disclosure = Literal["public", "internal", "secret"]
ClaimStatus = Literal["confirmed", "derived", "interview-needed", "do-not-claim"]
FocusKind = Literal["product", "platform", "research", "leadership", "other"]
Ownership = Literal["led", "implemented", "designed", "proposed", "collaborated"]
ReleaseState = Literal["prototype", "internal-eval", "production", "launched", "absorbed"]
NodeType = Literal[
    "person",
    "company",
    "role",
    "focus",
    "claim",
    "metric",
    "award",
    "education",
    "certificate",
    "publication",
    "skill",
    "skill-group",
]


class NodeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: NonEmptyString
    type: NodeType
    title: NonEmptyString
    title_ja: str = ""
    disclosure: Disclosure = "public"

    _id = field_validator("id", mode="before")(validate_slug)


class Person(NodeModel):
    type: Literal["person"] = "person"
    label: str = ""
    label_ja: str = ""
    image: str = ""
    email: str = ""
    phone: str = ""
    url: str = ""
    summary: str = ""
    summary_ja: str = ""
    city: str = ""
    city_ja: str = ""
    region: str = ""
    region_ja: str = ""
    country_code: str = ""
    profiles: list[dict[str, str]] = Field(default_factory=list)

    _url = field_validator("url", "image", mode="before")(validate_url)


class Company(NodeModel):
    type: Literal["company"] = "company"


class Role(NodeModel):
    type: Literal["role"] = "role"
    person: NonEmptyString = "shem"
    company: NonEmptyString
    start: str
    end: str = ""
    location: str = ""
    location_ja: str = ""
    summary: str = ""
    summary_ja: str = ""
    awards: list[str] = Field(default_factory=list)

    _start = field_validator("start", mode="before")(
        lambda value: validate_date(value, allow_empty=False)
    )
    _end = field_validator("end", mode="before")(
        lambda value: validate_date(value, allow_present=True)
    )
    _company = field_validator("company", "person", mode="before")(validate_slug)


class Focus(NodeModel):
    type: Literal["focus"] = "focus"
    kind: FocusKind = "product"
    role: NonEmptyString
    start: str = ""
    end: str = ""
    problem: str = ""
    problem_ja: str = ""
    ownership: Ownership = "implemented"
    release: ReleaseState = "production"
    stack: list[str] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    do_not_claim: list[str] = Field(default_factory=list)

    _role = field_validator("role", mode="before")(validate_slug)
    _start = field_validator("start", mode="before")(validate_date)
    _end = field_validator("end", mode="before")(
        lambda value: validate_date(value, allow_present=True)
    )


class LocalizedText(BaseModel):
    model_config = ConfigDict(extra="forbid")

    en: NonEmptyString
    ja: str = ""


class Claim(NodeModel):
    type: Literal["claim"] = "claim"
    focus: NonEmptyString
    status: ClaimStatus = "confirmed"
    source: str = ""
    metric: str = ""
    text: LocalizedText
    do_not_claim: list[str] = Field(default_factory=list)

    _focus = field_validator("focus", mode="before")(validate_slug)

    @field_validator("metric", mode="before")
    @classmethod
    def _metric_slug(cls, value: Any) -> str:
        if value is None or value == "":
            return ""
        return validate_slug(value)


class Metric(NodeModel):
    type: Literal["metric"] = "metric"
    name: NonEmptyString
    display: NonEmptyString
    from_value: str = Field(default="", alias="from")
    to_value: str = Field(default="", alias="to")
    window: str = ""
    cohort: str = ""
    n_cases: Optional[int] = None
    n_items: Optional[int] = None
    source: str = ""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Award(NodeModel):
    type: Literal["award"] = "award"
    role: NonEmptyString
    date: str = ""
    text_ja: str = ""

    _role = field_validator("role", mode="before")(validate_slug)
    _date = field_validator("date", mode="before")(validate_date)


class Education(NodeModel):
    type: Literal["education"] = "education"
    institution: NonEmptyString
    institution_id: str = ""
    area: str = ""
    area_ja: str = ""
    study_type: str = ""
    study_type_ja: str = ""
    start: str = ""
    end: str = ""
    score: str = ""
    claims: list[str] = Field(default_factory=list)

    _start = field_validator("start", mode="before")(validate_date)
    _end = field_validator("end", mode="before")(
        lambda value: validate_date(value, allow_present=True)
    )


class Certificate(NodeModel):
    type: Literal["certificate"] = "certificate"
    issuer: str = ""
    date: str = ""

    _date = field_validator("date", mode="before")(validate_date)


class Publication(NodeModel):
    type: Literal["publication"] = "publication"
    publisher: str = ""
    released: str = ""
    url: str = ""
    summary: str = ""

    _url = field_validator("url", mode="before")(validate_url)
    _released = field_validator("released", mode="before")(validate_date)


class Skill(NodeModel):
    type: Literal["skill"] = "skill"


class SkillGroup(NodeModel):
    type: Literal["skill-group"] = "skill-group"
    skills: list[str] = Field(default_factory=list)


NODE_MODELS = {
    "person": Person,
    "company": Company,
    "role": Role,
    "focus": Focus,
    "claim": Claim,
    "metric": Metric,
    "award": Award,
    "education": Education,
    "certificate": Certificate,
    "publication": Publication,
    "skill": Skill,
    "skill-group": SkillGroup,
}


GraphNode = Union[
    Person,
    Company,
    Role,
    Focus,
    Claim,
    Metric,
    Award,
    Education,
    Certificate,
    Publication,
    Skill,
    SkillGroup,
]


class ParsedPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    node: GraphNode
    body: str = ""


def parse_node(data: dict[str, Any]) -> GraphNode:
    node_type = data.get("type")
    model = NODE_MODELS.get(node_type)
    if model is None:
        raise ValueError(f"unknown node type: {node_type!r}")
    return model.model_validate(data)


__all__ = [
    "Award",
    "Certificate",
    "Claim",
    "Company",
    "Education",
    "Focus",
    "GraphNode",
    "Metric",
    "NODE_MODELS",
    "ParsedPage",
    "Person",
    "Publication",
    "Role",
    "Skill",
    "SkillGroup",
    "parse_node",
]
