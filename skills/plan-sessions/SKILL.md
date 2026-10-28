---
name: plan-sessions
description: Split an agreed task into bounded interactive sessions with completion evidence, model and effort guidance, and fresh-session launch prompts.
---

Read [the model reference](../../reference/models.md), [the work-record policy](../../reference/work-records.md), project instructions, the selected work record and relevant docs. Resolve repository facts yourself. Ask one question and wait when a missing decision materially changes the plan; explain what the choice changes for the user.

Confirm the agreed outcome, constraints, status owner and remaining uncertainty. Follow the work-record policy for ownership, publication and completion, including express user overrides. Planning remains tentative until adopted; a request to plan does not authorize creating or publishing issues.

Split the work into sessions with one coherent outcome and a reviewable exit condition each. Explain how the sessions lead to the agreed result and where a research or decision session must settle uncertainty first. Keep scope credible for one session. Distinguish intermediate session completion from delivery and include any required PR and integration gates.

For every session, provide:

- Prerequisites and dependencies, scope and exclusions, and evidence that will establish completion.
- The session's role, a specific primary model and supported effort, the harness that supports them, and a short task-based rationale.
- A separate fenced, copyable launch prompt, with model, effort, rationale and setup guidance outside the fence.

Choose each session's model and effort using the public model-selection guidance and relevant [private context](../../reference/private-context.md). Load the user's access, rotation preferences, role choices, and dated local launch evidence when available. Recommend from verified available options, explain the task-based reason, and respect explicit user choices. Ask for consequential missing access or preference facts rather than assuming a provider. Keep personalized inventories and generated comparisons private; include only the chosen model/client/effort and useful task rationale in shared plans.

Each prompt must work without this conversation. Name the project, authoritative record path or URL, accepted source state, essential context, bounded outcome, scope and exclusions, prerequisite checks, validation and owner to update. Require checking that the latest accepted prerequisite source contains required fixes under the work-record policy. Make local-only or uncommitted sources and unmerged work explicit so the next session can find the right starting point.

When a parent exists, name its record directly in each prompt. Require updating and reading back the owner, parent's child-status table, remaining gates and next ready child's prompt, and affected dependent instructions before finishing, using the policy's reconciliation procedure. When publication is authorized, keep the coordination section and next ready prompt in the existing parent under that policy.

Mark later prompts provisional when earlier work may change them, and explain what must be refreshed before launch. Check that every session has the required information and a usable prompt. Finish by identifying the next bounded session.
