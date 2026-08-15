"""Pydantic models for the profile data used by the resume generator.

The YAML files are the human-edited source of truth, while templates and the
AI provider consume the JSON-compatible representation returned by
``Profile.model_dump(mode="json")``.  Keeping the models here (rather than in
the loader or generator) gives both consumers the same contract.
"""

from __future__ import annotations

from datetime import date, datetime
import re
from typing import Annotated, Any
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def normalize_date(value: Any) -> Any:
    """Convert YAML date objects to deterministic ISO strings.

    ``yaml.safe_load`` turns an unquoted ``YYYY-MM-DD`` value into a
    ``datetime.date`` while leaving the quoted equivalent as ``str``.  The
    distinction is undesirable at the template/AI boundary, so both are
    represented as strings.  Four-digit integer years are normalized as well;
    other values are left alone and validated by the model field as usual (for
    example, ``"Present"`` remains ``"Present"``).
    """

    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    # YAML parses an unquoted year such as ``2017`` as an integer rather than
    # a string.  Treat four-digit year integers as date values too.
    if isinstance(value, int) and 1000 <= value <= 9999:
        return str(value)
    return value


_DATE_PATTERN = re.compile(r"^(?:\d{4}|\d{4}-\d{2}|\d{4}-\d{2}-\d{2})$")


def validate_date(value: Any, *, allow_empty: bool = True, allow_present: bool = False) -> str:
    """Normalize and validate a profile date value.

    Resume records intentionally support year-only and year/month values in
    addition to full dates.  They are checked for real calendar values rather
    than merely matching a regular expression.  ``Present`` is only valid for
    an open-ended end date.
    """

    value = normalize_date(value)
    if value is None or value == "":
        if allow_empty:
            return ""
        raise ValueError("date must not be empty")
    if not isinstance(value, str):
        raise ValueError("date must be a string")

    text = value.strip()
    if not text:
        if allow_empty:
            return ""
        raise ValueError("date must not be empty")
    if text.lower() == "present":
        if allow_present:
            return "Present"
        raise ValueError("Present is only valid for an end date")
    if not _DATE_PATTERN.fullmatch(text):
        raise ValueError("date must use YYYY, YYYY-MM, or YYYY-MM-DD")

    try:
        if len(text) == 4:
            date(int(text), 1, 1)
        elif len(text) == 7:
            date.fromisoformat(f"{text}-01")
        else:
            date.fromisoformat(text)
    except ValueError as error:
        raise ValueError("date is not a valid calendar date") from error
    return text


def validate_url(value: Any) -> str:
    """Validate a profile URL and return its normalized string value.

    Empty URLs are intentionally accepted because several existing records use
    ``url: ""`` for projects without a public link.  Non-empty values must be
    absolute HTTP(S) URLs; this rejects ``javascript:``, ``data:``, ``mailto:``
    and protocol-relative URLs before they can reach an HTML ``href``.
    """

    if value is None or value == "":
        return ""
    if not isinstance(value, str):
        raise ValueError("URL must be a string or an empty value")

    value = value.strip()
    if not value:
        return ""
    if any(character.isspace() for character in value):
        raise ValueError("URL must not contain whitespace")

    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must use the http or https scheme")
    return value


class ProfileModel(BaseModel):
    """Base model shared by every profile section."""

    model_config = ConfigDict(extra="forbid")


class Location(ProfileModel):
    address: str = ""
    postalCode: str = ""
    city: str = ""
    countryCode: str = ""
    region: str = ""


class SocialProfile(ProfileModel):
    network: NonEmptyString
    username: str = ""
    url: str = ""

    _url = field_validator("url", mode="before")(validate_url)


class Basics(ProfileModel):
    name: NonEmptyString
    label: str = ""
    image: str = ""
    email: str = ""
    phone: str = ""
    url: str = ""
    summary: str = ""
    location: Location = Field(default_factory=Location)
    profiles: list[SocialProfile] = Field(default_factory=list)

    _url = field_validator("url", "image", mode="before")(validate_url)


class Work(ProfileModel):
    name: NonEmptyString
    position: NonEmptyString
    startDate: str
    endDate: str = ""
    location: str = ""
    summary: str = ""
    highlights: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)

    _start_date = field_validator("startDate", mode="before")(
        lambda value: validate_date(value, allow_empty=False)
    )
    _end_date = field_validator("endDate", mode="before")(
        lambda value: validate_date(value, allow_present=True)
    )


class Education(ProfileModel):
    institution: NonEmptyString
    area: NonEmptyString
    studyType: NonEmptyString
    startDate: str
    endDate: str = ""
    score: str = ""
    courses: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)

    _start_date = field_validator("startDate", mode="before")(
        lambda value: validate_date(value, allow_empty=False)
    )
    _end_date = field_validator("endDate", mode="before")(
        lambda value: validate_date(value, allow_present=True)
    )


class Certificate(ProfileModel):
    name: NonEmptyString
    date: str = ""
    issuer: str = ""

    _date = field_validator("date", mode="before")(validate_date)


class Publication(ProfileModel):
    name: NonEmptyString
    publisher: str = ""
    releaseDate: str = ""
    url: str = ""
    summary: str = ""

    _date = field_validator("releaseDate", mode="before")(validate_date)
    _url = field_validator("url", mode="before")(validate_url)


class Skill(ProfileModel):
    name: NonEmptyString
    keywords: list[str] = Field(default_factory=list)


class Project(ProfileModel):
    name: NonEmptyString
    description: str = ""
    url: str = ""
    startDate: str = ""
    endDate: str = ""
    keywords: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)

    _start_date = field_validator("startDate", mode="before")(
        validate_date
    )
    _end_date = field_validator("endDate", mode="before")(
        lambda value: validate_date(value, allow_present=True)
    )
    _url = field_validator("url", mode="before")(validate_url)


class Profile(ProfileModel):
    """Complete profile contract consumed by templates and AI."""

    basics: Basics
    work: list[Work] = Field(min_length=1)
    education: list[Education] = Field(default_factory=list)
    certificates: list[Certificate] = Field(default_factory=list)
    publications: list[Publication] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)


def profile_dict(value: Profile | dict[str, Any]) -> dict[str, Any]:
    """Validate a profile and return a JSON-friendly dictionary."""

    model = value if isinstance(value, Profile) else Profile.model_validate(value)
    return model.model_dump(mode="json")


__all__ = [
    "Basics",
    "Certificate",
    "Education",
    "Location",
    "Profile",
    "ProfileModel",
    "Project",
    "Publication",
    "Skill",
    "SocialProfile",
    "Work",
    "normalize_date",
    "validate_date",
    "profile_dict",
    "validate_url",
]
