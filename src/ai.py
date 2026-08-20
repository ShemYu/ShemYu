"""OpenAI Agents and xAI Chat Completions integration for profile tailoring."""

from __future__ import annotations

import copy
import json
import os
import time
from collections.abc import Mapping
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictInt, ValidationError, model_validator

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

try:  # Used by the xAI Chat Completions path; same optional extra as Agents.
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover - core-only installs.
    OpenAI = None  # type: ignore[assignment,misc]


DEFAULT_MODEL = "gpt-5.6-luna"
DEFAULT_PROVIDER = "openai"
DEFAULT_XAI_MODEL = "grok-4.6"
XAI_BASE_URL = "https://api.x.ai/v1"
XAI_TIMEOUT_S = 180.0
PROMPT_INSTRUCTIONS = (
    "Select relevant source profile entries for the supplied job description. "
    "Return only zero-based indices in TailoringPlan; never write, rewrite, "
    "summarize, or invent profile content. Basics and every education entry "
    "are always retained by the local assembler. Select at most four work "
    "entries, three projects, and three bullets per selected item. "
    "Prefer the most relevant, already-published highlights. "
    "Do not use or mention any field that is not present in the source JSON."
)
_INDEX_FIELDS = ("work", "projects", "skills", "certificates", "publications")


class HighlightSelection(BaseModel):
    """Select bullet indices for one source work or project item."""

    model_config = ConfigDict(extra="forbid")

    item_index: StrictInt
    highlight_indices: list[StrictInt] = Field(default_factory=list, max_length=3)

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
    """Selection-only output returned by the specialist agent.

    The model can select source entries and (optionally) their bullet
    indices.  It has no fields for basics, education, summaries, or prose;
    those values are copied locally from the validated source profile.
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


class TailorTransportError(RuntimeError):
    """Timeout, HTTP 429/5xx, or connection failure. Not a schema miss."""


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


def public_selectable_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Indexable source sections with internal evidence removed."""

    pub = {section: copy.deepcopy(profile[section]) for section in _INDEX_FIELDS}
    for section in ("work", "projects"):
        for item in pub[section]:
            item.pop("evidence", None)
    return pub


def _profile_for_prompt(profile: dict[str, Any]) -> str:
    """Serialize only the source sections the agent can select."""

    return json.dumps(
        public_selectable_profile(profile),
        ensure_ascii=False,
        default=str,
        sort_keys=True,
    )


def _tailor_user_prompt(source: dict[str, Any], job_description: str) -> str:
    return (
        "JOB DESCRIPTION\n---\n"
        f"{job_description.strip()}\n---\n"
        "SOURCE PROFILE (use indices only; do not reproduce or edit content)\n"
        f"{_profile_for_prompt(source)}\n---\n"
        "Return a TailoringPlan; the local assembler copies all non-selectable source "
        "fields unchanged."
    )


def _int_field(obj: Any, *names: str) -> int | None:
    if obj is None:
        return None
    for name in names:
        value = obj.get(name) if isinstance(obj, Mapping) else getattr(obj, name, None)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def _usage_dict(usage: Any) -> dict[str, int] | None:
    if usage is None:
        return None
    result: dict[str, int] = {}
    prompt = _int_field(usage, "prompt_tokens", "input_tokens")
    completion = _int_field(usage, "completion_tokens", "output_tokens")
    total = _int_field(usage, "total_tokens")
    reasoning = None
    for details_name in ("completion_tokens_details", "output_tokens_details"):
        details = (
            usage.get(details_name)
            if isinstance(usage, Mapping)
            else getattr(usage, details_name, None)
        )
        reasoning = _int_field(details, "reasoning_tokens")
        if reasoning is not None:
            break
    if reasoning is None:
        reasoning = _int_field(usage, "reasoning_tokens")
    if prompt is not None:
        result["prompt_tokens"] = prompt
    if completion is not None:
        result["completion_tokens"] = completion
    if total is not None:
        result["total_tokens"] = total
    if reasoning is not None:
        result["reasoning_tokens"] = reasoning
    return result or None


def _run_usage_dict(run_result: Any) -> dict[str, int] | None:
    usage = getattr(run_result, "usage", None)
    if usage is None:
        wrapper = getattr(run_result, "context_wrapper", None)
        usage = getattr(wrapper, "usage", None)
    return _usage_dict(usage)


def _status_code(exc: BaseException) -> int | None:
    value = getattr(exc, "status_code", None)
    return value if isinstance(value, int) else None


def _openai_error_types() -> tuple[type, type, type, type] | None:
    try:
        from openai import (
            APIConnectionError,
            APIStatusError,
            APITimeoutError,
            RateLimitError,
        )
    except ImportError:  # pragma: no cover - core-only installs.
        return None
    return APITimeoutError, APIConnectionError, RateLimitError, APIStatusError


def _is_transport_error(exc: BaseException) -> bool:
    types = _openai_error_types()
    if types is None:
        return False
    timeout_error, connection_error, rate_limit_error, status_error = types
    if isinstance(exc, (timeout_error, connection_error, rate_limit_error)):
        return True
    if isinstance(exc, status_error):
        status = _status_code(exc)
        return status is not None and (status == 429 or status >= 500)
    return False


def _is_schema_error(exc: BaseException) -> bool:
    types = _openai_error_types()
    if types is None:
        return False
    status_error = types[3]
    if not isinstance(exc, status_error):
        return False
    status = _status_code(exc)
    return status is not None and 400 <= status < 500 and status != 429


def _is_invalid_plan_error(exc: BaseException) -> bool:
    if _is_schema_error(exc) or isinstance(exc, ValidationError):
        return True
    try:
        from openai import ContentFilterFinishReasonError, LengthFinishReasonError
    except ImportError:  # pragma: no cover - core-only installs.
        return False
    return isinstance(exc, (LengthFinishReasonError, ContentFilterFinishReasonError))


def _plan_from_xai_message(message: Any) -> TailoringPlan:
    raw = getattr(message, "parsed", None)
    if raw is None and getattr(message, "content", None):
        try:
            raw = TailoringPlan.model_validate_json(message.content)
        except Exception as exc:
            raise ValueError("xAI returned an invalid TailoringPlan") from exc
    if raw is None:
        raise ValueError("xAI returned an invalid TailoringPlan")
    try:
        return raw if isinstance(raw, TailoringPlan) else TailoringPlan.model_validate(raw)
    except Exception as exc:
        raise ValueError("xAI returned an invalid TailoringPlan") from exc


def _source_summary(profile: dict[str, Any]) -> Optional[str]:
    basics = profile.get("basics", {}) if isinstance(profile, Mapping) else {}
    summary = basics.get("summary") if isinstance(basics, Mapping) else None
    return summary if isinstance(summary, str) else None


def build_provider(
    name: str | None = None,
    model_name: str | None = None,
) -> AIProvider:
    if load_dotenv is not None:
        load_dotenv(override=False)
    provider = (name or os.environ.get("TAILOR_PROVIDER") or DEFAULT_PROVIDER).strip().lower()
    if provider == "xai":
        return XAIChatProvider(model_name)
    if provider == "openai":
        return OpenAIAgentProvider(model_name)
    raise ValueError(f"Unknown tailoring provider: {provider}")


class OpenAIAgentProvider(AIProvider):
    """Single specialist Agent that selects source profile indices."""

    def __init__(self, model_name: Optional[str] = None):
        # Read local development configuration only when this opt-in provider
        # is instantiated.  Deterministic generation never imports this module.
        if load_dotenv is not None:
            load_dotenv(override=False)

        self.model_name = model_name or os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL
        if Agent is None or RunConfig is None or Runner is None:
            raise RuntimeError(
                "OpenAI tailoring is unavailable; install the 'tailoring' extra"
            )

        self.agent = Agent(
            name="Resume tailoring specialist",
            model=self.model_name,
            output_type=TailoringPlan,
            instructions=PROMPT_INSTRUCTIONS,
        )
        # Resume/JD contents are sensitive personal data. The model request is
        # required for tailoring, but duplicate storage in SDK traces is not.
        self.run_config = RunConfig(tracing_disabled=True)
        self.last_usage: dict[str, int] | None = None
        self.last_elapsed_s: float | None = None

    def generate_highlight(self, profile: dict[str, Any]) -> Optional[str]:
        """Return the validated source summary; never generate new facts."""

        return _source_summary(profile)

    def tailor_profile(
        self, profile: dict[str, Any], job_description: str
    ) -> dict[str, Any]:
        """Select and assemble source facts for ``job_description``."""

        if not isinstance(job_description, str) or not job_description.strip():
            raise ValueError("job_description must not be empty")
        if not os.environ.get("OPENAI_API_KEY", "").strip():
            raise RuntimeError("OPENAI_API_KEY is required to tailor a resume")

        source = _validated_profile(profile)
        if not source["work"]:
            raise ValueError("profile.work must contain at least one entry")

        self.last_usage = None
        started = time.perf_counter()
        try:
            run_result = Runner.run_sync(
                self.agent,
                _tailor_user_prompt(source, job_description),
                max_turns=1,
                run_config=self.run_config,
            )
            raw_plan = getattr(run_result, "final_output", run_result)
            try:
                plan = (
                    raw_plan
                    if isinstance(raw_plan, TailoringPlan)
                    else TailoringPlan.model_validate(raw_plan)
                )
            except Exception as exc:
                raise ValueError("Agent returned an invalid TailoringPlan") from exc
            tailored = assemble_profile(source, plan)
            self.last_usage = _run_usage_dict(run_result)
            return tailored
        finally:
            self.last_elapsed_s = time.perf_counter() - started


class XAIChatProvider(AIProvider):
    """OpenAI-compatible Chat Completions parse() against api.x.ai."""

    def __init__(self, model_name: Optional[str] = None):
        if load_dotenv is not None:
            load_dotenv(override=False)

        self.model_name = model_name or os.environ.get("XAI_MODEL") or DEFAULT_XAI_MODEL
        if OpenAI is None:
            raise RuntimeError(
                "xAI tailoring is unavailable; install the 'tailoring' extra"
            )
        key = os.environ.get("XAI_API_KEY", "").strip()
        if not key:
            raise RuntimeError(
                "XAI_API_KEY is required to tailor a resume with provider=xai"
            )
        self._client = OpenAI(
            api_key=key,
            base_url=XAI_BASE_URL,
            timeout=XAI_TIMEOUT_S,
        )
        self.last_usage: dict[str, int] | None = None
        self.last_elapsed_s: float | None = None

    def generate_highlight(self, profile: dict[str, Any]) -> Optional[str]:
        """Return the validated source summary; never generate new facts."""

        return _source_summary(profile)

    def tailor_profile(
        self, profile: dict[str, Any], job_description: str
    ) -> dict[str, Any]:
        """Select and assemble source facts for ``job_description``."""

        if not isinstance(job_description, str) or not job_description.strip():
            raise ValueError("job_description must not be empty")

        source = _validated_profile(profile)
        if not source["work"]:
            raise ValueError("profile.work must contain at least one entry")

        self.last_usage = None
        started = time.perf_counter()
        try:
            try:
                completion = self._client.beta.chat.completions.parse(
                    model=self.model_name,
                    temperature=0,
                    extra_body={"reasoning_effort": "low"},
                    messages=[
                        {"role": "system", "content": PROMPT_INSTRUCTIONS},
                        {
                            "role": "user",
                            "content": _tailor_user_prompt(source, job_description),
                        },
                    ],
                    response_format=TailoringPlan,
                )
            except Exception as exc:
                if _is_invalid_plan_error(exc):
                    raise ValueError("xAI returned an invalid TailoringPlan") from exc
                if _is_transport_error(exc):
                    raise TailorTransportError(f"xAI request failed: {exc}") from exc
                raise
            try:
                message = completion.choices[0].message
            except (AttributeError, IndexError, TypeError) as exc:
                raise ValueError("xAI returned an invalid TailoringPlan") from exc
            plan = _plan_from_xai_message(message)
            tailored = assemble_profile(source, plan)
            self.last_usage = _usage_dict(getattr(completion, "usage", None))
            return tailored
        finally:
            self.last_elapsed_s = time.perf_counter() - started


__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_PROVIDER",
    "DEFAULT_XAI_MODEL",
    "PROMPT_INSTRUCTIONS",
    "XAI_BASE_URL",
    "XAI_TIMEOUT_S",
    "HighlightSelection",
    "TailoringPlan",
    "TailorTransportError",
    "assemble_profile",
    "build_provider",
    "public_selectable_profile",
    "OpenAIAgentProvider",
    "XAIChatProvider",
]
