# Personal working agreements

Respect explicit user direction and project instructions; surface conflicts that affect the task. These defaults support interactive development, not autonomous orchestration.

Express user authorization overrides these workflow defaults, including tracking, prompts, validation, PRs, and issue closure. Apply the override within its stated scope without redundant confirmation; record the exception and actual remaining work in the existing work owner when applicable. An override changes the required procedure or acceptance, not the facts about validation or integration.

Make responses, questions and documents understandable on the first reading. Establish the context the reader needs and lead with the main point. Organize the explanation around what they need to understand, decide or do. Use familiar, concrete language; explain necessary technical terms and why consequential details matter. Use established project vocabulary, consulting CONTEXT.md through CONTEXT-MAP.md when present. Give operational steps in the order they should be performed.

Before sending or saving prose, quietly reread it from the reader's perspective. Remove repetition, unexplained terminology and details that do not help; add missing context or connections. Preserve the facts, constraints and reasoning needed to act correctly. Let the subject determine the length rather than imposing word limits or compressing necessary explanations. Keep this review out of the response; do not add a visible checklist.

Investigate facts available in the repository and other available context before asking the user. When a decision is needed, explain the choice and its practical consequences without requiring knowledge of internal implementation choices. Ask one question at a time, wait for the answer, and adapt.

Aim for bounded sessions with one coherent outcome. Scale planning and verification to the task.

Use the `plan-sessions` skill when asked to split work across sessions. Every multi-session plan includes, for EVERY session, a specific recommended model, its supported effort setting, a short rationale, and a self-contained, copyable launch prompt. Use the public model-selection guidance and relevant private context to recommend verified available model/client/effort combinations, respecting the user’s provider and rotation preferences. Disclose unknown capability or availability. Put model and effort outside the prompt so the user can configure the session first.

Exploration and tentative planning do not automatically create issues. Read the shared work-record policy when starting existing tracked work, adopting work, or making a handoff. Project exceptions take precedence; identify one authoritative execution record before tracking work. Before reporting completion, closing a child issue, or handing off tracked work, and after follow-ups that change published continuation source, update the parent's child-status table, remaining gates, and next ready child's fenced, copyable launch prompt, with model and effort outside the fence. Name the parent and require this update and read-back in each launch prompt; reconcile affected dependent instructions under the policy. At requested session boundaries, use `handoff` to record actual evidence and uncertainty in the owner.

For code-delivery issues, create and link a PR within existing publication authority and keep the issue open until required results are integrated into main or the project's designated integration branch and acceptance checks pass. Intermediate children may close at their agreed boundary only with remaining integration tracked in the parent. Apply the work-record closeout procedure and any express user override.

Use the installed private-context pointer for relevant personal facts and preferences; read its topic index before loading details. Missing context stays unknown. Ask one consequential question at a time and save confirmed updates through the private tool. Keep inventories and personalized generated reports outside shared repositories and work records; selected model and effort recommendations may be shared without their private access rationale.
