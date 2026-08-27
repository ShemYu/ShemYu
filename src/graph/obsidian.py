"""Write Obsidian ``[[wikilinks]]`` that match typed graph edges.

Frontmatter keeps machine slugs (YAML cannot store ``[[id]]`` unquoted
without becoming a nested list). Obsidian's graph view reads wikilinks
in the note body, so each page gets a generated ``## Graph`` block.
Do not maintain a second graph in Canvas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml

from src.graph.loader import CareerGraph, parse_markdown_page
from src.graph.schema import Claim

GRAPH_START = "<!-- graph:start -->"
GRAPH_END = "<!-- graph:end -->"
CLAIM_START = "<!-- claim-text:start -->"
CLAIM_END = "<!-- claim-text:end -->"


class _LiteralStr(str):
    """YAML block scalar so long claim text is not wrapped mid-sentence."""


def _represent_literal(dumper: yaml.Dumper, data: _LiteralStr) -> yaml.Node:
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style="|")


class _LiteralDumper(yaml.SafeDumper):
    pass


_LiteralDumper.add_representer(_LiteralStr, _represent_literal)


def wikilink(node_id: str, title: str = "") -> str:
    if title and title != node_id:
        return f"[[{node_id}|{title}]]"
    return f"[[{node_id}]]"


def _title(graph: CareerGraph, node_id: str) -> str:
    title = graph.get(node_id).title
    # Migrator truncated claim titles with "..."; those are not display names.
    if title.endswith("...") or len(title) > 80:
        return ""
    return title


def _line(label: str, ids: list[str], graph: CareerGraph) -> Optional[str]:
    ids = [item for item in ids if item]
    if not ids:
        return None
    links = ", ".join(wikilink(item, _title(graph, item)) for item in ids)
    return f"- {label}: {links}"


def graph_markdown(graph: CareerGraph, node_id: str) -> str:
    node = graph.get(node_id)
    data = node.model_dump()
    lines: list[str] = []

    for key, label in (
        ("person", "person"),
        ("company", "company"),
        ("role", "role"),
        ("focus", "focus"),
        ("metric", "metric"),
        ("institution_id", "institution"),
    ):
        line = _line(label, [data.get(key) or ""], graph)
        if line:
            lines.append(line)
    for key, label in (
        ("awards", "awards"),
        ("claims", "claims"),
        ("stack", "stack"),
        ("skills", "skills"),
    ):
        line = _line(label, list(data.get(key) or []), graph)
        if line:
            lines.append(line)

    if node.type == "person":
        roles = [item.id for item in graph.of_type("role") if item.person == node.id]
        lines.append(_line("roles", roles, graph) or "")
        lines.append(
            _line("education", [item.id for item in graph.of_type("education")], graph) or ""
        )
        lines.append(
            _line(
                "certificates",
                [item.id for item in graph.of_type("certificate")],
                graph,
            )
            or ""
        )
        lines.append(
            _line(
                "publications",
                [item.id for item in graph.of_type("publication")],
                graph,
            )
            or ""
        )
    elif node.type == "company":
        roles = [item.id for item in graph.of_type("role") if item.company == node.id]
        edu = [
            item.id
            for item in graph.of_type("education")
            if item.institution_id == node.id
        ]
        lines.append(_line("roles", roles, graph) or "")
        if edu:
            lines.append(_line("education", edu, graph) or "")
    elif node.type == "role":
        foci = [item.id for item in graph.of_type("focus") if item.role == node.id]
        lines.append(_line("foci", foci, graph) or "")
    elif node.type == "skill":
        used = [
            item.id
            for item in graph.of_type("focus")
            if node.id in (item.stack or [])
        ]
        groups = [
            item.id
            for item in graph.of_type("skill-group")
            if node.id in (item.skills or [])
        ]
        if used:
            lines.append(_line("used-by", used, graph) or "")
        if groups:
            lines.append(_line("groups", groups, graph) or "")
    elif node.type == "metric":
        used = [
            item.id
            for item in graph.of_type("claim")
            if item.metric == node.id
        ]
        if used:
            lines.append(_line("claims", used, graph) or "")

    compact = [line for line in lines if line]
    body = "\n".join(compact) if compact else "- (no typed links)"
    return f"{GRAPH_START}\n## Graph\n\n{body}\n{GRAPH_END}\n"


def upsert_block(body: str, start_mark: str, end_mark: str, section: str) -> str:
    if start_mark in body and end_mark in body:
        start = body.index(start_mark)
        end = body.index(end_mark) + len(end_mark)
        prefix = body[:start].rstrip()
        suffix = body[end:].lstrip("\n")
        pieces = [part for part in (prefix, section.rstrip(), suffix) if part]
        return "\n\n".join(pieces) + "\n"
    body = body.rstrip()
    if body:
        return body + "\n\n" + section
    return section


def upsert_graph_section(body: str, section: str) -> str:
    return upsert_block(body, GRAPH_START, GRAPH_END, section)


def claim_text_markdown(claim: Claim) -> str:
    lines = [CLAIM_START, claim.text.en]
    if claim.text.ja:
        lines.extend(["", claim.text.ja])
    lines.append(CLAIM_END)
    return "\n".join(lines) + "\n"


def _strip_block(body: str, start_mark: str, end_mark: str) -> str:
    if start_mark not in body or end_mark not in body:
        return body
    start = body.index(start_mark)
    end = body.index(end_mark) + len(end_mark)
    return (body[:start] + body[end:]).strip()


def rewrite_claim_frontmatter(path: Path, claim: Claim) -> tuple[str, str]:
    """Store full ``text`` as a block scalar; stop using truncated titles."""

    meta, body = parse_markdown_page(path)
    meta["title"] = _LiteralStr(claim.text.en)
    text: dict[str, Any] = dict(meta.get("text") or {})
    text["en"] = _LiteralStr(claim.text.en)
    if claim.text.ja:
        text["ja"] = _LiteralStr(claim.text.ja)
    else:
        text["ja"] = ""
    meta["text"] = text
    dumped = yaml.dump(
        meta,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        Dumper=_LiteralDumper,
    )
    return dumped, body


def write_obsidian_links(graph: CareerGraph) -> list[str]:
    """Rewrite generated body blocks. Returns changed paths."""

    changed: list[str] = []
    for page in graph.pages:
        path = Path(page.path)
        if isinstance(page.node, Claim):
            meta_text, body = rewrite_claim_frontmatter(path, page.node)
        else:
            meta_text, body = _raw_parts(path)
        human = _strip_block(body, GRAPH_START, GRAPH_END)
        human = _strip_block(human, CLAIM_START, CLAIM_END).strip()
        parts: list[str] = []
        if human:
            parts.append(human)
        if isinstance(page.node, Claim):
            parts.append(claim_text_markdown(page.node).rstrip())
        parts.append(graph_markdown(graph, page.node.id).rstrip())
        updated_body = "\n\n".join(parts) + "\n"
        rendered = f"---\n{meta_text.lstrip()}---\n\n{updated_body.lstrip()}"
        if rendered != path.read_text(encoding="utf-8"):
            path.write_text(rendered, encoding="utf-8")
            changed.append(str(path))
    return changed


def _raw_parts(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    rest = text[3:]
    end = rest.find("\n---")
    return rest[: end + 1], rest[end + 4 :]


def write_home(graph: CareerGraph, vault: Path) -> None:
    roles = sorted(graph.of_type("role"), key=lambda item: item.start, reverse=True)
    foci = sorted(graph.of_type("focus"), key=lambda item: item.start, reverse=True)
    lines = [
        "# Home",
        "",
        "Map of the career vault. Typed edges live in frontmatter; this page and each note's `## Graph` block are what Obsidian draws.",
        "",
        "## Roles",
        "",
    ]
    for role in roles:
        company = graph.get(role.company).title
        lines.append(f"- {wikilink(role.id, role.title)} @ {wikilink(role.company, company)}")
    lines.extend(["", "## Foci", ""])
    for focus in foci:
        lines.append(f"- {wikilink(focus.id, focus.title)} ← {wikilink(focus.role)}")
    lines.extend(["", f"Person: {wikilink('shem', graph.get('shem').title)}", ""])
    (vault / "home.md").write_text("\n".join(lines), encoding="utf-8")


__all__ = [
    "CLAIM_END",
    "CLAIM_START",
    "GRAPH_END",
    "GRAPH_START",
    "claim_text_markdown",
    "graph_markdown",
    "upsert_graph_section",
    "wikilink",
    "write_home",
    "write_obsidian_links",
]
