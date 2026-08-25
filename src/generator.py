from __future__ import annotations

import os
import shutil
import stat
import tempfile
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pydantic import BaseModel

from src.i18n import HIGHLIGHT_CAPS, as_of_label, format_date as format_date_localized
from src.i18n import normalize_language, ui_labels
from src.interfaces import ContentGenerator
from src.schema import validate_url

import copy

PUBLIC_RESUME_TEMPLATES = frozenset(
    {
        "resume.html.j2",
        "resume.md.j2",
        "readme.md.j2",
    }
)


def for_public_resume(profile: Mapping[str, Any] | BaseModel) -> dict[str, Any]:
    """Return a profile copy with internal evidence stripped.

    ``highlights`` are the public layer. ``evidence`` stays in YAML / the
    bible template and must not reach one-page outbound resumes.
    """

    if isinstance(profile, BaseModel):
        data = profile.model_dump(mode="json")
    else:
        data = copy.deepcopy(dict(profile))
    for section in ("work", "projects"):
        items = []
        for item in data.get(section) or []:
            item = dict(item)
            item.pop("evidence", None)
            items.append(item)
        data[section] = items
    return data

def format_date(value: Any) -> str:
    """Format resume dates consistently while preserving unknown values."""
    if value is None or value == "":
        return ""

    text = str(value)
    if text.lower() == "present":
        return "Present"

    for date_format in ("%Y-%m-%d", "%Y-%m"):
        try:
            return datetime.strptime(text, date_format).strftime("%b %Y")
        except ValueError:
            pass

    return text


def _autoescape_template(template_name: str | None) -> bool:
    """Enable escaping only for the HTML Jinja templates."""

    return bool(template_name and template_name.endswith(".html.j2"))


def _validate_context_urls(value: Any, path: tuple[str, ...] = ()) -> None:
    """Reject unsafe URL values even when a caller bypasses the YAML loader."""

    if isinstance(value, BaseModel):
        _validate_context_urls(value.model_dump(mode="json"), path)
    elif isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text in {"url", "image"}:
                try:
                    validate_url(child)
                except ValueError as error:
                    location = ".".join((*path, key_text))
                    raise ValueError(f"Unsafe URL at {location}: {error}") from error
            _validate_context_urls(child, (*path, key_text))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _validate_context_urls(child, (*path, str(index)))


class Jinja2Generator(ContentGenerator):
    """Render Jinja templates with strict variables and atomic file writes."""

    def __init__(self, template_dir: str, language: str = "en"):
        self.language = normalize_language(language)
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            undefined=StrictUndefined,
            autoescape=_autoescape_template,
        )
        self.env.filters["format_date"] = self._format_date

    def _format_date(self, value: Any) -> str:
        return format_date_localized(value, self.language)

    def _render_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        """Copy the profile and add language-only keys used by templates."""

        payload = dict(context)
        payload["language"] = self.language
        payload["ui"] = ui_labels(self.language)
        payload["as_of"] = as_of_label(self.language)
        payload["highlight_caps"] = list(HIGHLIGHT_CAPS[self.language])
        payload["education_limit"] = 2 if self.language == "ja" else 1
        return payload

    @staticmethod
    def _normalize_outputs(
        outputs: Mapping[str, str] | Sequence[tuple[str, str]],
    ) -> list[tuple[str, str]]:
        """Normalize supported batch output forms to template/path pairs.

        The public form is a sequence of ``(template_name, output_path)``
        tuples.  A mapping with template names as keys is accepted as a small
        convenience; mappings in the reverse direction are also recognized
        when their values end in ``.j2``.
        """

        if isinstance(outputs, Mapping):
            pairs: list[tuple[str, str]] = []
            for first, second in outputs.items():
                first_text, second_text = os.fspath(first), os.fspath(second)
                if second_text.endswith(".j2") and not first_text.endswith(".j2"):
                    pairs.append((second_text, first_text))
                else:
                    pairs.append((first_text, second_text))
            return pairs

        pairs = []
        for pair in outputs:
            if len(pair) != 2:
                raise ValueError("Each batch output must be (template_name, output_path)")
            template_name, output_path = pair
            pairs.append((os.fspath(template_name), os.fspath(output_path)))
        return pairs

    def render(self, context: Mapping[str, Any] | BaseModel, template_name: str) -> str:
        """Render one template without touching the filesystem."""

        if isinstance(context, BaseModel):
            context = context.model_dump(mode="json")
        if not isinstance(context, Mapping):
            raise TypeError("template context must be a mapping or Pydantic model")
        _validate_context_urls(context)
        if template_name in PUBLIC_RESUME_TEMPLATES:
            context = for_public_resume(context)
        template = self.env.get_template(template_name)
        output = template.render(**self._render_context(context))
        # Match the historical single-file API's whitespace normalization.
        return "\n".join(line.rstrip() for line in output.splitlines())

    def render_batch(
        self,
        context: Mapping[str, Any] | BaseModel,
        outputs: Mapping[str, str] | Sequence[tuple[str, str]],
    ) -> dict[str, str]:
        """Render every requested template in memory before any file write."""

        rendered: dict[str, str] = {}
        seen_paths: set[str] = set()
        for template_name, output_path in self._normalize_outputs(outputs):
            destination = os.fspath(output_path)
            absolute_destination = os.path.abspath(destination)
            if absolute_destination in seen_paths:
                raise ValueError(f"Duplicate batch output path: {destination}")
            seen_paths.add(absolute_destination)
            rendered[destination] = self.render(context, template_name)
        return rendered

    @staticmethod
    def _temporary_file(directory: str, prefix: str) -> str:
        descriptor, path = tempfile.mkstemp(prefix=prefix, dir=directory)
        os.close(descriptor)
        return path

    def _atomic_commit(self, rendered: Mapping[str, str]) -> None:
        """Commit staged output files, restoring old outputs on failure."""

        staged: list[dict[str, Any]] = []
        committed: list[dict[str, Any]] = []
        try:
            # Stage every output beside its destination.  At this point no
            # destination has been changed, so a render or write failure is
            # inherently all-or-nothing.
            for output_path, content in rendered.items():
                destination = os.path.abspath(os.fspath(output_path))
                directory = os.path.dirname(destination) or os.curdir
                os.makedirs(directory, exist_ok=True)
                temporary = self._temporary_file(directory, f".{os.path.basename(destination)}.")
                try:
                    with open(temporary, "w", encoding="utf-8", newline="") as file:
                        file.write(content)
                        file.flush()
                        os.fsync(file.fileno())
                    if os.path.exists(destination):
                        mode = stat.S_IMODE(os.stat(destination).st_mode)
                        os.chmod(temporary, mode)
                    else:
                        os.chmod(temporary, 0o644)
                except Exception:
                    try:
                        os.unlink(temporary)
                    except OSError:
                        pass
                    raise

                backup = None
                existed = os.path.exists(destination)
                if existed:
                    backup = self._temporary_file(directory, f".{os.path.basename(destination)}.bak.")
                    try:
                        shutil.copy2(destination, backup)
                    except Exception:
                        try:
                            os.unlink(backup)
                        except OSError:
                            pass
                        try:
                            os.unlink(temporary)
                        except OSError:
                            pass
                        raise
                staged.append(
                    {
                        "destination": destination,
                        "temporary": temporary,
                        "backup": backup,
                        "existed": existed,
                    }
                )

            for item in staged:
                os.replace(item["temporary"], item["destination"])
                item["temporary"] = None
                committed.append(item)
        except Exception:
            # Roll back in reverse order.  A failed os.replace may leave the
            # source temp in place; cleanup below handles both states.
            for item in reversed(committed):
                try:
                    if item["existed"] and item["backup"]:
                        os.replace(item["backup"], item["destination"])
                        item["backup"] = None
                    elif not item["existed"]:
                        os.unlink(item["destination"])
                except OSError:
                    # Rollback is best effort; retain the original commit
                    # exception and clean up any files that remain possible.
                    pass
            raise
        finally:
            for item in staged:
                for key in ("temporary", "backup"):
                    path = item.get(key)
                    if path:
                        try:
                            os.unlink(path)
                        except OSError:
                            pass

    def generate_batch(
        self,
        context: Mapping[str, Any] | BaseModel,
        outputs: Mapping[str, str] | Sequence[tuple[str, str]],
    ) -> None:
        """Render and atomically commit a group of template outputs."""

        rendered = self.render_batch(context, outputs)
        self._atomic_commit(rendered)
        for output_path in rendered:
            print(f"Successfully generated {output_path}")

    def generate(
        self,
        context: Mapping[str, Any] | BaseModel,
        template_name: str,
        output_path: str,
    ) -> None:
        """Backward-compatible single-template generation API."""

        self.generate_batch(context, [(template_name, output_path)])


__all__ = ["Jinja2Generator", "PUBLIC_RESUME_TEMPLATES", "for_public_resume", "format_date"]
