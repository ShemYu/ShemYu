"""Deterministic quality gates for authored resume bullets."""

from __future__ import annotations

import re
from collections.abc import Iterable


_METRIC_FIRST = re.compile(
    r"^(?:achieved|boosted|cut|decreased|grew|improved|increased|raised|reduced)\b",
    re.IGNORECASE,
)
_WEAK_OPENING = re.compile(
    r"^(?:helped with|responsible for|worked on)\b",
    re.IGNORECASE,
)
_TOOL_LED_ACTION = re.compile(
    r"^(?:architected|built|created|designed|developed|engineered|implemented)"
    r"(?:\s+and\s+(?:built|created|delivered|designed|developed|engineered|implemented))?"
    r"\s+(?:(?:a|an|the)\s+)?(.+)",
    re.IGNORECASE,
)


def validate_bullet(
    text: str,
    *,
    standard: str,
    locale: str,
    skill_titles: Iterable[str] = (),
) -> None:
    """Reject common project-log phrasing before a one-pager is rendered.

    The versioned v1 standard is deliberately narrow: exact golden tests own
    the approved prose, while this function prevents the two recurring failure
    modes that prompted the standard (a standalone metric and a tool-led task).
    """

    if standard == "none" or locale != "en":
        return
    if standard != "senior-impact-v1":
        raise ValueError(f"unknown editorial standard: {standard}")

    normalized = " ".join(text.split())
    if not normalized:
        raise ValueError("senior-impact-v1 requires non-empty bullet text")
    if len(normalized.split()) < 8:
        raise ValueError(
            "senior-impact-v1 requires enough context to describe the implementation"
        )
    if normalized[-1] not in ".!?":
        raise ValueError("senior-impact-v1 bullets must end with punctuation")
    if _METRIC_FIRST.match(normalized):
        raise ValueError(
            "senior-impact-v1 rejects metric-first bullets; lead with ownership or implementation"
        )
    if _WEAK_OPENING.match(normalized):
        raise ValueError(
            "senior-impact-v1 rejects weak task phrasing; state ownership and implementation"
        )

    action = _TOOL_LED_ACTION.match(normalized)
    if not action:
        return
    remainder = action.group(1)
    for title in sorted(set(skill_titles), key=len, reverse=True):
        if re.match(rf"{re.escape(title)}(?:\b|\s)", remainder, re.IGNORECASE):
            raise ValueError(
                "senior-impact-v1 rejects tool-first bullets; describe the system or workflow first"
            )


__all__ = ["validate_bullet"]
