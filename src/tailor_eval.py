"""Tailor eval: source-faithful scanners, golden cases, and opt-in live repeats."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from src.ai import (
    DEFAULT_PROVIDER,
    PROMPT_INSTRUCTIONS,
    TailoringPlan,
    TailorTransportError,
    assemble_profile,
    build_provider,
)
from src.generator import Jinja2Generator, for_public_resume, format_date
from src.loader import YamlDataLoader


PUBLIC_SCAN_TEMPLATES = ("resume.md.j2", "resume.html.j2")
BIBLE_SCAN_TEMPLATE = "resume_bible.html.j2"
DEFAULT_CASES_DIR = "tests/tailor_eval/cases"
DEFAULT_OUTPUT_DIR = "output/tailor_eval"
DEFAULT_LIVE_REPEATS = 5
MIN_LIVE_REPEATS = 3
MAX_LIVE_REPEATS = 9
JACCARD_PASS = 0.60
_REPO_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATES_DIR = _REPO_ROOT / "templates"
LIVE_FRAGMENTS_PATH = _REPO_ROOT / "tests" / "tailor_eval" / "fragments_live.yaml"
ASSEMBLER_VERSION = "1"
_KNOWN_PROVIDERS = frozenset({"openai", "xai"})
_PROVIDER_KEY = {"openai": "OPENAI_API_KEY", "xai": "XAI_API_KEY"}

SECTION_HEADINGS = frozenset(
    {
        "Summary",
        "Experience",
        "Education",
        "Skills",
        "Certificates",
        "Publications",
        "Projects",
        "Professional Summary",
        "Technical Skills",
        "Professional Experience",
        "Certifications",
        "Contact",
    }
)
_VOID_TAGS = frozenset(
    {
        "meta",
        "link",
        "img",
        "br",
        "hr",
        "input",
        "col",
        "base",
        "area",
        "embed",
        "source",
        "track",
        "wbr",
    }
)
_KEYWORDS_LINE = re.compile(r"^\*\*Keywords\*\*:")
_WORK_PROJECT_NAME_FIELDS = (
    ("must_include_work", "work"),
    ("must_exclude_work", "work"),
    ("preferred_work", "work"),
    ("must_include_projects", "projects"),
    ("must_exclude_projects", "projects"),
    ("preferred_projects", "projects"),
)

QUALITY_STOPLIST = frozenset(
    {
        "that",
        "this",
        "with",
        "from",
        "have",
        "will",
        "your",
        "about",
        "into",
        "than",
        "them",
        "then",
        "also",
        "such",
        "only",
        "over",
        "plus",
        "need",
        "must",
        "able",
        "work",
        "team",
        "role",
        "using",
        "including",
        "across",
        "their",
        "more",
        "other",
        "well",
        "been",
        "were",
        "they",
        "this",
        "what",
        "when",
        "where",
    }
)
LEADERSHIP_JD = re.compile(r"\blead(?:er|ership)?\b|\bmanager\b|\bmentoring\b")
IC_JD = re.compile(r"\bimplement|\bproduction\b|\bengineer\b")
LEADERSHIP_SRC = re.compile(r"\blead|\bteam\b")
IC_SRC = re.compile(r"\bimplement|\bbuilt\b|\bproduction\b")


class GoldenCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    jd: str
    profile_dir: str = "tests/tailor_eval/profiles/synthetic"
    must_include_work: list[str] = Field(default_factory=list)
    must_exclude_work: list[str] = Field(default_factory=list)
    must_include_projects: list[str] = Field(default_factory=list)
    must_exclude_projects: list[str] = Field(default_factory=list)
    must_include_highlights: list[str] = Field(default_factory=list)
    preferred_work: list[str] = Field(default_factory=list)
    preferred_projects: list[str] = Field(default_factory=list)
    forbidden_tokens: list[str] = Field(default_factory=list)
    min_keyword_coverage: float | None = None


class ScanFinding(BaseModel):
    severity: Literal["fail", "warn"]
    code: str
    message: str
    template: str | None = None


class RunRecord(BaseModel):
    case_id: str
    provider: str | None
    model: str | None
    plan: dict | None
    selected_work: list[str]
    selected_projects: list[str]
    findings: list[ScanFinding]
    quality: dict[str, float]
    elapsed_s: float | None = None
    usage: dict[str, int] | None = None
    error_class: str | None = None


class EvalReport(BaseModel):
    offline: bool
    repeats: int
    prompt_version: str
    jaccard: float | None
    passed: bool
    elapsed_s: float
    records: list[RunRecord]


@dataclass
class PublicFields:
    basics: dict[str, Any]
    work: list[dict[str, Any]]
    projects: list[dict[str, Any]]
    education: list[dict[str, Any]]
    skills: list[dict[str, Any]]
    certificates: list[dict[str, Any]]
    publications: list[dict[str, Any]]
    allowed: frozenset[str]


@dataclass
class ExtractedItem:
    title: str | None = None
    name: str | None = None
    date: str | None = None
    summary: str | None = None
    bullets: list[str] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)


@dataclass
class ExtractedPublic:
    name: str | None = None
    label: str | None = None
    summary: str | None = None
    headings: list[str] = field(default_factory=list)
    contact: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)
    work: list[ExtractedItem] = field(default_factory=list)
    projects: list[ExtractedItem] = field(default_factory=list)
    education: list[ExtractedItem] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    certificates: list[str] = field(default_factory=list)
    publications: list[str] = field(default_factory=list)
    skill_names: list[str] = field(default_factory=list)
    cert_mains: list[str] = field(default_factory=list)
    edu_mains: list[str] = field(default_factory=list)
    edu_details: list[str] = field(default_factory=list)


@dataclass
class BibleItem:
    kind: str
    title: str = ""
    name: str = ""
    highlights: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


@dataclass
class ExtractedBible:
    work: list[BibleItem] = field(default_factory=list)
    projects: list[BibleItem] = field(default_factory=list)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return html.unescape(str(value)).strip()


def _add_allowed(allowed: set[str], value: Any) -> None:
    text = _norm(value)
    if text:
        allowed.add(text)


def index_by_name(items: list[dict[str, Any]], name: str) -> int:
    matches = [i for i, item in enumerate(items) if item.get("name") == name]
    if len(matches) != 1:
        raise ValueError(f"identity {name!r} matched {len(matches)} items")
    return matches[0]


def load_case(path: Path | str) -> GoldenCase:
    case_path = Path(path)
    raw = yaml.safe_load(case_path.read_text(encoding="utf-8"))
    return GoldenCase.model_validate(raw)


def load_live_fragments(path: Path | str | None = None) -> list[str]:
    fragment_path = Path(path) if path is not None else LIVE_FRAGMENTS_PATH
    if not fragment_path.is_file():
        return []
    data = yaml.safe_load(fragment_path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        items = data.get("fragments") or []
    else:
        items = data or []
    return [str(item) for item in items]


def _uses_live_profile(case: GoldenCase) -> bool:
    return Path(case.profile_dir).name == "data"


def public_fields(profile: dict[str, Any]) -> PublicFields:
    pub = for_public_resume(profile)
    allowed: set[str] = set(SECTION_HEADINGS)
    allowed.update({"Present", "|"})

    basics = dict(pub.get("basics") or {})
    for key in ("name", "label", "email", "phone", "url", "summary"):
        _add_allowed(allowed, basics.get(key))
    email = basics.get("email") or ""
    url = basics.get("url") or ""
    if email:
        _add_allowed(allowed, f"[Email](mailto:{email})")
    if url:
        _add_allowed(allowed, f"[Website]({url})")
    for profile_link in basics.get("profiles") or []:
        network = profile_link.get("network") or ""
        href = profile_link.get("url") or ""
        if network:
            _add_allowed(allowed, f"[{network}]({href})")

    work = [dict(item) for item in pub.get("work") or []]
    for item in work:
        _add_item_fields(allowed, item, kind="work")
    projects = [dict(item) for item in pub.get("projects") or []]
    for item in projects:
        _add_item_fields(allowed, item, kind="project")
    education = [dict(item) for item in pub.get("education") or []]
    for item in education:
        _add_education_fields(allowed, item)
    skills = [dict(item) for item in pub.get("skills") or []]
    for item in skills:
        name = item.get("name") or ""
        keywords = [str(part) for part in item.get("keywords") or []]
        _add_allowed(allowed, name)
        for keyword in keywords:
            _add_allowed(allowed, keyword)
        if name:
            _add_allowed(allowed, f"**{name}**: " + ", ".join(keywords))
            _add_allowed(allowed, f"{name}:")
        if name == "Language":
            _add_allowed(allowed, "Languages:")
    certificates = [dict(item) for item in pub.get("certificates") or []]
    for item in certificates:
        name = item.get("name") or ""
        issuer = item.get("issuer") or ""
        _add_allowed(allowed, name)
        _add_allowed(allowed, issuer)
        _add_allowed(allowed, item.get("date"))
        if item.get("date"):
            _add_allowed(allowed, format_date(item.get("date")))
        if name and issuer:
            _add_allowed(allowed, f"{name} ({issuer})")
        elif name:
            _add_allowed(allowed, name)
    publications = [dict(item) for item in pub.get("publications") or []]
    for item in publications:
        name = item.get("name") or ""
        publisher = item.get("publisher") or ""
        href = item.get("url") or ""
        _add_allowed(allowed, name)
        _add_allowed(allowed, publisher)
        _add_allowed(allowed, href)
        _add_allowed(allowed, item.get("summary"))
        if name:
            _add_allowed(allowed, f"[{name}]({href}) - {publisher}")

    return PublicFields(
        basics=basics,
        work=work,
        projects=projects,
        education=education,
        skills=skills,
        certificates=certificates,
        publications=publications,
        allowed=frozenset(allowed),
    )


def _add_date_pair(allowed: set[str], start: Any, end: Any, *, empty_end_is_present: bool) -> None:
    start_text = _norm(start)
    end_text = _norm(end)
    if empty_end_is_present and not end_text:
        end_text = "Present"
    _add_allowed(allowed, start_text)
    _add_allowed(allowed, end_text)
    if start_text and end_text:
        _add_allowed(allowed, f"{start_text} - {end_text}")
        _add_allowed(allowed, f"{format_date(start_text)} - {format_date(end_text)}")
    elif start_text:
        _add_allowed(allowed, f"{start_text} - {end_text}")
        formatted_end = format_date(end_text) if end_text else ""
        _add_allowed(allowed, f"{format_date(start_text)} - {formatted_end}".rstrip())


def _add_item_fields(allowed: set[str], item: dict[str, Any], *, kind: str) -> None:
    name = item.get("name") or ""
    position = item.get("position") or ""
    _add_allowed(allowed, name)
    _add_allowed(allowed, position)
    _add_allowed(allowed, item.get("location"))
    _add_allowed(allowed, item.get("summary"))
    _add_allowed(allowed, item.get("description"))
    _add_allowed(allowed, item.get("url"))
    for highlight in item.get("highlights") or []:
        _add_allowed(allowed, highlight)
    for keyword in item.get("keywords") or []:
        _add_allowed(allowed, keyword)
    if kind == "work" and position and name:
        _add_allowed(allowed, f"{position} at {name}")
    if kind == "project" and name:
        href = item.get("url") or ""
        _add_allowed(allowed, name)
        if href:
            _add_allowed(allowed, f"{name} ([Link]({href}))")
    _add_date_pair(
        allowed,
        item.get("startDate"),
        item.get("endDate"),
        empty_end_is_present=(kind == "work"),
    )


def _add_education_fields(allowed: set[str], item: dict[str, Any]) -> None:
    institution = item.get("institution") or ""
    area = item.get("area") or ""
    study_type = item.get("studyType") or ""
    score = item.get("score") or ""
    courses = [str(part) for part in item.get("courses") or []]
    _add_allowed(allowed, institution)
    _add_allowed(allowed, area)
    _add_allowed(allowed, study_type)
    _add_allowed(allowed, score)
    for course in courses:
        _add_allowed(allowed, course)
    for highlight in item.get("highlights") or []:
        _add_allowed(allowed, highlight)
    heading = ""
    if study_type:
        heading = study_type
        if area:
            heading += " in "
        heading += area
    else:
        heading = area
    if institution:
        heading = f"{heading} at {institution}" if heading else f"at {institution}"
    _add_allowed(allowed, heading)
    if study_type and area:
        _add_allowed(allowed, f"{study_type} in {area}")
    if institution:
        _add_allowed(allowed, f", {institution}")
        if score:
            _add_allowed(allowed, f", {institution} - GPA {score}")
    if score:
        _add_allowed(allowed, f"Score: {score}")
        _add_allowed(allowed, f"GPA {score}")
    if courses:
        _add_allowed(allowed, "Courses: " + ", ".join(courses))
    _add_date_pair(
        allowed,
        item.get("startDate"),
        item.get("endDate"),
        empty_end_is_present=False,
    )


def extract_public_md(text: str) -> ExtractedPublic:
    extracted = ExtractedPublic()
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            extracted.name = stripped[2:].strip()
            i += 1
            break
        if stripped.startswith("## "):
            break
        i += 1
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("## "):
            break
        if stripped.startswith("**") and stripped.endswith("**") and len(stripped) >= 4:
            extracted.label = stripped[2:-2]
            i += 1
            continue
        if "](" in stripped:
            for part in stripped.split(" | "):
                piece = part.strip().strip("|").strip()
                if piece:
                    extracted.contact.append(piece)
        i += 1

    sections = _md_sections(lines, i)
    if "Summary" in sections:
        extracted.summary = "\n".join(
            line.strip() for line in sections["Summary"] if line.strip()
        ).strip() or None
        extracted.headings.append("Summary")
    if "Experience" in sections:
        extracted.headings.append("Experience")
        extracted.work = _parse_md_entries(sections["Experience"])
    if "Projects" in sections:
        extracted.headings.append("Projects")
        extracted.projects = _parse_md_entries(sections["Projects"])
    if "Education" in sections:
        extracted.headings.append("Education")
        extracted.education = _parse_md_entries(sections["Education"], education=True)
    if "Skills" in sections:
        extracted.headings.append("Skills")
        extracted.skills = _md_dash_lines(sections["Skills"])
    if "Certificates" in sections:
        extracted.headings.append("Certificates")
        extracted.certificates = _md_dash_lines(sections["Certificates"])
    if "Publications" in sections:
        extracted.headings.append("Publications")
        extracted.publications = _md_dash_lines(sections["Publications"])
    for item in (*extracted.work, *extracted.projects, *extracted.education):
        if item.date:
            extracted.dates.append(item.date)
    return extracted


def _md_sections(lines: list[str], start: int) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("## "):
            current = stripped[3:].strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def _md_dash_lines(lines: list[str]) -> list[str]:
    values: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            values.append(stripped[2:].strip())
    return values


def _parse_md_entries(lines: list[str], *, education: bool = False) -> list[ExtractedItem]:
    items: list[ExtractedItem] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("### "):
            item = ExtractedItem(title=stripped[4:].strip())
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines):
                date_line = lines[i].strip()
                if date_line.startswith("_") and date_line.endswith("_") and len(date_line) >= 2:
                    item.date = date_line.strip("_").strip()
                    i += 1
            body: list[str] = []
            while i < len(lines):
                raw = lines[i]
                next_stripped = raw.strip()
                if next_stripped.startswith("### ") or next_stripped.startswith("## "):
                    break
                if _KEYWORDS_LINE.match(next_stripped):
                    i += 1
                    continue
                if next_stripped.startswith("- "):
                    item.bullets.append(next_stripped[2:].strip())
                elif education and next_stripped.startswith("Score:"):
                    item.extra.append(next_stripped)
                elif education and next_stripped.startswith("Courses:"):
                    item.extra.append(next_stripped)
                elif next_stripped:
                    body.append(next_stripped)
                i += 1
            item.summary = "\n".join(body).strip() or None
            items.append(item)
            continue
        i += 1
    return items


class _ClassParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, frozenset[str]]] = []
        self.buffers: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _VOID_TAGS:
            return
        classes = _class_set(attrs)
        self.stack.append((tag, classes))
        self.buffers.append([])
        self.on_start(tag, classes, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag in _VOID_TAGS or not self.stack:
            return
        text = ""
        classes: frozenset[str] = frozenset()
        actual = tag
        while self.stack:
            actual, classes = self.stack.pop()
            text = "".join(self.buffers.pop()) if self.buffers else ""
            self.on_end(actual, classes, text)
            if self.buffers:
                self.buffers[-1].append(text)
            if actual == tag:
                break

    def handle_data(self, data: str) -> None:
        if self.buffers:
            self.buffers[-1].append(data)

    def on_start(
        self, tag: str, classes: frozenset[str], attrs: list[tuple[str, str | None]]
    ) -> None:
        return None

    def on_end(self, tag: str, classes: frozenset[str], text: str) -> None:
        return None


def _class_set(attrs: list[tuple[str, str | None]]) -> frozenset[str]:
    for key, value in attrs:
        if key == "class" and value:
            return frozenset(value.split())
    return frozenset()


class _PublicHTMLParser(_ClassParser):
    def __init__(self) -> None:
        super().__init__()
        self.extracted = ExtractedPublic()
        self.current_entry: ExtractedItem | None = None

    def on_start(
        self, tag: str, classes: frozenset[str], attrs: list[tuple[str, str | None]]
    ) -> None:
        if "entry" in classes:
            self.current_entry = ExtractedItem()
            self.extracted.work.append(self.current_entry)

    def on_end(self, tag: str, classes: frozenset[str], text: str) -> None:
        value = text.strip()
        if tag == "h1":
            self.extracted.name = value or self.extracted.name
        elif tag == "h2":
            if value:
                self.extracted.headings.append(value)
        elif "headline" in classes:
            self.extracted.label = value
        elif "summary" in classes:
            self.extracted.summary = value or None
        elif "entry-title" in classes and self.current_entry is not None:
            self.current_entry.title = value
        elif "entry-subtitle" in classes and self.current_entry is not None:
            self.current_entry.name = value
        elif "entry-date" in classes:
            if value:
                self.extracted.dates.append(value)
                if self.current_entry is not None:
                    self.current_entry.date = value
        elif tag == "li" and self.current_entry is not None:
            if value:
                self.current_entry.bullets.append(value)
        elif "skill-name" in classes:
            if value:
                self.extracted.skill_names.append(value)
        elif "certificate-main" in classes:
            if value:
                self.extracted.cert_mains.append(value)
        elif "education-main" in classes:
            if value:
                self.extracted.edu_mains.append(value)
        elif "education-detail" in classes:
            if value:
                self.extracted.edu_details.append(value)
        if "entry" in classes:
            self.current_entry = None


def extract_public_html(text: str) -> ExtractedPublic:
    parser = _PublicHTMLParser()
    parser.feed(text)
    parser.close()
    return parser.extracted


class _BibleHTMLParser(_ClassParser):
    def __init__(self) -> None:
        super().__init__()
        self.extracted = ExtractedBible()
        self.current: BibleItem | None = None
        self.in_evidence = False
        self.pending_lis: list[str] = []

    def on_start(
        self, tag: str, classes: frozenset[str], attrs: list[tuple[str, str | None]]
    ) -> None:
        if "job-entry" in classes:
            self.current = BibleItem(kind="work")
            self.in_evidence = False
            self.pending_lis = []
        elif "project-entry" in classes:
            self.current = BibleItem(kind="project")
            self.in_evidence = False
            self.pending_lis = []
        elif tag == "ul":
            self.pending_lis = []

    def on_end(self, tag: str, classes: frozenset[str], text: str) -> None:
        value = text.strip()
        if self.current is None:
            return
        if tag == "h3":
            self.current.title = value
            if self.current.kind == "project" and not self.current.name:
                self.current.name = value
        elif tag == "span" and value.startswith("@ "):
            self.current.name = value[2:].strip()
        elif tag == "p" and "Evidence (not public)" in value:
            self.in_evidence = True
        elif tag == "li":
            if value:
                self.pending_lis.append(value)
        elif tag == "ul":
            if self.in_evidence:
                self.current.evidence = list(self.pending_lis)
            elif not self.current.highlights:
                self.current.highlights = list(self.pending_lis)
            self.pending_lis = []
        elif "job-entry" in classes:
            self.extracted.work.append(self.current)
            self.current = None
            self.in_evidence = False
        elif "project-entry" in classes:
            self.extracted.projects.append(self.current)
            self.current = None
            self.in_evidence = False


def extract_bible(text: str) -> ExtractedBible:
    parser = _BibleHTMLParser()
    parser.feed(text)
    parser.close()
    return parser.extracted


def _extracted_slots(extracted: ExtractedPublic) -> list[str]:
    values: list[str] = []
    for item in (
        extracted.name,
        extracted.label,
        extracted.summary,
        *extracted.headings,
        *extracted.contact,
        *extracted.dates,
        *extracted.skills,
        *extracted.certificates,
        *extracted.publications,
        *extracted.skill_names,
        *extracted.cert_mains,
        *extracted.edu_mains,
        *extracted.edu_details,
    ):
        if item:
            values.append(item)
    for group in (extracted.work, extracted.projects, extracted.education):
        for record in group:
            for item in (
                record.title,
                record.name,
                record.date,
                record.summary,
                *record.bullets,
                *record.extra,
            ):
                if item:
                    values.append(item)
    return values


def _fail(code: str, message: str, template: str | None = None) -> ScanFinding:
    return ScanFinding(severity="fail", code=code, message=message, template=template)


def _warn(code: str, message: str, template: str | None = None) -> ScanFinding:
    return ScanFinding(severity="warn", code=code, message=message, template=template)


def _source_evidence(source: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for section in ("work", "projects"):
        for item in source.get(section) or []:
            values.extend(item.get("evidence") or [])
    return values


def _highlight_universe_findings(
    source: dict[str, Any], tailored: dict[str, Any]
) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    for section in ("work", "projects"):
        source_by_name = {
            item.get("name"): item for item in source.get(section) or [] if item.get("name")
        }
        for item in tailored.get(section) or []:
            name = item.get("name")
            source_item = source_by_name.get(name)
            if source_item is None:
                continue
            allowed = list(source_item.get("highlights") or [])
            for highlight in item.get("highlights") or []:
                if highlight not in allowed:
                    findings.append(
                        _fail(
                            "allowed_highlight_universe",
                            f"{section} {name!r} highlight is not a source highlight of that item",
                        )
                    )
    return findings


def scan_rendered(
    source: dict[str, Any],
    tailored: dict[str, Any],
    rendered: dict[str, str],
) -> list[ScanFinding]:
    findings = _highlight_universe_findings(source, tailored)
    allowed = public_fields(source).allowed
    evidence = [token for token in _source_evidence(source) if token]
    for template in PUBLIC_SCAN_TEMPLATES:
        if template not in rendered:
            continue
        body = rendered[template]
        extracted = (
            extract_public_md(body) if template.endswith(".md.j2") else extract_public_html(body)
        )
        for value in _extracted_slots(extracted):
            if _norm(value) not in allowed:
                findings.append(
                    _fail(
                        "verbatim_highlight",
                        f"extracted text is not a source field or allowed composition: {value!r}",
                        template,
                    )
                )
        for token in evidence:
            if token in body:
                findings.append(
                    _fail(
                        "evidence_leak",
                        f"source evidence appears in public render: {token!r}",
                        template,
                    )
                )
    return findings


def scan_bible(source: dict[str, Any], tailored: dict[str, Any], html_text: str) -> list[ScanFinding]:
    del tailored
    findings: list[ScanFinding] = []
    extracted = extract_bible(html_text)
    work_by_name = {item.get("name"): item for item in source.get("work") or []}
    project_by_name = {item.get("name"): item for item in source.get("projects") or []}
    source_names = set(work_by_name) | set(project_by_name)
    for item in extracted.work + extracted.projects:
        if item.name and item.name not in source_names:
            findings.append(
                _fail(
                    "bible_unknown_identity",
                    f"bible identity {item.name!r} is not a source name",
                    BIBLE_SCAN_TEMPLATE,
                )
            )
        source_item = (
            work_by_name.get(item.name)
            if item.kind == "work"
            else project_by_name.get(item.name)
        )
        source_highlights = list((source_item or {}).get("highlights") or [])
        for highlight in item.highlights:
            if highlight not in source_highlights:
                findings.append(
                    _fail(
                        "bible_highlight_verbatim",
                        f"bible highlight is not a source highlight of {item.name!r}: {highlight!r}",
                        BIBLE_SCAN_TEMPLATE,
                    )
                )
        source_evidence = list((source_item or {}).get("evidence") or [])
        for evidence in item.evidence:
            if evidence not in source_evidence:
                findings.append(
                    _warn(
                        "bible_evidence_unknown",
                        f"bible evidence is not a source evidence string of {item.name!r}",
                        BIBLE_SCAN_TEMPLATE,
                    )
                )
    return findings


def quality_tokens(text: str) -> set[str]:
    return {
        tok
        for tok in re.findall(r"[a-z0-9]{4,}", text.lower())
        if tok not in QUALITY_STOPLIST
    }


def classify_jd(jd: str) -> str:
    text = jd.lower()
    if LEADERSHIP_JD.search(text):
        return "leadership"
    if IC_JD.search(text):
        return "ic"
    return "unspecified"


def role_match(source: dict[str, Any], tailored: dict[str, Any], jd: str) -> float:
    del source
    kind = classify_jd(jd)
    if kind == "unspecified":
        return 1.0
    pattern = LEADERSHIP_SRC if kind == "leadership" else IC_SRC
    selected = tailored.get("work") or []
    if not selected:
        return 0.0
    hits = 0
    for item in selected:
        blob = " ".join(
            [item.get("position") or "", item.get("summary") or ""]
            + list(item.get("highlights") or [])
        ).lower()
        if pattern.search(blob):
            hits += 1
    return hits / len(selected)


def _selected_text(tailored: dict[str, Any]) -> str:
    parts = [str((tailored.get("basics") or {}).get("summary") or "")]
    for section in ("work", "projects"):
        for item in tailored.get(section) or []:
            parts.append(item.get("name") or "")
            parts.append(item.get("position") or "")
            parts.append(item.get("summary") or "")
            parts.extend(item.get("highlights") or [])
    return " ".join(parts)


def _recency(source: dict[str, Any], tailored: dict[str, Any]) -> float:
    source_work = list(source.get("work") or [])
    n_work = len(source_work)
    if n_work <= 1:
        return 1.0
    source_names = [item.get("name") for item in source_work]
    ranks: list[int] = []
    for item in tailored.get("work") or []:
        name = item.get("name")
        if name in source_names:
            ranks.append(source_names.index(name))
    if not ranks:
        return 0.0
    mean_rank = sum(ranks) / len(ranks)
    return 1 - mean_rank / (n_work - 1)


def score_quality(source: dict[str, Any], tailored: dict[str, Any], jd: str) -> dict[str, float]:
    jd_tokens = quality_tokens(jd)
    selected_tokens = quality_tokens(_selected_text(tailored))
    if not jd_tokens:
        coverage = 1.0
    else:
        coverage = len(jd_tokens & selected_tokens) / len(jd_tokens)
    return {
        "keyword_coverage": coverage,
        "recency": _recency(source, tailored),
        "role_match": role_match(source, tailored, jd),
        "weight_keyword_coverage": 0.50,
        "weight_recency": 0.25,
        "weight_role_match": 0.25,
    }


def _prompt_version() -> str:
    schema = json.dumps(TailoringPlan.model_json_schema(), sort_keys=True, default=str)
    payload = f"{PROMPT_INSTRUCTIONS}\n{schema}\n{ASSEMBLER_VERSION}"
    return hashlib.sha256(payload.encode()).hexdigest()


def mean_pairwise_jaccard(sets: list[set[str]]) -> float | None:
    if len(sets) < 2:
        return None
    scores: list[float] = []
    for i, left in enumerate(sets):
        for right in sets[i + 1 :]:
            union = left | right
            scores.append(1.0 if not union else len(left & right) / len(union))
    return sum(scores) / len(scores)


def _classify_unexpected(exc: BaseException) -> str:
    status = getattr(exc, "status_code", None)
    if isinstance(status, int) and 400 <= status < 500 and status != 429:
        return "plan"
    return "transport"


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(override=False)


def _elapsed_from_provider(ai_provider: Any | None, started: float) -> float:
    if ai_provider is not None:
        elapsed = getattr(ai_provider, "last_elapsed_s", None)
        if elapsed is not None:
            return float(elapsed)
    return time.perf_counter() - started


def _usage_from_provider(ai_provider: Any | None) -> dict[str, int] | None:
    if ai_provider is None:
        return None
    usage = getattr(ai_provider, "last_usage", None)
    if not isinstance(usage, Mapping):
        return None
    result: dict[str, int] = {}
    for key, value in usage.items():
        if isinstance(value, int) and not isinstance(value, bool):
            result[str(key)] = value
    return result or None


def _section_indices(
    source_items: list[dict[str, Any]], selected_items: list[dict[str, Any]]
) -> list[int]:
    indices: list[int] = []
    for item in selected_items:
        name = item.get("name")
        matches = [i for i, src in enumerate(source_items) if src.get("name") == name]
        if len(matches) == 1:
            indices.append(matches[0])
    return indices


def _plan_from_tailored(
    source: dict[str, Any], tailored: dict[str, Any]
) -> dict[str, Any] | None:
    """Name-index reconstruction for the report; highlight selections are omitted."""

    payload = {
        "work": _section_indices(list(source.get("work") or []), list(tailored.get("work") or [])),
        "projects": _section_indices(
            list(source.get("projects") or []), list(tailored.get("projects") or [])
        ),
        "skills": _section_indices(
            list(source.get("skills") or []), list(tailored.get("skills") or [])
        ),
        "certificates": _section_indices(
            list(source.get("certificates") or []), list(tailored.get("certificates") or [])
        ),
        "publications": _section_indices(
            list(source.get("publications") or []), list(tailored.get("publications") or [])
        ),
    }
    try:
        return TailoringPlan.model_validate(payload).model_dump()
    except Exception:
        return payload if payload["work"] else None


def _render_public_and_bible(tailored: dict[str, Any]) -> dict[str, str]:
    gen = Jinja2Generator(str(_TEMPLATES_DIR))
    return {
        template: gen.render(tailored, template)
        for template in (*PUBLIC_SCAN_TEMPLATES, BIBLE_SCAN_TEMPLATE)
    }


def _score_artifacts(
    case: GoldenCase,
    source: dict[str, Any],
    tailored: dict[str, Any],
    rendered: dict[str, str] | None,
) -> tuple[list[ScanFinding], dict[str, float], list[str], list[str]]:
    selected_work = [item.get("name") or "" for item in tailored.get("work") or []]
    selected_projects = [item.get("name") or "" for item in tailored.get("projects") or []]
    findings = _identity_findings(case, tailored)
    quality = score_quality(source, tailored, case.jd)
    if (
        case.min_keyword_coverage is not None
        and quality["keyword_coverage"] < case.min_keyword_coverage
    ):
        findings.append(
            _warn("min_keyword_coverage", "keyword_coverage is below the recorded minimum")
        )
    if rendered:
        public_rendered = {key: rendered[key] for key in PUBLIC_SCAN_TEMPLATES if key in rendered}
        findings.extend(scan_rendered(source, tailored, public_rendered))
        if BIBLE_SCAN_TEMPLATE in rendered:
            findings.extend(scan_bible(source, tailored, rendered[BIBLE_SCAN_TEMPLATE]))
        findings.extend(_forbidden_findings(case, source, public_rendered))
    return findings, quality, selected_work, selected_projects


def _empty_record(
    case: GoldenCase,
    *,
    provider: str | None,
    model: str | None,
    elapsed_s: float | None,
    usage: dict[str, int] | None,
    error_class: str | None,
    plan: dict[str, Any] | None = None,
    selected_work: list[str] | None = None,
    selected_projects: list[str] | None = None,
    findings: list[ScanFinding] | None = None,
    quality: dict[str, float] | None = None,
) -> RunRecord:
    return RunRecord(
        case_id=case.id,
        provider=provider,
        model=model,
        plan=plan,
        selected_work=list(selected_work or []),
        selected_projects=list(selected_projects or []),
        findings=list(findings or []),
        quality=dict(quality or {}),
        elapsed_s=elapsed_s,
        usage=usage,
        error_class=error_class,
    )


def _live_repeat(
    case: GoldenCase,
    source: dict[str, Any],
    *,
    ai_provider: Any | None,
    provider: str | None,
    model: str | None,
) -> RunRecord:
    started = time.perf_counter()
    model_name = model or (getattr(ai_provider, "model_name", None) if ai_provider else None)
    try:
        if ai_provider is None:
            raise RuntimeError("live tailor eval requires a provider")
        tailored = ai_provider.tailor_profile(source, case.jd)
        elapsed = _elapsed_from_provider(ai_provider, started)
        usage = _usage_from_provider(ai_provider)
        rendered = _render_public_and_bible(tailored)
        findings, quality, selected_work, selected_projects = _score_artifacts(
            case, source, tailored, rendered
        )
        return _empty_record(
            case,
            provider=provider,
            model=model_name,
            elapsed_s=elapsed,
            usage=usage,
            error_class=None,
            plan=_plan_from_tailored(source, tailored),
            selected_work=selected_work,
            selected_projects=selected_projects,
            findings=findings,
            quality=quality,
        )
    except TailorTransportError:
        return _empty_record(
            case,
            provider=provider,
            model=model_name,
            elapsed_s=_elapsed_from_provider(ai_provider, started),
            usage=_usage_from_provider(ai_provider),
            error_class="transport",
        )
    except RuntimeError:
        return _empty_record(
            case,
            provider=provider,
            model=model_name,
            elapsed_s=_elapsed_from_provider(ai_provider, started),
            usage=_usage_from_provider(ai_provider),
            error_class="config",
        )
    except ValueError:
        return _empty_record(
            case,
            provider=provider,
            model=model_name,
            elapsed_s=_elapsed_from_provider(ai_provider, started),
            usage=_usage_from_provider(ai_provider),
            error_class="plan",
        )
    except Exception as exc:
        return _empty_record(
            case,
            provider=provider,
            model=model_name,
            elapsed_s=_elapsed_from_provider(ai_provider, started),
            usage=_usage_from_provider(ai_provider),
            error_class=_classify_unexpected(exc),
        )


def write_eval_report(report: EvalReport, path: Path | str) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")


def _report_path(output_dir: Path, case_id: str, provider: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return output_dir / f"{case_id}-{provider}-{stamp}.json"


def _plan_dict(plan: TailoringPlan | Mapping[str, Any] | None) -> dict[str, Any] | None:
    if plan is None:
        return None
    if isinstance(plan, TailoringPlan):
        return plan.model_dump()
    try:
        return TailoringPlan.model_validate(plan).model_dump()
    except Exception:
        return dict(plan)


def _identity_findings(case: GoldenCase, tailored: dict[str, Any]) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    selected_work = [item.get("name") for item in tailored.get("work") or []]
    selected_projects = [item.get("name") for item in tailored.get("projects") or []]
    for name in case.must_include_work:
        if name not in selected_work:
            findings.append(_fail("identity_gate", f"must_include_work missing {name!r}"))
    for name in case.must_exclude_work:
        if name in selected_work:
            findings.append(_fail("identity_gate", f"must_exclude_work present {name!r}"))
    for name in case.must_include_projects:
        if name not in selected_projects:
            findings.append(_fail("identity_gate", f"must_include_projects missing {name!r}"))
    for name in case.must_exclude_projects:
        if name in selected_projects:
            findings.append(_fail("identity_gate", f"must_exclude_projects present {name!r}"))
    assembled_highlights: list[str] = []
    for section in ("work", "projects"):
        for item in tailored.get(section) or []:
            assembled_highlights.extend(item.get("highlights") or [])
    for highlight in case.must_include_highlights:
        if highlight not in assembled_highlights:
            findings.append(
                _fail(
                    "must_include_highlights",
                    f"assembled profile missing highlight {highlight!r}",
                )
            )
    for name in case.preferred_work:
        if name not in selected_work:
            findings.append(_warn("preferred_work", f"preferred work {name!r} was not selected"))
    for name in case.preferred_projects:
        if name not in selected_projects:
            findings.append(
                _warn("preferred_projects", f"preferred project {name!r} was not selected")
            )
    return findings


def _forbidden_findings(
    case: GoldenCase, source: dict[str, Any], public_rendered: dict[str, str]
) -> list[ScanFinding]:
    haystack = "\n".join(public_rendered.values())
    tokens: list[str] = []
    tokens.extend(case.forbidden_tokens)
    tokens.extend(_source_evidence(source))
    if _uses_live_profile(case):
        tokens.extend(load_live_fragments())
    findings: list[ScanFinding] = []
    seen: set[str] = set()
    for token in tokens:
        if not token or token in seen:
            continue
        seen.add(token)
        if token in haystack:
            findings.append(
                _fail("forbidden_tokens", f"forbidden token present in public render: {token!r}")
            )
    return findings


def evaluate_case(
    case: GoldenCase,
    *,
    source: dict[str, Any],
    tailored: dict[str, Any] | None = None,
    plan: TailoringPlan | Mapping[str, Any] | None = None,
    rendered: dict[str, str] | None = None,
    live: bool = False,
    provider: str | None = None,
    repeats: int = 1,
    ai_provider: Any | None = None,
    model: str | None = None,
    report_path: Path | str | None = None,
) -> EvalReport:
    started = time.perf_counter()
    if live:
        records = [
            _live_repeat(
                case,
                source,
                ai_provider=ai_provider,
                provider=provider,
                model=model,
            )
            for _ in range(max(repeats, 0))
        ]
        successful = [rec for rec in records if rec.error_class is None]
        jaccard = mean_pairwise_jaccard(
            [set(rec.selected_work) | set(rec.selected_projects) for rec in successful]
        )
        all_valid = bool(records) and all(rec.error_class is None for rec in records)
        no_fails = all(
            not any(item.severity == "fail" for item in rec.findings) for rec in records
        )
        passed = (
            all_valid
            and no_fails
            and jaccard is not None
            and jaccard >= JACCARD_PASS
        )
        report = EvalReport(
            offline=False,
            repeats=repeats,
            prompt_version=_prompt_version(),
            jaccard=jaccard,
            passed=passed,
            elapsed_s=time.perf_counter() - started,
            records=records,
        )
        if report_path is not None:
            write_eval_report(report, report_path)
        return report

    if tailored is None and plan is not None:
        tailored = assemble_profile(source, plan)
    findings: list[ScanFinding] = []
    quality: dict[str, float] = {}
    selected_work: list[str] = []
    selected_projects: list[str] = []
    error_class = None
    if tailored is None:
        error_class = "config"
        findings.append(_fail("identity_gate", "evaluate_case requires tailored or plan"))
    else:
        findings, quality, selected_work, selected_projects = _score_artifacts(
            case, source, tailored, rendered
        )
    elapsed = time.perf_counter() - started
    record = RunRecord(
        case_id=case.id,
        provider=provider,
        model=model,
        plan=_plan_dict(plan),
        selected_work=selected_work,
        selected_projects=selected_projects,
        findings=findings,
        quality=quality,
        elapsed_s=elapsed,
        usage=None,
        error_class=error_class,
    )
    fails = [item for item in findings if item.severity == "fail"]
    report = EvalReport(
        offline=True,
        repeats=repeats,
        prompt_version=_prompt_version(),
        jaccard=None,
        passed=not fails and error_class is None,
        elapsed_s=elapsed,
        records=[record],
    )
    if report_path is not None:
        write_eval_report(report, report_path)
    return report


def _resolve_case_names(case: GoldenCase, source: dict[str, Any]) -> int:
    resolved = 0
    for field_name, section in _WORK_PROJECT_NAME_FIELDS:
        for name in getattr(case, field_name):
            index_by_name(list(source.get(section) or []), name)
            resolved += 1
    return resolved


def _resolve_provider_name(raw: str | None) -> str:
    return (raw or os.environ.get("TAILOR_PROVIDER") or DEFAULT_PROVIDER).strip().lower()


def _live_line(report: EvalReport, case_id: str, provider: str) -> str:
    coverages = [
        rec.quality["keyword_coverage"]
        for rec in report.records
        if "keyword_coverage" in rec.quality
    ]
    coverage = sum(coverages) / len(coverages) if coverages else None
    errors = [rec.error_class for rec in report.records if rec.error_class]
    jaccard = "-" if report.jaccard is None else f"{report.jaccard:.2f}"
    coverage_text = "-" if coverage is None else f"{coverage:.2f}"
    error = errors[0] if errors else "-"
    status = "PASS" if report.passed else "FAIL"
    return (
        f"{status} {case_id} {provider} n={report.repeats} "
        f"jaccard={jaccard} coverage={coverage_text} error={error}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate tailor-eval case YAML, or run opt-in live repeats."
    )
    parser.add_argument("--live", action="store_true", help="Call the selected provider N times.")
    parser.add_argument(
        "--provider",
        default=None,
        help="Tailoring provider for --live. Defaults to TAILOR_PROVIDER or openai.",
    )
    parser.add_argument("--model", default=None, help="Override the selected provider's model.")
    parser.add_argument(
        "--repeats",
        type=int,
        default=DEFAULT_LIVE_REPEATS,
        help=f"Live repeats (default {DEFAULT_LIVE_REPEATS}, min {MIN_LIVE_REPEATS}, max {MAX_LIVE_REPEATS}).",
    )
    parser.add_argument("--cases", default=DEFAULT_CASES_DIR)
    parser.add_argument(
        "--profile-dir",
        default=None,
        help="Override profile_dir on every loaded case.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for live JSON reports.",
    )
    args = parser.parse_args(argv)
    cases_dir = Path(args.cases)
    if not cases_dir.is_dir():
        print(f"missing --cases directory: {cases_dir}", file=sys.stderr)
        return 2

    ai_provider = None
    provider_name: str | None = None
    if args.live:
        if not MIN_LIVE_REPEATS <= args.repeats <= MAX_LIVE_REPEATS:
            print(
                f"--repeats must be between {MIN_LIVE_REPEATS} and {MAX_LIVE_REPEATS}",
                file=sys.stderr,
            )
            return 2
        _load_env()
        provider_name = _resolve_provider_name(args.provider)
        if provider_name not in _KNOWN_PROVIDERS:
            print(f"unknown --provider: {provider_name}", file=sys.stderr)
            return 2
        key_name = _PROVIDER_KEY[provider_name]
        if not os.environ.get(key_name, "").strip():
            print(
                f"{key_name} is required for --live with provider={provider_name}",
                file=sys.stderr,
            )
            return 2
        try:
            ai_provider = build_provider(provider_name, args.model)
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 2
        except RuntimeError as exc:
            print(exc, file=sys.stderr)
            return 2

    paths = sorted(cases_dir.glob("*.yaml"))
    live_failed = False
    for path in paths:
        try:
            case = load_case(path)
        except Exception as exc:
            print(f"{path}: invalid case YAML: {exc}", file=sys.stderr)
            return 1
        profile_dir = args.profile_dir or case.profile_dir
        try:
            source = YamlDataLoader(profile_dir).load()
        except Exception as exc:
            print(f"{case.id}: failed to load profile {profile_dir}: {exc}", file=sys.stderr)
            return 1
        try:
            resolved = _resolve_case_names(case, source)
        except ValueError as exc:
            print(f"{case.id}: {exc}", file=sys.stderr)
            return 1
        if not args.live:
            print(f"OK {case.id} ({resolved} names resolved)")
            continue
        assert provider_name is not None
        report_path = _report_path(Path(args.output), case.id, provider_name)
        report = evaluate_case(
            case,
            source=source,
            live=True,
            provider=provider_name,
            repeats=args.repeats,
            ai_provider=ai_provider,
            model=args.model,
            report_path=report_path,
        )
        print(_live_line(report, case.id, provider_name))
        if not report.passed:
            live_failed = True
    if args.live:
        return 1 if live_failed else 0
    return 0


__all__ = [
    "ASSEMBLER_VERSION",
    "BIBLE_SCAN_TEMPLATE",
    "DEFAULT_LIVE_REPEATS",
    "EvalReport",
    "ExtractedBible",
    "ExtractedPublic",
    "GoldenCase",
    "JACCARD_PASS",
    "PUBLIC_SCAN_TEMPLATES",
    "PublicFields",
    "QUALITY_STOPLIST",
    "RunRecord",
    "ScanFinding",
    "classify_jd",
    "evaluate_case",
    "extract_bible",
    "extract_public_html",
    "extract_public_md",
    "index_by_name",
    "load_case",
    "load_live_fragments",
    "main",
    "mean_pairwise_jaccard",
    "public_fields",
    "quality_tokens",
    "role_match",
    "scan_bible",
    "scan_rendered",
    "score_quality",
    "write_eval_report",
]


if __name__ == "__main__":
    sys.exit(main())
