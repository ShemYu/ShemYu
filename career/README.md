# Career wiki + graph

This directory is the source of truth for Shem’s career. Each Markdown file is a **wiki page**. YAML frontmatter is the **graph node** (`id`, `type`, links). Resume files are not authored here; they are views under `../views/`.

| Folder | Node type |
|---|---|
| `people/` | person |
| `companies/` | employer / school org |
| `roles/` | employment |
| `foci/` | what was being worked on |
| `claims/` | locked facts |
| `metrics/` | metric contracts |
| `awards/` | awards tied to a role |
| `education/` | degrees |
| `certificates/` | certifications |
| `publications/` | writing |
| `skills/` | individual skills |
| `skill-groups/` | resume-facing skill lines (a view convenience backed by skill ids) |

Filename must equal `id`.

On a **claim** note: `id` / `focus` / `disclosure` are the query index; **`text.en` / `text.ja` are the locked full wording**. `title` may be a short stub (the migrator chopped at ~72 characters with `...`); that is not the fact. The note body repeats `text` so you can read it in Obsidian without opening YAML. A concise view may carry an editorial rewrite beside the primary claim id and cite related facts with `supporting_claims`. The rewrite cannot add a fact absent from those cited nodes, and every cited claim must belong to the same role or project.

Open **`career/` as the Obsidian vault** (not the repo root). Obsidian’s graph
view only follows `[[wikilinks]]` in note bodies. Each note has a generated
`## Graph` block (between `<!-- graph:start -->` and `<!-- graph:end -->`)
that is the same edges as frontmatter. Start from `home.md`.

Do **not** draw a second graph in Canvas, and do not add one-off links that
are not a career fact. To add a real relation, edit frontmatter (`role`,
`focus`, `claims`, `stack`, …) then run:

```bash
python scripts/sync_obsidian_links.py
```

`disclosure: public` may be selected by public views. `internal` stays in the graph and can appear on the Bible view as evidence. `secret` is never selected.

Private narrative that must not be committed goes in `private/` (gitignored), same schema.
