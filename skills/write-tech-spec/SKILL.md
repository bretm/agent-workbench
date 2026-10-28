---
name: write-tech-spec
description: Write a TECH.md spec for a significant feature after researching the current codebase and implementation constraints. Use when the user asks for a technical spec, implementation plan, or architecture doc tied to a product spec.
---

# write-tech-spec

Write a `TECH.md` spec for a significant feature.

## Overview

The tech spec should translate product intent into an implementation plan that fits the existing codebase, documents architectural choices, and makes the work easier for agents to execute and reviewers to evaluate.

## Project conventions and destination

Read project instructions and relevant existing specs first. Follow the project's document locations, templates, metadata, vocabulary, and authority rules. `PRODUCT.md` and `TECH.md` describe document roles; use established filenames when the project has them. Link existing decisions rather than creating duplicate policy or status owners.

When no convention exists, use `specs/<id>/TECH.md`, where `<id>` is an existing issue id or a short kebab-case feature name. Keep companion specs together. Infer a suitable feature name from the request; ask only if the choice matters.

Read [work-record ownership](../../reference/work-records.md) before planning adopted work or making a handoff. Spec writing is tentative unless adopted; it does not automatically publish issues or authorize implementation, prototypes, commits, promotion, or live operations. Preserve authorization already given in the session.

## When to use

Use this skill when the implementation spans multiple modules, has meaningful architectural tradeoffs, or when reviewers will benefit from seeing the plan before or alongside the code. For pure UI changes or straightforward fixes, a tech spec is often unnecessary.

Prefer to have a `PRODUCT.md` first so the technical plan is anchored to agreed behavior. If implementation is too uncertain, identify the bounded research or prototype needed to settle it. Record the uncertainty and use existing task authorization before doing that work.

## Research before writing

Ask one question at a time for consequential missing intent, wait for the answer, and adapt. Investigate repository facts yourself.

Before drafting, read the product spec (if any), inspect the relevant code, and identify the main files, types, data flow, and ownership boundaries. Do not guess about current architecture when the code can be inspected directly.
When referencing relevant code chunks in the spec, prefer commit-pinned references so future readers can inspect the exact code you researched. Capture the current commit SHA for each repository you inspected (for example, `git rev-parse HEAD`) and, when possible, make file references Markdown links to the corresponding GitHub `blob/<sha>/...#Lx-Ly` URL. Use the linked text to keep the path readable in the spec.

## Structure

Required sections:

1. **Context** — What's being built, how the current system works in the area being changed, and the most relevant files with line references. Combine the "problem," "current state," and "relevant code" into one grounded section. Example references:
   - [`src/cli.py:42 @ <commit-sha>`](https://github.com/OWNER/REPO/blob/<commit-sha>/src/cli.py#L42) — entry point for the user flow
   - [`src/transaction.py (120-220) @ <commit-sha>`](https://github.com/OWNER/REPO/blob/<commit-sha>/src/transaction.py#L120-L220) — state and event handling that will likely change
   Reference `PRODUCT.md` for user-visible behavior rather than restating it.
2. **Proposed changes** — The implementation plan: which modules change, new types/APIs/state being introduced, data flow, ownership boundaries, and how the design follows existing patterns. Call out tradeoffs when there is more than one reasonable path.
3. **Testing and validation** — How the implementation will be verified against the product behavior. Owns everything about proving the feature works: unit tests, integration tests, manual steps, screenshots, videos, and any other verification. Reference the numbered Behavior invariants from `PRODUCT.md` directly rather than restating them; each important invariant should map to a concrete test or verification step. This section is where validation lives — `PRODUCT.md` intentionally does not have a Validation section.
Optional sections — include only when they add signal. Omit the heading entirely if empty; do not write "None" as a placeholder.

- **Implementation sequence** — Include when ordering or prerequisites affect feasibility. Record dependencies without creating another execution-status owner. Session planning belongs in `plan-sessions` when requested.
- **End-to-end flow** — Include only when tracing the path through the system tells you something the Proposed changes list doesn't.
- **Diagram** — Include a Mermaid diagram only when a visual will explain the design faster than prose (data flow, state transitions, sequence across layers). Prefer one or two focused diagrams over decorative ones.
- **Risks and mitigations** — Include when there are real failure modes, regressions, migration concerns, or rollout hazards worth calling out.
- **Follow-ups** — Include when there is deferred cleanup or future work worth naming.

## Detail and readability

For a single-file change with a clear approach, skip the tech spec or keep it brief. Larger or uncertain changes need enough explanation for a reviewer to follow the design, its consequences and how it will be verified. Preserve required technical content, introduce unfamiliar terms and connect implementation details to the behavior or constraint they serve. Completeness requires readable explanations as well as coverage. Follow the shared working agreements' quiet review before saving.

If Context and Proposed changes end up describing the same files and state from different angles, collapse them.

## Writing guidance

- Ground the plan in actual codebase structure and patterns.
- Pin important code references to a commit SHA and link them to the corresponding GitHub lines when the repository has an accessible remote.
- Prefer concrete implementation guidance over generic architecture language.
- Explain why the proposed design fits this repo.
- Reference `PRODUCT.md` for behavior instead of restating it.
- Each section should earn its place — if a section would repeat another or contain only boilerplate, omit it.

## Keep the spec current

Approved specs may ship in the same PR as the implementation. Update `TECH.md` in the same PR when module boundaries, implementation sequencing, risks, validation strategy, or rollout assumptions change. The checked-in spec should describe the implementation that actually ships.

Use existing project decision records first. Where no convention exists, the implementer may optionally keep a `DECISIONS.md` file summarizing concrete decisions. Offer it when it would help future agents; otherwise skip it.

## Related skills

[write-product-spec](../write-product-spec/SKILL.md) defines the behavior this design implements. When asked to split agreed work into sessions, use [plan-sessions](../plan-sessions/SKILL.md).


Adapted from Warp Common Skills. See [provenance and license](../../reference/upstream.md).

When relevant personal facts or preferences affect this task, use [private context](../../reference/private-context.md). Load only the needed topics; ask about consequential unknowns and save confirmed updates through its tool. Keep personalized profiles and reports private.
