---
name: grill-with-docs
description: Grill a plan or design while capturing agreed domain language and significant decisions in project documentation.
---

Use the [grilling workflow](../grilling/SKILL.md): investigate the repository, ask one question at a time, and stop when the decision is sufficiently resolved.

Read the project's existing domain vocabulary and decision records, including CONTEXT-MAP.md and the relevant CONTEXT.md when present. Follow project instructions, document locations and formats; do not create a competing glossary. Challenge ambiguous or conflicting terms, check claims against the code, and use concrete scenarios to clarify domain boundaries. Surface discrepancies for resolution rather than assuming the code or the conversation is authoritative.

As terms are agreed, update the appropriate existing domain document inline. If none exists, create CONTEXT.md when there is a substantive term to record, unless project conventions specify another location. Keep domain vocabulary separate from implementation details and distinguish agreed meaning from unresolved questions.

Offer an architecture decision record only when the decision is costly to reverse, surprising without context, and involves a real trade-off. Follow the project's ADR conventions; if none exist, use docs/adr/ and record the decision, context, alternatives and reasons. Create documents only when there is something substantive to capture. Respect the user's requested scope and any project restrictions on documentation changes.

Adapted from Matt Pocock's grill-with-docs and domain-modeling skills; see [attribution](../../reference/upstream.md).
