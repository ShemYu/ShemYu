"""Map existing YAML strings to another locale without inventing facts."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


PROSE_KEYS = frozenset(
    {
        "label",
        "summary",
        "position",
        "area",
        "studyType",
        "description",
    }
)
PROSE_LIST_KEYS = frozenset({"highlights"})
ALWAYS_MAP_KEYS = frozenset(
    {
        "name",
        "location",
        "city",
        "region",
        "institution",
    }
)

LOCALES_DIR = Path("locales")


def load_translations(locale: str, locales_dir: str | Path = LOCALES_DIR) -> dict[str, str]:
    path = Path(locales_dir) / f"{locale}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Locale file not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    strings = payload.get("strings", payload)
    if not isinstance(strings, Mapping):
        raise ValueError(f"{path}: expected a mapping of source strings")
    return {str(key): str(value) for key, value in strings.items()}


def _should_report(key: str, parent_skill_name: str | None) -> bool:
    if key in PROSE_KEYS or key in PROSE_LIST_KEYS:
        return True
    if key == "name" and parent_skill_name is None:
        # Company / project / skill-group names: report only if unmapped
        # skill-group names are useful; company names are optional.
        return True
    if key in {"city", "region"} or key == "location":
        return True
    if key == "keywords" and parent_skill_name == "Language":
        return True
    return False


def translate_value(
    value: Any,
    translations: Mapping[str, str],
    *,
    key: str = "",
    parent_skill_name: str | None = None,
    untranslated: list[str] | None = None,
) -> Any:
    """Translate a nested profile value. Unmapped prose is left in English."""

    missing = untranslated if untranslated is not None else []
    if isinstance(value, Mapping):
        skill_name = value.get("name") if "keywords" in value else parent_skill_name
        return {
            child_key: translate_value(
                child,
                translations,
                key=str(child_key),
                parent_skill_name=skill_name if isinstance(skill_name, str) else None,
                untranslated=missing,
            )
            for child_key, child in value.items()
        }
    if isinstance(value, list):
        return [
            translate_value(
                item,
                translations,
                key=key,
                parent_skill_name=parent_skill_name,
                untranslated=missing,
            )
            for item in value
        ]
    if not isinstance(value, str) or not value:
        return value
    if value in translations:
        return translations[value]
    stripped = value.strip()
    if stripped and stripped in translations:
        return translations[stripped]
    if _should_report(key, parent_skill_name):
        missing.append(stripped or value)
    return value


def translate_profile(
    profile: Mapping[str, Any],
    locale: str,
    *,
    locales_dir: str | Path = LOCALES_DIR,
) -> tuple[dict[str, Any], list[str]]:
    """Return (translated profile, untranslated prose strings)."""

    if locale == "en":
        return deepcopy(dict(profile)), []
    translations = load_translations(locale, locales_dir)
    missing: list[str] = []
    translated = translate_value(deepcopy(dict(profile)), translations, untranslated=missing)
    # Preserve insertion order while dropping duplicates.
    unique_missing = list(dict.fromkeys(missing))
    return translated, unique_missing


__all__ = ["load_translations", "translate_profile", "translate_value"]
