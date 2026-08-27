"""OpenAI Agents SDK integration for deterministic profile tailoring."""

from __future__ import annotations

import copy
import os
from collections.abc import Mapping
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from src.compose import (
    GroundedTailoringPlan,
    RoleBullets,
    assemble_composed_profile,
    composer_instructions,
    composer_prompt,
)
from src.interfaces import AIProvider
from src.schema import profile_dict

try:  # The SDK is an optional dependency used only by the tailoring command.
    from agents import Agent, RunConfig, Runner
except ModuleNotFoundError:  # pragma: no cover - core-only installs.
    Agent = None  # type: ignore[assignment,misc]
    RunConfig = None  # type: ignore[assignment,misc]
    Runner = None  # type: ignore[assignment,misc]

try:  # Keep importing this module harmless when the optional extra is absent.
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - core-only installs.
    load_dotenv = None  # type: ignore[assignment]


DEFAULT_MODEL = "gpt-5.6-luna"
_INDEX_FIELDS = ("work", "projects", "skills", "certificates", "publications")


class HighlightSelection(BaseModel):
    """Select bullet indices for one source work or project item."""

    model_config = ConfigDict(extra="forbid")

    item_index: StrictInt
    highlight_indices: list[StrictInt] = Field(default_factory=list, max_length=4)

    @model_validator(mode="after")
    def validate_indices(self) -> "HighlightSelection":
        if self.item_index < 0:
            raise ValueError("item_index must be non-negative")
        if any(index < 0 for index in self.highlight_indices):
            raise ValueError("highlight_indices must be non-negative")
        if len(self.highlight_indices) != len(set(self.highlight_indices)):
            raise ValueError("highlight_indices contains duplicate indices")
        return self


class TailoringPlan(BaseModel):
    """Selection-only plan used by pick-eval and ``assemble_profile``.

    The live tailor path emits ``GroundedTailoringPlan`` (indices plus
    composed bullets). This model remains so role-selection tests can still
    assemble a profile by copying source highlight indices.
    """

    model_config = ConfigDict(extra="forbid")

    # Required and bounded so a valid model response cannot produce an empty
    # or unreasonably long work history in a one-page resume.
    work: list[StrictInt] = Field(min_length=1, max_length=4)
    projects: list[StrictInt] = Field(default_factory=list, max_length=3)
    work_highlights: list[HighlightSelection] = Field(default_factory=list, max_length=4)
    project_highlights: list[HighlightSelection] = Field(default_factory=list, max_length=3)
    skills: list[StrictInt] = Field(default_factory=list)
    certificates: list[StrictInt] = Field(default_factory=list)
    publications: list[StrictInt] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_duplicate_indices(self) -> "TailoringPlan":
        for field_name in _INDEX_FIELDS:
            values = getattr(self, field_name)
            if any(index < 0 for index in values):
                raise ValueError(f"{field_name} must contain non-negative indices")
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} contains duplicate indices")

        for field_name in ("work_highlights", "project_highlights"):
            selections = getattr(self, field_name)
            item_indices = [selection.item_index for selection in selections]
            if len(item_indices) != len(set(item_indices)):
                raise ValueError(f"{field_name} contains duplicate item indices")
        return self


def _validated_profile(profile: Any) -> dict[str, Any]:
    """Validate a dict/Profile with the shared YAML/render profile contract."""

    # profile_dict accepts both the concrete Profile model and a mapping.
    return profile_dict(profile)


def _select_items(
    source: dict[str, Any], section: str, indices: list[int]
) -> list[dict[str, Any]]:
    items = source.get(section, [])
    for index in indices:
        if index < 0 or index >= len(items):
            raise ValueError(
                f"{section} index {index} is out of range (size={len(items)})"
            )
    return [copy.deepcopy(items[index]) for index in indices]


def _apply_highlight_selection(
    selected: list[dict[str, Any]],
    source_items: list[Mapping[str, Any]],
    selected_indices: list[int],
    selections: list[HighlightSelection],
    section: str,
) -> None:
    """Apply explicit bullet selections or retain at most three bullets."""

    selected_positions = {
        source_index: position
        for position, source_index in enumerate(selected_indices)
    }
    explicit = {selection.item_index: selection for selection in selections}
    for source_index, selection in explicit.items():
        if source_index < 0 or source_index >= len(source_items):
            raise ValueError(
                f"{section} highlight selection references out-of-range item {source_index}"
            )
        if source_index not in selected_positions:
            raise ValueError(
                f"{section} highlight selection references unselected item {source_index}"
            )

        highlights = source_items[source_index].get("highlights", [])
        if highlights is None:
            highlights = []
        if not isinstance(highlights, list):
            raise ValueError(f"profile.{section}[{source_index}].highlights must be a list")
        for highlight_index in selection.highlight_indices:
            if highlight_index >= len(highlights):
                raise ValueError(
                    f"{section}[{source_index}] highlight index {highlight_index} "
                    f"is out of range (size={len(highlights)})"
                )
        selected[selected_positions[source_index]]["highlights"] = [
            copy.deepcopy(highlights[index]) for index in selection.highlight_indices
        ]

    # Keep a compact deterministic prefix when the model leaves a selected
    # item's bullets unspecified.
    for source_index, position in selected_positions.items():
        if source_index in explicit:
            continue
        highlights = source_items[source_index].get("highlights", [])
        if highlights is None:
            highlights = []
        if not isinstance(highlights, list):
            raise ValueError(f"profile.{section}[{source_index}].highlights must be a list")
        selected[position]["highlights"] = copy.deepcopy(highlights[:3])


def assemble_profile(
    profile: Any, plan: TailoringPlan | Mapping[str, Any]
) -> dict[str, Any]:
    """Build a tailored profile from source facts and a validated plan."""

    source = _validated_profile(profile)
    if not isinstance(plan, TailoringPlan):
        plan = TailoringPlan.model_validate(plan)

    result = copy.deepcopy(source)
    for section in _INDEX_FIELDS:
        result[section] = _select_items(source, section, list(getattr(plan, section)))

    _apply_highlight_selection(
        result["work"],
        source["work"],
        list(plan.work),
        list(plan.work_highlights),
        "work",
    )
    _apply_highlight_selection(
        result["projects"],
        source["projects"],
        list(plan.projects),
        list(plan.project_highlights),
        "projects",
    )
    # Education and basics intentionally remain complete source copies.
    result["education"] = copy.deepcopy(source["education"])

    # Validate the assembled result with the same model used by YamlDataLoader
    # and return its JSON-compatible representation to templates.
    return _validated_profile(result)


class OpenAIAgentProvider(AIProvider):
    """Specialist Agent that selects entries and composes grounded bullets."""

    def __init__(self, model_name: Optional[str] = None, language: str = "en"):
        # Read local development configuration only when this opt-in provider
        # is instantiated.  Deterministic generation never imports this module.
        if load_dotenv is not None:
            load_dotenv(override=False)

        from src.i18n import normalize_language

        self.language = normalize_language(language)
        self.model_name = model_name or os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL
        if Agent is None or RunConfig is None or Runner is None:
            raise RuntimeError(
                "OpenAI tailoring is unavailable; install the 'tailoring' extra"
            )

        self.agent = Agent(
            name="Resume compose specialist",
            model=self.model_name,
            output_type=GroundedTailoringPlan,
            instructions=composer_instructions(self.language),
        )
        # Resume/JD contents are sensitive personal data. The model request is
        # required for tailoring, but duplicate storage in SDK traces is not.
        self.run_config = RunConfig(tracing_disabled=True)

    def generate_highlight(self, profile: dict[str, Any]) -> Optional[str]:
        """Return the validated source summary; never generate new facts."""

        basics = profile.get("basics", {}) if isinstance(profile, Mapping) else {}
        summary = basics.get("summary") if isinstance(basics, Mapping) else None
        return summary if isinstance(summary, str) else None

    def tailor_profile(
        self, profile: dict[str, Any], job_description: str
    ) -> dict[str, Any]:
        """Select roles and compose grounded bullets for ``job_description``."""

        if not isinstance(job_description, str) or not job_description.strip():
            raise ValueError("job_description must not be empty")
        if not os.environ.get("OPENAI_API_KEY", "").strip():
            raise RuntimeError("OPENAI_API_KEY is required to tailor a resume")

        source = _validated_profile(profile)
        if not source["work"]:
            raise ValueError("profile.work must contain at least one entry")

        run_result = Runner.run_sync(
            self.agent,
            composer_prompt(source, job_description),
            max_turns=1,
            run_config=self.run_config,
        )
        raw_plan = getattr(run_result, "final_output", run_result)
        try:
            plan = (
                raw_plan
                if isinstance(raw_plan, GroundedTailoringPlan)
                else GroundedTailoringPlan.model_validate(raw_plan)
            )
        except Exception as exc:
            raise ValueError("Agent returned an invalid GroundedTailoringPlan") from exc
        return assemble_composed_profile(source, plan)


__all__ = [
    "DEFAULT_MODEL",
    "GroundedTailoringPlan",
    "HighlightSelection",
    "RoleBullets",
    "TailoringPlan",
    "assemble_composed_profile",
    "assemble_profile",
    "OpenAIAgentProvider",
]
