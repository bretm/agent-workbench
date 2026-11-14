---
name: plan-sessions
description: Split an agreed task into bounded interactive sessions with completion evidence, model and effort guidance, and fresh-session launch prompts.
---

Read [the model reference](../../reference/models.md), [the work-record policy](../../reference/work-records.md), project instructions, the selected work record and relevant docs. Resolve repository facts yourself. Ask one question and wait when a missing decision materially changes the plan; explain what the choice changes for the user.

Confirm the agreed outcome, constraints, status owner and remaining uncertainty. Follow the work-record policy for ownership, publication and completion, including express user overrides. Keep tentative exploration in conversation or an explicitly requested planning document; a request to plan does not authorize creating or publishing issues. Once adopted and publication is authorized, use GitHub issues for execution status, reusing existing owners and avoiding speculative issue trees or another status document.

Split the work into sessions with one coherent outcome and a reviewable exit condition each. Explain how the sessions lead to the agreed result and where a research or decision session must settle uncertainty first. Keep scope credible for one session. Distinguish intermediate session completion from delivery and include any required PR and integration gates.

For every session, provide:

- Prerequisites and dependencies, scope and exclusions, and evidence that will establish completion.
- The session's role, a specific primary model and supported effort, the harness that supports them, and a short task-based rationale.
- Readiness or concrete activation conditions when blocked or deferred.

Provide one compact, fenced, copyable launch prompt for the next ready session, with model, effort, rationale and setup guidance outside the fence. If no session is ready, state what must be resolved before launch instead of supplying an executable prompt.

Choose each session's model and effort using the public model-selection guidance and relevant [private context](../../reference/private-context.md). Load the user's access, rotation preferences, role choices, and dated local launch evidence when available. Recommend from verified available options, explain the task-based reason, and respect explicit user choices. Ask for consequential missing access or preference facts rather than assuming a provider. Keep personalized inventories and generated comparisons private; include only the chosen model/client/effort and useful task rationale in shared plans.

The prompt must work without this conversation. Name the project, execution owner, accepted source state and bounded outcome. Link authoritative records for essential context, scope, exclusions, prerequisites and completion criteria. Reference shared project procedures for ordinary build, validation, preservation, publication and closeout; include task-specific exceptions, consequential constraints and checks. Require verifying the latest accepted prerequisite source under the work-record policy. Make local-only or uncommitted sources and unmerged work explicit so the next session can find the right starting point.

When a parent exists, keep the single next ready prompt there; children and other continuation records link to it rather than duplicate it. Name the parent in the prompt and require reconciliation and read-back of the owner, parent's child-status table, remaining gates, next prompt and affected dependents under the policy before finishing. With no parent, keep the prompt in the execution owner or the requested conversational plan.

Maintain issue bodies as current plans: replace stale scope, prerequisites and prompts instead of adding another status section. Parents coordinate; ordinary children retain current status, outcome, remaining work, blockers, completion criteria and essential evidence links. Keep durable design and detailed evidence in appropriate existing repository docs. Check that every session has the required information, the next ready session has a usable prompt, and blocked or deferred work has activation conditions without executable prompts. Apply the work-record policy's fresh-reader review before publishing. Finish by identifying the next bounded session or the condition that will make one ready.
