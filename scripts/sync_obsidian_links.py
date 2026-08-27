"""Refresh Obsidian [[wikilinks]] from typed career graph edges."""

from __future__ import annotations

from pathlib import Path

from src.graph.loader import load_graph
from src.graph.obsidian import write_home, write_obsidian_links


def main() -> None:
    vault = Path("career")
    graph = load_graph(vault)
    changed = write_obsidian_links(graph)
    write_home(graph, vault)
    print(f"updated {len(changed)} notes + home.md")


if __name__ == "__main__":
    main()
