"""Load a Markdown wiki vault into an in-memory career graph."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import yaml
from pydantic import ValidationError

from src.graph.schema import Claim, Focus, GraphNode, ParsedPage, parse_node


def parse_markdown_page(path: Path) -> tuple[dict[str, Any], str]:
    """Split a page into YAML frontmatter and wiki body."""

    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path}: page must start with YAML frontmatter")
    rest = text[3:]
    end = rest.find("\n---")
    if end < 0:
        raise ValueError(f"{path}: unterminated YAML frontmatter")
    meta_text = rest[:end]
    body = rest[end + 4 :].lstrip("\n")
    try:
        meta = yaml.safe_load(meta_text) or {}
    except yaml.YAMLError as error:
        raise ValueError(f"{path}: invalid YAML frontmatter: {error}") from error
    if not isinstance(meta, dict):
        raise ValueError(f"{path}: frontmatter must be a mapping")
    return meta, body


def _iter_pages(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] == "private":
            continue
        if path.name.lower() in {"readme.md", "interview.md", "home.md"}:
            continue
        yield path


class CareerGraph:
    """Indexed career nodes. Views query this; they do not live here."""

    def __init__(self, pages: list[ParsedPage]):
        self.pages = pages
        self.by_id: dict[str, ParsedPage] = {}
        duplicates: list[str] = []
        for page in pages:
            node_id = page.node.id
            if node_id in self.by_id:
                duplicates.append(node_id)
            self.by_id[node_id] = page
        if duplicates:
            raise ValueError("duplicate node id: " + ", ".join(sorted(set(duplicates))))
        self._assert_filename_matches_id()
        self._assert_links_resolve()
        self._assert_claim_links_are_reciprocal()

    def _assert_filename_matches_id(self) -> None:
        mismatches = []
        for page in self.pages:
            stem = Path(page.path).stem
            if stem != page.node.id:
                mismatches.append(f"{page.path} (id {page.node.id})")
        if mismatches:
            raise ValueError("filename must match id: " + "; ".join(mismatches))

    def _assert_links_resolve(self) -> None:
        missing: list[str] = []
        for page in self.pages:
            node = page.node
            for target in _link_targets(node):
                if target not in self.by_id:
                    missing.append(f"{node.id} -> {target}")
        if missing:
            raise ValueError("dangling graph link: " + "; ".join(missing))

    def _assert_claim_links_are_reciprocal(self) -> None:
        """Keep Focus.claims and Claim.focus as one consistent graph edge."""

        mismatches: list[str] = []
        for page in self.pages:
            node = page.node
            if isinstance(node, Claim):
                focus = self.get(node.focus)
                if not isinstance(focus, Focus) or node.id not in focus.claims:
                    mismatches.append(
                        f"claim {node.id} points to {node.focus}, but the focus does not list it"
                    )
            elif isinstance(node, Focus):
                for claim_id in node.claims:
                    claim = self.get(claim_id)
                    if not isinstance(claim, Claim) or claim.focus != node.id:
                        mismatches.append(
                            f"focus {node.id} lists {claim_id}, but the claim points elsewhere"
                        )
        if mismatches:
            raise ValueError("non-reciprocal claim link: " + "; ".join(mismatches))

    def get(self, node_id: str) -> GraphNode:
        try:
            return self.by_id[node_id].node
        except KeyError as error:
            raise KeyError(f"unknown node id: {node_id}") from error

    def body(self, node_id: str) -> str:
        return self.by_id[node_id].body

    def of_type(self, node_type: str) -> list[GraphNode]:
        return [page.node for page in self.pages if page.node.type == node_type]


def _link_targets(node: GraphNode) -> list[str]:
    targets: list[str] = []
    data = node.model_dump()
    for key in ("person", "company", "role", "focus", "metric", "institution_id"):
        value = data.get(key) or ""
        if value:
            targets.append(value)
    for key in ("claims", "stack", "awards", "skills"):
        targets.extend(item for item in data.get(key) or [] if item)
    return targets


def load_graph(root: str | Path) -> CareerGraph:
    vault = Path(root)
    if not vault.is_dir():
        raise FileNotFoundError(f"{vault} is not a directory")
    pages: list[ParsedPage] = []
    for path in _iter_pages(vault):
        meta, body = parse_markdown_page(path)
        try:
            node = parse_node(meta)
        except (ValidationError, ValueError) as error:
            raise ValueError(f"{path}: {error}") from error
        pages.append(ParsedPage(path=str(path), node=node, body=body))
    return CareerGraph(pages)


__all__ = ["CareerGraph", "load_graph", "parse_markdown_page"]
