"""Derive the print-shaped resume view from Role → Focus → Claim.

YAML that still authors ``highlights`` / ``evidence`` is left unchanged.
YAML that authors ``foci`` gets template lists filled here so existing
Jinja templates keep clipping ``work[].highlights``.
"""

from __future__ import annotations

import copy
from typing import Any, Iterable, Mapping, Optional

PROJECT_FOCUS_KINDS = frozenset({"product", "platform"})
PUBLIC_LAYER = "public"
ARCHIVE_LAYERS = frozenset({"bible", "archive"})


def _sorted_foci(foci: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (dict(focus) for focus in foci),
        key=lambda focus: (int(focus.get("public_rank") or 0), str(focus.get("id") or "")),
    )


def _sorted_claims(
    focus: Mapping[str, Any], layers: Iterable[str]
) -> list[dict[str, Any]]:
    allowed = set(layers)
    claims = [
        dict(claim)
        for claim in focus.get("claims") or []
        if claim.get("layer") in allowed
    ]
    return sorted(
        claims,
        key=lambda claim: (int(claim.get("rank") or 0), str(claim.get("id") or "")),
    )


def _project_role(role: Mapping[str, Any]) -> dict[str, Any]:
    projected = dict(role)
    foci = list(role.get("foci") or [])
    if not foci:
        return projected

    highlights: list[str] = []
    evidence: list[str] = []
    for focus in _sorted_foci(foci):
        highlights.extend(
            claim["text"]
            for claim in _sorted_claims(focus, (PUBLIC_LAYER,))
            if claim.get("resume", True)
        )
        evidence.extend(
            claim["text"] for claim in _sorted_claims(focus, ARCHIVE_LAYERS)
        )
    for award in role.get("awards") or []:
        name = award.get("name")
        if name:
            highlights.append(name)
    projected["highlights"] = highlights
    projected["evidence"] = evidence
    return projected


def _project_from_focus(focus: Mapping[str, Any]) -> Optional[dict]:
    if focus.get("kind") not in PROJECT_FOCUS_KINDS:
        return None
    public = _sorted_claims(focus, (PUBLIC_LAYER,))
    if not public:
        return None
    return {
        "name": focus.get("name") or "",
        "description": focus.get("problem") or "",
        "url": "",
        "startDate": focus.get("startDate") or "",
        "endDate": focus.get("endDate") or "",
        "keywords": list(focus.get("stack") or []),
        "highlights": [claim["text"] for claim in public],
        "evidence": [claim["text"] for claim in _sorted_claims(focus, ARCHIVE_LAYERS)],
    }


def project_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Fill derived ``highlights``, ``evidence``, and ``projects`` lists."""

    data = copy.deepcopy(dict(profile))
    roles = [_project_role(role) for role in data.get("work") or []]
    data["work"] = roles

    derived_projects: list[dict[str, Any]] = []
    for role in roles:
        for focus in _sorted_foci(role.get("foci") or []):
            project = _project_from_focus(focus)
            if project is not None:
                derived_projects.append(project)

    if derived_projects:
        derived_names = {item["name"] for item in derived_projects}
        leftover = [
            dict(item)
            for item in data.get("projects") or []
            if item.get("name") not in derived_names
        ]
        merged = leftover + derived_projects
        merged.sort(key=lambda item: item.get("startDate") or "", reverse=True)
        data["projects"] = merged

    return data


__all__ = ["PROJECT_FOCUS_KINDS", "project_profile"]
