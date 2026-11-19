---
name: write-spec
description: Write and fresh-context verify a design specification before implementation. Use when the user asks for a spec, design doc, PRD, or technical plan, or when moving from brainstorming and grilling to an execution-ready specification.
---

# write-spec

Write and verify an execution-ready specification for a feature or technical change.

## Overview

The specification turns decisions agreed in conversation and [grilling](../grilling/SKILL.md) into a single, codebase-grounded document that a fresh agent session can implement and verify without guessing. It connects observable behavior, module and interface boundaries, commit-pinned code touchpoints, and concrete verification in one place.

Trivial fixes or narrow single-file tweaks do not need a spec file; an in-chat summary or issue description is enough. Use this skill when behavior has nontrivial invariants or edge cases, when changes span multiple modules, or when the design will be handed off to another session for execution.

Read [work-record ownership](../../reference/work-records.md) before planning adopted work or making a handoff. Spec writing is tentative unless adopted; it does not automatically publish issues or authorize implementation, prototypes, commits, promotion, or live operations. Preserve authorization already given in the session.

## Project conventions and destination

Read project instructions and relevant existing specs first. Follow the project's document locations, templates, metadata, domain vocabulary (`CONTEXT.md` and `CONTEXT-MAP.md` when present), and authority rules. Link existing decisions rather than creating duplicate policy or status owners. Keep durable design in appropriate repository docs and execution status in the adopted work's issue; routine progress does not need a new spec or decision document.

- **Default unified target:** When no project convention exists, write one cohesive spec at `specs/<id>/SPEC.md`, where `<id>` is an existing issue id or a short kebab-case feature name. Infer a suitable name from the request; ask only if the choice matters.
- **Project-mandated layouts (Spec Kit or split specs):** When a repository standardizes on GitHub Spec Kit (`.specify/` or `specs/<id>/spec.md` and `plan.md`) or split product and technical documents (`PRODUCT.md` and `TECH.md`), emit those files instead while applying the same synthesis, `[NEEDS CLARIFICATION]` rules, and fresh-context review below. Keep execution status in the authoritative work record rather than creating a competing task checklist unless the project explicitly requires `tasks.md`.

## Step 1: Synthesize and research (do not re-interview from scratch)

Start from the decisions, scope boundaries, and trade-offs already settled in the current conversation and [grilling](../grilling/SKILL.md). Do not restart a generic discovery interview over topics the user already discussed.

1. **Inspect the codebase directly:** Identify the entrypoints, types, data flow, ownership boundaries, and existing test suites. Do not guess about current architecture when the code can be read.
2. **Capture commit-pinned references:** Record the current commit SHA (`git rev-parse HEAD`) for each inspected repository. When referencing code chunks, use commit-pinned links (`https://github.com/OWNER/REPO/blob/<sha>/path#Lx-Ly` when an accessible GitHub remote exists, or `path:line @ <sha>`) so future readers and fresh sessions see the exact code researched.
3. **If invoked cold on a rough idea:** When high-impact decisions are still unsettled and prevent framing an approach at all, use [grilling](../grilling/SKILL.md) first—asking one question at a time with a recommendation grounded in the codebase—until the core direction and boundaries are clear.
4. **Never silently invent second-order requirements:** When drafting or mapping decisions to the code exposes an unagreed detail or edge case that neither prior conversation nor existing code answers, do not make up a rule to keep the prose flowing. Insert an inline tag:
   `[NEEDS CLARIFICATION: <specific question — recommended default and practical consequence>]`

## Step 2: Draft the specification

Write concrete, observable rules and codebase-grounded plans. Omit optional headings that would be empty or repeat another section; never write `"None"` as a placeholder.

### Required sections

1. **Summary and scope** — Briefly state the problem, desired outcome, target consumer or surface (human UI user, CLI caller, API/library consumer, or data-model reader/writer), and explicit exclusions or non-goals when scope could be misread. If the feature has visual or interaction design, include a Figma/design link (or an explicit `Figma: none provided` note when design matters but no mock exists; omit for non-visual work).
2. **Behavior invariants** — A complete description of how the feature behaves from the consumer's perspective, written as numbered, testable invariants. Cover:
   - Default behavior and the primary flow.
   - Consumer-visible states, transitions, inputs, and outputs.
   - Empty, loading, error, cancellation, and fallback behavior.
   - Consequential edge cases (permissions, timeouts, concurrency/races, stale or malformed input, resize/reflow, accessibility/keyboard expectations where relevant, and interaction with adjacent features).
   - Non-regression invariants that must continue to hold.
   Keep internal implementation mechanics out of Behavior invariants so each numbered rule defines *what* must hold.
3. **Codebase context and proposed changes** — Ground the technical plan in the live repository:
   - **Current state:** How the area being changed works today, with commit-pinned file and line references (for example, [`src/cli.py:42 @ <sha>`](https://github.com/OWNER/REPO/blob/<sha>/src/cli.py#L42)).
   - **Module and interface boundaries:** Which modules own the change, new or modified types/APIs/state, and how the design fits existing patterns. Prefer deep modules (substantial behavior behind a small, clear interface) over scattering shallow pass-through wrappers across layers.
   - **Trade-offs and risks:** Call out material alternatives considered, failure modes, migration/rollout hazards, or ordering constraints when more than one reasonable path exists.
4. **Verification plan** — How the implementation will be proven against the Behavior invariants:
   - **Primary testing seam(s):** Name the cleanest existing interface or entrypoint where tests will verify the behavior (preferring high-level public or CLI/API seams over brittle internal mocks).
   - **Invariant mapping:** Reference the numbered Behavior invariants directly instead of restating them, mapping every invariant to a concrete automated test (naming the target test file or suite) or an explicit manual/browser verification step.

## Step 3: Automatic "Goldfish" check (zero-context review)

An agent session that participated in brainstorming and grilling holds unstated context in its chat window and cannot reliably spot what it forgot to write down. Immediately after writing the draft spec to disk—and before declaring the draft ready—run **one fresh-context review pass**:

1. **Run a zero-context reader:**
   - When the current harness supports launching a read-only subagent with an isolated context, invoke **one** read-only reviewer and give it *only* the spec file path(s) and repository access. Do **not** include a summary of the chat conversation or unrecorded rationale in the subagent prompt.
   - When no isolated subagent is available, perform a strict artifact-only audit by reading only the written spec file and its referenced code files from disk, treating anything present only in chat history as missing from the spec.
2. **Audit against four criteria:**
   - **Cold comprehension:** Which terms, flows, or assumptions rely on unstated chat history or undefined domain vocabulary?
   - **Simplicity and scope (YAGNI):** Did speculative abstractions, unrequested features, or shallow pass-through layers sneak into the design?
   - **Traceability:** Does every numbered Behavior invariant map to a concrete proposed code change and a verification step at an agreed testing seam?
   - **Implementation readiness:** Do all referenced file paths, symbols, and signatures match the live codebase, and where would a fresh coding session still have to guess?
3. **Triage findings before presenting to the user (Elephant triage):**
   Do not dump a raw wall of reviewer complaints on the user. Verify each finding against the codebase and conversation history:
   - **Auto-fix omissions:** If a finding points out something already settled in chat or clear from the codebase that was omitted or ambiguous in the text, edit the spec file immediately.
   - **Dismiss false alarms:** If the zero-context reader misread the codebase, discard the finding silently.
   - **Tag genuine forks:** If a finding exposes a real product or architectural decision that has not been made yet, insert an inline `[NEEDS CLARIFICATION: <specific question — recommendation and consequence>]` tag in the spec.

## Step 4: Resolve `[NEEDS CLARIFICATION]` tags one at a time

Present the tightened spec to the user, briefly noting any gaps the Goldfish check caught and auto-fixed.

If any `[NEEDS CLARIFICATION]` tags remain in the spec:

1. Pick the highest-impact tag whose prerequisites are settled. Ask **one** clear question with a concise recommendation and practical consequence, then stop and wait for the user's answer.
2. Update the spec with the agreed decision and remove the tag before moving to the next question.
3. Repeat until **zero `[NEEDS CLARIFICATION]` tags remain**. If a question genuinely cannot be answered without a prototype or research spike first, replace the tag with an explicit prerequisite so [plan-sessions](../plan-sessions/SKILL.md) schedules that probe before implementation rather than leaving a coding agent to improvise.

## Keep the spec current

Follow the shared working agreements' quiet review before saving. Approved specs may ship in the same PR as the implementation; update the spec when user-visible behavior, module boundaries, or verification strategy change during implementation so the checked-in document matches what ships.

## Related skills

- [grilling](../grilling/SKILL.md) and [grill-with-docs](../grill-with-docs/SKILL.md) stress-test decisions and record domain language before or during spec writing.
- [plan-sessions](../plan-sessions/SKILL.md) splits the verified spec into bounded interactive sessions with model/effort guidance and a fresh-session launch prompt.

When relevant personal facts or preferences affect this task, use [private context](../../reference/private-context.md). Load only the needed topics; ask about consequential unknowns and save confirmed updates through its tool. Keep personalized profiles and reports private.
