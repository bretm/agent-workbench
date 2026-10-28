---
name: handoff
description: Capture a requested interactive session boundary in the existing work owner and provide the next fresh-session prompt with model and effort guidance.
---

Read [the work-record policy](../../reference/work-records.md), [the model reference](../../reference/models.md), and [session prompt requirements](../plan-sessions/SKILL.md). This captures a human-led session boundary.

Inspect the current work owner, changes, branch, commit and uncommitted state. Compare the actual outcome with acceptance criteria. Explain what was accomplished, what the evidence establishes, and what must happen next. Distinguish validated work, implementation awaiting verification, and blocked or unfinished work. Include validation commands, results and limits, unresolved decisions and the next concrete step; a passing subset or skipped check does not establish full completion.

Update the existing owner using the work-record policy's reconciliation and closeout procedures. They govern contributing sources, PR and integration evidence, parent coordination, dependent instructions, verification of the continuation source, publication authority and read-back. Record express user overrides and any remaining delivery gates. If publication is unavailable, prepare temporary ready-to-post updates and identify what remains unpublished. With no owner, use a temporary handoff unless a durable record is requested.

Provide the next session's prerequisites, bounded outcome, validation and a self-contained, copyable launch prompt following `plan-sessions`. Include the project, verified continuation source, owner, essential context, authoritative links, known blockers and completion evidence. Put the specific model, supported effort, harness and task-based rationale outside the prompt, following the model reference's availability, efficiency and escalation rules. If a parent exists, name it in the prompt and require updating and reading back the owner, parent coordination and next prompt, and affected dependent instructions under the work-record policy before finishing. Mark the prompt provisional if a decision remains open, and explain what must be settled before launch.

Adapted in part from Matt Pocock's handoff; see [attribution](../../reference/upstream.md).

When relevant personal facts or preferences affect this task, use [private context](../../reference/private-context.md). Load only the needed topics; ask about consequential unknowns and save confirmed updates through its tool. Keep personalized profiles and reports private.
