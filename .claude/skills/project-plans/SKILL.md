---
name: project-plans
description: Historical implementation plans for mkdocs-note releases (Notion sync, same-site link hover preview, path-encoding fixes). Use when changing those subsystems, investigating why an earlier design was chosen, or continuing work recorded in a plan.
---

# Historical implementation plans

Plans live in `.claude/plans/`, one file per release. Each starts with YAML
frontmatter containing `name`, `overview`, and `todos` (each with a `status`
such as `completed` or `cancelled`), followed by the problem statement, locked
decisions, and implementation notes.

Read only the plan that covers the current task. Do not load all of them.

| Plan | Release | Subsystem |
| --- | --- | --- |
| `notion_sync_adaptation_127cae36.plan.md` | pre-3.3.0 | Notion sync adaptation: `notion-sync` / `ns` CLI, shared meta/tree utilities, `convert` / `client` / `sync` layers |
| `notion_sync_3.3.0_878d053f.plan.md` | 3.3.0 | Notion sync: `local_images` `upload`/`site` modes, `--full` page-level resume checkpoints |
| `3.3.1_notion_section_fix_3cb93383.plan.md` | 3.3.1 | Fix the 404 when creating a nav section under the Notebook wiki root (issue #74) |
| `3.4.0_link_preview_3562be30.plan.md` | 3.4.0 | Same-site link hover preview: `preview` module, `previews.json`, fragment and rich excerpt modes (issue #82) |
| `3.4.1_preview_fixes_a349e839.plan.md` | 3.4.1 | Preview bugfixes: `linked_only` scope, CJK fragment keys, asset URL rewrite, section summaries (issue #84) |
| `3.4.2_path_encoding_2a4658d7.plan.md` | 3.4.2 | Preview failures under non-ASCII paths: decode keys at build time, encoded variants at runtime |

## Using a plan

1. Match the task to a row in the table.
2. Read that plan in full before inspecting or changing the subsystem.
3. Treat `todos` as a record of what shipped, not as current instructions.
   Verify the code as it exists now before assuming a plan is still accurate.
4. The plan may contain stale links or statuses; the code and the changelog are
   authoritative when they disagree.
5. When a new release produces a plan, add its file to `.claude/plans/` and a
   row to this table.
