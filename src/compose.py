"""Grounded composition of resume bullets from selected role facts.

Role / project / skill / cert / publication *selection* stays index-based.
For each selected work or project item, the model emits at most three
sentences. The local assembler writes those sentences into ``highlights``
and the grounding checker hard-fails invented numbers, names, and causality.

The no-JD canonical path does not use this module; templates clip the locked
public highlights.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from src.grounding import assert_grounded, is_constraint_evidence
from src.schema import profile_dict


STANDARD_PATH = Path(__file__).resolve().parent.parent / "RESUME_STANDARD.md"
_INDEX_FIELDS = ("work", "projects", "skills", "certificates", "publications")


class RoleBullets(BaseModel):
    """Composed bullets for one selected work or project item."""

    model_config = ConfigDict(extra="forbid")

    item_index: StrictInt
    bullets: list[str] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validate_bullets(self) -> "RoleBullets":
        if self.item_index < 0:
            raise ValueError("item_index must be non-negative")
        cleaned = [bullet.strip() for bullet in self.bullets]
        if any(not bullet for bullet in cleaned):
            raise ValueError("composed bullets must be non-empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("composed bullets contains duplicates")
        self.bullets = cleaned
        return self


class GroundedTailoringPlan(BaseModel):
    """Index selection plus composed bullets for selected roles."""

    model_config = ConfigDict(extra="forbid")

    work: list[StrictInt] = Field(min_length=1, max_length=4)
    projects: list[StrictInt] = Field(default_factory=list, max_length=3)
    skills: list[StrictInt] = Field(default_factory=list)
    certificates: list[StrictInt] = Field(default_factory=list)
    publications: list[StrictInt] = Field(default_factory=list)
    work_bullets: list[RoleBullets] = Field(default_factory=list, max_length=4)
    project_bullets: list[RoleBullets] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def validate_selection_and_coverage(self) -> "GroundedTailoringPlan":
        for field_name in _INDEX_FIELDS:
            values = getattr(self, field_name)
            if any(index < 0 for index in values):
                raise ValueError(f"{field_name} must contain non-negative indices")
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} contains duplicate indices")

        for field_name, selected in (
            ("work_bullets", self.work),
            ("project_bullets", self.projects),
        ):
            items = getattr(self, field_name)
            covered = [item.item_index for item in items]
            if len(covered) != len(set(covered)):
                raise ValueError(f"{field_name} contains duplicate item indices")
            if set(covered) != set(selected):
                raise ValueError(
                    f"{field_name} must cover each selected index exactly once"
                )
        return self


def load_resume_standard(path: Path | None = None) -> str:
    standard_path = path or STANDARD_PATH
    text = standard_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Resume standard is empty: {standard_path}")
    return text


def facts_for_role(item: Mapping[str, Any]) -> dict[str, Any]:
    """Facts the composer may read for one role.

    Locked public highlights remain a source. Constraint evidence is returned
    separately so the model can see what not to write without treating those
    lines as publishable inventory.
    """

    evidence = [str(line) for line in item.get("evidence") or [] if line]
    return {
        "name": item.get("name"),
        "position": item.get("position"),
        "summary": item.get("summary"),
        "description": item.get("description"),
        "location": item.get("location"),
        "highlights": list(item.get("highlights") or []),
        "evidence_publishable": [
            line for line in evidence if not is_constraint_evidence(line)
        ],
        "evidence_constraints": [line for line in evidence if is_constraint_evidence(line)],
    }


def _select_items(source: dict[str, Any], section: str, indices: list[int]) -> list[dict[str, Any]]:
    items = source.get(section, [])
    for index in indices:
        if index < 0 or index >= len(items):
            raise ValueError(f"{section} index {index} is out of range (size={len(items)})")
    return [copy.deepcopy(items[index]) for index in indices]


def _apply_role_bullets(
    selected: list[dict[str, Any]],
    selected_indices: list[int],
    compositions: list[RoleBullets],
    section: str,
) -> None:
    position_by_source = {
        source_index: position for position, source_index in enumerate(selected_indices)
    }
    for composition in compositions:
        if composition.item_index not in position_by_source:
            raise ValueError(
                f"{section} composition references unselected item {composition.item_index}"
            )
        selected[position_by_source[composition.item_index]]["highlights"] = list(
            composition.bullets
        )


def assemble_composed_profile(
    profile: Any,
    plan: GroundedTailoringPlan | Mapping[str, Any],
    *,
    ground: bool = True,
) -> dict[str, Any]:
    """Select source entries by index and write composed bullets into highlights.

    Live tailor runs keep ``ground=True`` (hard fail). Offline eval can set
    ``ground=False`` and collect ``check_profile`` findings instead.
    """

    source = profile_dict(profile)
    if not isinstance(plan, GroundedTailoringPlan):
        plan = GroundedTailoringPlan.model_validate(plan)

    result = copy.deepcopy(source)
    for section in _INDEX_FIELDS:
        result[section] = _select_items(source, section, list(getattr(plan, section)))
    result["education"] = copy.deepcopy(source["education"])

    _apply_role_bullets(result["work"], list(plan.work), list(plan.work_bullets), "work")
    _apply_role_bullets(
        result["projects"], list(plan.projects), list(plan.project_bullets), "projects"
    )
    if ground:
        assert_grounded(source, result)
    return profile_dict(result)


def composer_instructions(language: str = "en") -> str:
    """System instructions for the grounded compose agent."""

    from src.i18n import normalize_language

    language = normalize_language(language)
    standard = load_resume_standard()
    if language == "ja":
        language_rule = (
            "Write each composed bullet in Japanese. Keep source numbers and "
            "Latin product names unchanged (50%, 95%, 53/56, 0.67, 0.89, "
            "Databricks, Google ADK). Do not write 40%→95% as the Cookpad "
            "public sentence. Do not add 日本語 Fluent, N1, ビジネス日本語, or LiteLLM. "
            "Prefer the three newest roles. Drop awards, MVP titles, redundant "
            "cost bullets, generic deploy bullets, and documentation-only "
            "bullets unless the job description clearly needs them."
        )
    else:
        language_rule = (
            "Write each composed bullet in English. Select at most four work "
            "entries and three projects."
        )

    return (
        "You tailor a one-page resume. Select source entries by zero-based "
        "index. For every selected work and project item, compose at most "
        "three resume-standard sentences from that item's facts. Do not "
        "return highlight indices. Do not invent, strengthen, or estimate "
        "facts. Basics and every education entry are retained locally.\n\n"
        f"{language_rule}\n\n"
        "RESUME STANDARD\n"
        "---\n"
        f"{standard}\n"
        "---\n"
        "Use locked public highlights plus publishable evidence as the fact "
        "inventory. Treat evidence_constraints as a ban list, not as bullets "
        "to publish. work_bullets / project_bullets must cover each selected "
        "index exactly once."
    )


def composer_prompt(profile: Mapping[str, Any], job_description: str) -> str:
    """User prompt: JD plus selectable sections with layered role facts."""

    import json

    source = profile_dict(profile)
    payload = {
        "work": [facts_for_role(item) for item in source.get("work") or []],
        "projects": [facts_for_role(item) for item in source.get("projects") or []],
        "skills": copy.deepcopy(source.get("skills") or []),
        "certificates": copy.deepcopy(source.get("certificates") or []),
        "publications": copy.deepcopy(source.get("publications") or []),
    }
    return (
        "JOB DESCRIPTION\n---\n"
        f"{job_description.strip()}\n---\n"
        "SOURCE PROFILE (select by index; compose bullets only from each "
        "role's facts)\n"
        f"{json.dumps(payload, ensure_ascii=False, default=str)}\n---\n"
        "Return a GroundedTailoringPlan."
    )


__all__ = [
    "STANDARD_PATH",
    "GroundedTailoringPlan",
    "RoleBullets",
    "assemble_composed_profile",
    "composer_instructions",
    "composer_prompt",
    "facts_for_role",
    "load_resume_standard",
]
