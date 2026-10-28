---
name: write-product-spec
description: Write a PRODUCT.md spec for a significant feature, focused on detailed behavior and validation. Use when the user asks for a product spec, desired behavior doc, or PRD, wants to define feature behavior before implementation, or when the feature is substantial or behaviorally ambiguous enough that a written spec would improve implementation or review.
---

# write-product-spec

Write a `PRODUCT.md` spec for a significant feature.

## Overview

The product spec should make the desired behavior unambiguous enough that an agent can implement it correctly and avoid regressions. Describe the feature purely from the user's perspective — what the user sees, does, and experiences, and the invariants that must hold for them. Do not include implementation details (internal types, state layout, module boundaries, data flow, algorithms).

"User" is not limited to a human using an application. It means whoever consumes the surface being designed:

- For UI / UX features: the human using the application.
- For a data model: the code that reads and writes that model.
- For an API, protocol, or library: the callers of that API — other services, client code, plugins, or agents.
- For a CLI tool or developer-facing surface: the developer invoking it.

The spec should describe behavior from that consumer's perspective: the shape of the surface, the operations they can perform, what they see back, invariants they can rely on, and edge cases they must handle — without prescribing how the surface is implemented underneath.

Implementation details, validation, and test planning live in a companion `TECH.md`, produced by the `write-tech-spec` skill. Writing the product spec is usually the first step of a two-step process: once `PRODUCT.md` is agreed on, invoke `write-tech-spec` to produce `TECH.md` for the same feature (or let the user know that's the expected next step). The product spec should be written so the tech spec can be written directly from it.

## Project conventions and destination

Read project instructions and relevant existing specs first. Follow the project's document locations, templates, metadata, vocabulary, and authority rules. `PRODUCT.md` and `TECH.md` describe document roles; use established filenames when the project has them. Link existing decisions rather than creating duplicate policy or status owners.

When no convention exists, use `specs/<id>/PRODUCT.md`, where `<id>` is an existing issue id or a short kebab-case feature name. Keep companion specs together. Infer a suitable feature name from the request; ask only if the choice matters.

Read [work-record ownership](../../reference/work-records.md) before planning adopted work or making a handoff. Spec writing is tentative unless adopted; it does not automatically publish issues or authorize implementation, prototypes, commits, promotion, or live operations. Preserve authorization already given in the session.

## Before writing

Gather only the context you need: directory id (Linear ticket, GitHub issue, or feature name), feature summary, target users, key behaviors, edge cases, and how the feature will be validated. Investigate repository facts yourself. Ask one question at a time for consequential missing intent, wait for the answer, and adapt. Mark unresolved behavior explicitly rather than inventing requirements.

### Figma mocks

If the feature has any UI or interaction design, ask the user whether a Figma mock exists before drafting the Behavior section, and include the link in the spec when one is provided. A mock is often the most reliable source of truth for visual states, spacing, and edge-case layouts — not asking can cause the Behavior section to guess at intent the designer already settled.

- If the user provides a link, include it under a short `## Figma` section (or inline near the top of Behavior) as `Figma: <link>`.
- If the user confirms no mock exists, note `Figma: none provided` so the absence is explicit rather than ambiguous.
- If the feature is purely backend (data model, API, CLI with no visual surface), skip the question and omit the section.

Do not silently drop design context; an explicit "none" is preferable to no mention at all on features where design would normally be expected.

## Structure

Required sections:

1. **Summary** — Briefly describe the feature and desired outcome, with enough context to understand why it matters.
2. **Behavior** — A complete English description of how the feature works, written as numbered, testable invariants. See "The Behavior section" below. Keep framing focused so it explains the behavior without duplicating it.

Optional sections — include only when they add signal beyond the core. Omit the heading entirely if empty; do not write "None" as a placeholder.

- **Problem** — Include only when the motivation isn't obvious from Summary.
- **Goals / Non-goals** — Include when scope is ambiguous or has been contested.
- **Figma** — Include with a link when one exists, or an explicit `Figma: none provided` note when design matters but no mock exists. Omit entirely for non-visual features. See "Figma mocks" above.
- **Open questions** — Prefer inline `**Open question:** …` next to the relevant behavior. Include a dedicated section only if there are multiple unresolved questions worth collecting.

Do not include Validation, Success criteria, or Testing sections. Validation and test planning live in the companion `TECH.md` (produced by `write-tech-spec`). Write Behavior as numbered invariants that are testable on their own — the tech spec can reference them directly.

## The Behavior section

Behavior is the spec. Everything else is framing.

The goal of Behavior is a complete English description of how the feature works, detailed enough that a tech spec can be written directly from it without the author having to guess or re-derive product intent. If a reader finishes Behavior with questions about what the feature does in some situation, the section is not done.

Describe, at minimum:

- Default behavior and the happy-path user flow.
- Every user-visible state and the transitions between them.
- All inputs the user can provide and how the feature responds.
- Empty states, error states, loading / pending states, and cancellation.
- Edge cases a reasonable implementer would not think to ask about — permission denied, offline, timeouts, races between state changes, multiple concurrent instances, stale or missing data, focus loss mid-interaction, interactions with adjacent features.
- Keyboard, accessibility, and focus expectations where relevant.
- Invariants that must hold at all times and behaviors that must not regress.

## Detail and readability

Trivial fixes or narrow UI tweaks do not need a spec. For features that do, use enough detail to explain all required behavior and edge cases, even when this makes the spec longer. Group related invariants by flow or state when that helps the reader follow them. Introduce necessary terms and explain the context behind consequential behavior; completeness requires readable explanations as well as coverage. Follow the shared working agreements' quiet review before saving.

If you find yourself writing the same idea in Summary, Problem, Goals, and Behavior, collapse the framing — not the Behavior content.

## Writing guidance

- Prefer concrete, observable behavior over aspirational wording.
- Write Behavior as numbered, testable invariants in clear sentences. Add context where needed to make each rule understandable.
- Capture invariants that must not regress and edge cases that are easy to miss.
- Avoid implementation details unless unavoidable for the UX.
- Each section should earn its place — if a section would repeat another or contain only boilerplate, omit it.

## Keep the spec current

Approved specs may ship in the same PR as the implementation. As implementation evolves, update `PRODUCT.md` in the same PR when user-facing behavior or UX details change. The checked-in spec should describe the feature that actually ships.

Use existing project decision records first. Where no convention exists, the implementer may optionally keep a `DECISIONS.md` file summarizing concrete decisions made during design and implementation. Offer it when it would help future agents; otherwise skip it.

## Related skills

[write-tech-spec](../write-tech-spec/SKILL.md) translates agreed behavior into technical design and verification.

## Example Behavior section

A sample Behavior section for a hypothetical feature: rendering GitHub-flavored Markdown tables in the Warp block list. It demonstrates the expected shape — numbered, testable, user-perspective invariants that enumerate defaults, edge cases, malformed input, streaming, selection/copy, search, sharing, theming, and cross-surface consistency, with one inline open question.

````markdown
## Behavior

1. When a terminal output block contains a GitHub-flavored Markdown table (a header row, a separator row of one or more `---` segments, and one or more body rows, all delimited by `|`), that table renders as a visually formatted table in the block — not as raw pipe-delimited text.

2. The table renders with:
   - A visually distinct header row.
   - Aligned columns based on the separator row: `|:---|` left-align, `|:---:|` center, `|---:|` right-align. `|---|` with no colons falls back to the default alignment (left for text, right for numeric-looking values).
   - Visible row separators (or equivalent spacing) consistent with the active theme.

3. Inline markdown inside a cell renders inline: bold, italic, inline code, strikethrough, and links all render the same way they do in the surrounding block output. Line breaks inside a cell (`<br>` or escaped `\n`) render as in-cell line breaks.

4. Column widths are chosen to fit the table's natural content when it fits inside the block. If a single cell's content is very long, that cell wraps its text within its column rather than forcing the column to an unreasonable width.
   - **Open question:** when a wrapped cell would produce an unreasonably tall row, do we clip with an "expand" affordance, or let the row grow unbounded?

5. Horizontal scrolling: when the table's total width exceeds the block width — many columns, or wide columns that can't reasonably be narrowed — the table becomes horizontally scrollable within the block. Scrolling horizontally reveals off-screen columns without clipping or truncating them. Vertical scrolling of the block continues to work independently of table scroll.

6. When the block is resized (terminal resize, pane split, sidebar open/close), the table reflows to the new width without losing row or column order.

7. Empty cells render as visibly empty (same row height as surrounding cells, no placeholder text). A row with all empty cells still renders as a row.

8. A table with only a header and separator (zero body rows) renders as a header-only table, not as raw text.

9. A single-column table renders as a single-column table (not collapsed to a bullet list or similar).

10. Malformed tables fall back gracefully:
    - Missing separator row → rendered as preformatted text, not as a table.
    - Ragged rows (some rows have fewer or more cells than the header) → missing cells render empty; extra cells are shown, with the header row extended visually if possible. The block should never silently drop data.
    - Unclosed table (last row truncated mid-stream) → rendered as a partial table; see (11).

11. Streaming output: while a command is still producing rows, the table renders incrementally. New rows append as they arrive. The header row locks in as soon as the separator line is received; rows before the separator render as plain text until the table is recognized.

12. Selection and copy:
    - Selecting across cells with the mouse or keyboard selects their visible text content.
    - Copying the selection produces tab-separated plain text by default (one row per line, cells separated by tabs). An affordance (context menu, shortcut) lets the user copy the original markdown source instead.
    - Copying the entire block preserves the original markdown source verbatim.

13. Search within a block (find-in-block) matches against cell text content. Matches highlight in place in the rendered cell; navigating matches scrolls the table into view, including horizontally if the match is in an off-screen column.

14. Sharing or exporting a block (Warp Drive, share link, save as file) preserves the original markdown source, not the rendered form.

15. Theming: table borders, header backgrounds, alternating row shading (if any), and link/code styles all come from the active Warp theme. No hard-coded colors.

16. Markdown tables render consistently wherever block-list markdown already renders — command output, agent responses, and any other block type that supports inline markdown. The same input produces the same table in each surface.

17. Non-table pipe content is not misrendered as a table. Text that contains `|` characters but no valid header-separator line remains plain text, even if it visually resembles a table.
````

Adapted from Warp Common Skills. See [provenance and license](../../reference/upstream.md).

When relevant personal facts or preferences affect this task, use [private context](../../reference/private-context.md). Load only the needed topics; ask about consequential unknowns and save confirmed updates through its tool. Keep personalized profiles and reports private.
