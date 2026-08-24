"""Deterministic, source-index selection of profile facts for a target role."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


SELECTIONS_DIR = Path("locales") / "selections"


def load_selection(name: str, selections_dir: str | Path = SELECTIONS_DIR) -> dict[str, Any]:
    path = Path(selections_dir) / f"{name}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Selection preset not found: {path}")
    spec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(spec, Mapping):
        raise ValueError(f"{path}: selection file must be a mapping")
    return dict(spec)


def _item_by_name(items: list[dict[str, Any]], name: str, section: str) -> dict[str, Any]:
    for item in items:
        if item.get("name") == name:
            return item
    available = ", ".join(item.get("name", "") for item in items)
    raise KeyError(f"{section} item {name!r} not found. Available: {available}")


def _select_highlights(item: dict[str, Any], indices: list[int] | None) -> dict[str, Any]:
    selected = deepcopy(item)
    if indices is None:
        return selected
    highlights = list(item.get("highlights") or [])
    picked = []
    for index in indices:
        if index < 0 or index >= len(highlights):
            raise IndexError(
                f"{item.get('name')}: highlight index {index} is out of range "
                f"(0..{len(highlights) - 1})"
            )
        picked.append(highlights[index])
    selected["highlights"] = picked
    return selected


def apply_selection(
    profile: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> dict[str, Any]:
    """Copy selected facts from a validated profile. Does not rewrite prose."""

    result = deepcopy(dict(profile))
    work_spec = spec.get("work")
    if work_spec:
        selected_work = []
        for entry in work_spec:
            source = _item_by_name(list(profile.get("work") or []), entry["name"], "work")
            selected_work.append(_select_highlights(source, entry.get("highlight_indices")))
        result["work"] = selected_work

    skill_names = spec.get("skills")
    if skill_names:
        selected_skills = []
        for name in skill_names:
            selected_skills.append(
                deepcopy(_item_by_name(list(profile.get("skills") or []), name, "skills"))
            )
        result["skills"] = selected_skills

    education_spec = spec.get("education", "all")
    if education_spec != "all":
        selected_education = []
        for name in education_spec:
            selected_education.append(
                deepcopy(_item_by_name(list(profile.get("education") or []), name, "education"))
            )
        result["education"] = selected_education

    excludes = tuple(spec.get("certificates_exclude_substrings") or ())
    if excludes:
        result["certificates"] = [
            deepcopy(item)
            for item in result.get("certificates") or []
            if not any(fragment in item.get("name", "") for fragment in excludes)
        ]

    if not spec.get("include_publications", True):
        result["publications"] = []
    if not spec.get("include_projects", True):
        result["projects"] = []

    limit = spec.get("skill_keyword_limit")
    if isinstance(limit, int) and limit >= 0:
        trimmed = []
        for skill in result.get("skills") or []:
            skill = deepcopy(skill)
            if skill.get("name") != "Language":
                skill["keywords"] = list(skill.get("keywords") or [])[:limit]
            trimmed.append(skill)
        result["skills"] = trimmed

    result["selection_meta"] = dict(spec.get("meta") or {})
    return result


__all__ = ["apply_selection", "load_selection"]
