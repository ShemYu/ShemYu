from __future__ import annotations

import glob
from datetime import date, datetime
from pathlib import Path
from typing import Any, Type

import yaml
from pydantic import BaseModel, ValidationError

from src.interfaces import DataLoader
from src.project import project_profile
from src.schema import (
    Basics,
    Certificate,
    Education,
    Profile,
    Project,
    Publication,
    Skill,
    Work,
)


SECTION_MODELS: dict[str, Type[BaseModel]] = {
    "work": Work,
    "education": Education,
    "certificates": Certificate,
    "publications": Publication,
    "skills": Skill,
    "projects": Project,
}


def _normalize_yaml_values(value: Any) -> Any:
    """Normalize YAML-native date values throughout a loaded document."""

    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _normalize_yaml_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_yaml_values(item) for item in value]
    return value


def _validation_error_with_source(error: ValidationError, source: Path) -> ValidationError:
    """Prefix Pydantic locations with the YAML source file path."""

    line_errors = []
    for detail in error.errors():
        detail = dict(detail)
        detail["loc"] = (str(source), *detail["loc"])
        line_errors.append(detail)
    return ValidationError.from_exception_data("Profile validation failed", line_errors)


class YamlDataLoader(DataLoader):
    """Load, validate, normalize, and sort profile data from YAML files."""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    @staticmethod
    def _read_yaml(path: Path) -> Any:
        try:
            with path.open("r", encoding="utf-8") as file:
                value = yaml.safe_load(file)
        except yaml.YAMLError as error:
            raise ValueError(f"{path}: invalid YAML: {error}") from error

        value = _normalize_yaml_values(value)
        if value is not None and not isinstance(value, dict):
            raise ValueError(f"{path}: top-level YAML value must be a mapping")
        return value

    def load(self) -> dict[str, Any]:
        data_root = Path(self.data_dir)

        basics_path = data_root / "basics.yaml"
        # Validating an empty mapping gives a useful source/field error for a
        # missing or empty required basics file instead of returning a partial
        # profile that fails later in a template.
        basics_value = self._read_yaml(basics_path) if basics_path.exists() else {}
        try:
            basics = Basics.model_validate(basics_value or {})
        except ValidationError as error:
            source = basics_path if basics_path.exists() else basics_path
            raise _validation_error_with_source(error, source) from error

        profile: dict[str, Any] = {
            "basics": basics.model_dump(mode="python"),
        }

        for section, model_type in SECTION_MODELS.items():
            entries: list[dict[str, Any]] = []
            section_dir = data_root / section
            if section_dir.exists():
                for file_name in sorted(glob.glob(str(section_dir / "*.yaml"))):
                    path = Path(file_name)
                    value = self._read_yaml(path)
                    try:
                        model = model_type.model_validate(value)
                    except ValidationError as error:
                        raise _validation_error_with_source(error, path) from error
                    entries.append(model.model_dump(mode="python"))
            profile[section] = entries

        # Sorting is performed on normalized strings, so quoted and unquoted
        # YAML dates have identical ordering semantics.
        for section in ("work", "education", "projects"):
            profile[section].sort(key=lambda item: item.get("startDate", ""), reverse=True)

        try:
            validated = Profile.model_validate(profile)
        except ValidationError as error:
            # Individual section validation above normally catches these.  The
            # final validation protects callers if the assembled profile is
            # changed in the future and still returns a precise field path.
            raise _validation_error_with_source(error, data_root) from error

        # ``mode="json"`` ensures dates and any future JSON-compatible scalar
        # types are safe to pass to Jinja. The projector then fills derived
        # highlights / projects from foci without re-entering Work validation
        # (which forbids mixed authored foci + highlights).
        return project_profile(validated.model_dump(mode="json"))
