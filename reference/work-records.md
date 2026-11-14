# Work records

Express user authorization overrides the workflow defaults in this policy, including record maintenance, prompts, validation, PR creation, and closure gates. Follow it within its stated scope without asking for the same authorization again. Record the override and actual remaining work in the existing execution owner when applicable; preserve accurate validation and integration status. Permission to override a rule is not itself a waiver of every rule for the current task.

## Ownership and adoption

GitHub issues own adopted work and its current execution status. Repository docs own lasting product direction, architecture, decisions, current behavior, and detailed technical evidence. Link supporting docs rather than duplicating them. Use appropriate existing documents; a routine status update does not need a new document.

Keep tentative exploration in conversation or an explicitly requested planning document. Move it to issues only when the user adopts the work and authorizes tracker publication; planning alone grants neither adoption nor publication authority. Do not create speculative issue trees. Name one execution-status owner. Use a parent for coordination when needed and child issues for coherent outcomes. Keep future or dormant scope deferred, with concrete activation conditions; create or activate executable work when prerequisites and acceptance are clear.

Read this policy when starting existing tracked work as well as when adopting work or making a handoff. Identify the execution owner and any parent from the existing records before implementation.

## Current issue bodies

An issue body is the current actionable plan. Edit or replace obsolete content when facts change; do not prepend a new “current” section above historical status, superseded prerequisites, duplicate instructions or obsolete prompts. Remove stale content wherever it appears in the body, including collapsed sections. Preserve consequential decisions and evidence through appropriate links, not competing instructions.

- **Ordinary children:** state current status, intended outcome and consequential scope boundaries, remaining work, dependencies or blockers, completion criteria, and essential evidence links. Include the accepted source when needed to resume. Scale detail to the task without a rigid word limit. Summarize what validation establishes and what remains uncertain; keep detailed runtime logs out of the body.
- **Parents:** coordinate with one table row per child, showing its link, status, and actual remaining gates or blockers. Keep overall acceptance and integration gates visible. Include one compact, fenced, copyable prompt for the next ready session, with its specific model, supported effort, client and short rationale outside the fence. Children link to that prompt instead of duplicating it. If no session is ready, say what must happen first and omit the executable prompt. Blocked and deferred work carries activation conditions, not launch prompts. Remove or replace the previous prompt as readiness changes.
- **Instructions:** reference shared project instructions for ordinary build, validation, preservation, publication and closeout procedures. Include task-specific exceptions, consequential constraints and required acceptance checks that those instructions do not already cover. Prompts point to authoritative records and evidence rather than repeat their bodies or general procedures.
- **Comments:** use them for significant decisions or new evidence worth retaining, with the reason or consequence. Update the body when that changes the plan. Do not routinely copy previous bodies into comments or post repetitive progress logs. Comments must not be required to discover the current plan.

Before publishing an update, apply this practical review: a fresh reader must be able to identify what remains, what blocks it, and what finishes it without reading historical updates. Preserve explicit user direction, acceptance requirements and meaningful uncertainty while removing repetition.

## Issue closeout

At completion and session boundaries, rewrite the owner to reflect actual remaining work; update existing docs when a decision or behavior becomes established. At closure, leave a short record of the accepted result or disposition, delivery/integration and acceptance evidence, material limits, and the owner of unfinished work (or explicitly none). Remove obsolete continuation prompts and completed task lists that no longer help explain the result. Label deferred or superseded closure as such, with activation conditions or a successor link; neither means the work was completed.

Issue closeout follows these defaults unless project instructions or express user authorization specify otherwise:

- For code-delivery issues, create or update and link the PRs needed to bring the required results from all contributing branches into main or the project's designated integration branch, within existing publication authority. Keep the necessary source branches, relevant commits, target branch, validation summary and PR/evidence links in the execution owner. Keep the issue open while required review or integration is pending. If publication is unavailable, prepare ready-to-post PR content and identify the unpublished work and available source; do not silently treat branch completion as delivery.
- An intermediate child may close when its explicitly agreed outcome is complete and validated, even if delivery requires later integration. Record its accepted source and remaining integration work in the parent, identify the next responsible issue or mark the integration work unassigned and blocked, and retain the parent's integration gate.
- Before closing a delivery issue or parent as complete, verify that the required results from its contributing branches are present in the target branch and required acceptance checks pass. Link PRs and integration evidence, checking ancestry or equivalent changes where appropriate. Distinguish implemented and tested on a branch, PR awaiting review, and integrated and complete. Research or other issues without repository changes do not require a PR solely to close.

## Merge checkout closeout

Completing an authorized merge includes returning the session's checkout to its updated merge target before handing control back. This applies whether the agent merges or the user reports merging during the active task, and whether or not an issue tracks the work. Explicit user direction and project instructions take precedence.

1. Confirm that the merge completed and identify its actual target branch and remote from the merge or PR evidence. Do not assume `main` or `origin`. For squash or rebase merges, use confirmed merge metadata or equivalent-change evidence; source-branch ancestry alone may not establish integration. If the merge or target cannot be verified, report that uncertainty before changing the checkout.
2. Inspect the session's checkout for staged, unstaged and untracked changes, an in-progress Git operation, local commits and linked worktrees. Require a clean working tree and no in-progress Git operation before switching. Preserve local work and commits; do not automatically stash, commit, discard, reset, force a switch, delete a branch or remove a worktree to complete this procedure. If the target is checked out in another worktree, report its location and the blocked switch without modifying that other checkout.
3. Fetch the verified target from the correct remote. If fetching fails, report that the local checkout has not been verified as current. Check any existing local target branch against the fetched remote target before switching. Leave a branch with local commits ahead of or divergent from that target unchanged and report the reconciliation needed.
4. Switch this checkout to the actual target, creating a local tracking branch if needed, and update it using a fast-forward only. Use the verified remote target explicitly rather than assuming an existing upstream points to it. If any step is blocked, preserve the current state and explain the obstacle and remaining work.
5. Verify and report the final branch, whether the working tree is clean, and whether local `HEAD` matches the fetched remote target. Claim that the checkout is up to date only when this verification succeeds. Keep integration and acceptance evidence separate from any unfinished checkout closeout; record the remaining step in the existing execution owner when one exists.

## Work-record reconciliation

Before reporting completion, closing a child issue, or handing off tracked work, and after changes to scope, prerequisites or accepted continuation source (even after child closure), reconcile the existing records:

1. Replace stale owner content with current status, remaining work, evidence links, validation summary, limits and uncertainty. Preserve task-specific user direction and exceptions. This ownership does not suppress parent coordination updates or create another execution owner.
2. If a parent exists, reconcile its child table, actual remaining gates and single next ready prompt under the body rules above. Follow the model reference and session-planning requirements for settings. The prompt must work without this conversation: name the project, owner and parent, accepted continuation source, bounded outcome, and authoritative links for essential context, prerequisites and completion criteria. State task-specific constraints or checks and require reconciliation and read-back under this policy before finishing. Reference shared procedures rather than copying them. If no child is ready, replace the prompt with activation conditions. A passing subset does not complete the parent or unblock dependent work whose prerequisites remain unmet.
3. Inspect affected dependents in existing issues, plans and handoffs when scope, prerequisites or accepted source changes, including after child closure. Update the facts and links that changed rather than copying the same narrative into every record. Remove obsolete or duplicated prompts; keep children pointing to the parent's current prompt and blocked work to its activation conditions. For Git continuations, identify the latest accepted prerequisite source and verify it contains the required fixes, using an ancestry check such as `git merge-base --is-ancestor <required-fix-commit> <continuation-ref>` where appropriate. For rebased or cherry-picked fixes, verify equivalent changes and link the evidence. Do not assume an unmerged branch is present on main; name the available source and any remaining integration gate.
4. Publish within existing authority and project exceptions; already-authorized maintenance needs no redundant confirmation. Read back published owner, parent and dependent changes before claiming reconciliation is complete. If access or authority is missing, prepare temporary ready-to-post updates, identify exactly which records and changes remain unpublished, and keep the existing owner authoritative. With no parent, reconcile only affected existing records; with no owner, use a temporary update unless a durable record is requested. Do not create issues from tentative planning.

Preserve explicit project exceptions, including document-owned work records and offline trackers. Fit existing paths. Before migration, reconcile active scope and evidence with the proposed owner and replace duplicate status with pointers. Retain significant historical evidence where appropriate; do not archive every previous issue body. Do not silently reinterpret competing policies or import a project's orchestration rules into this interactive workflow.

## Compact examples

These fictional excerpts illustrate body maintenance, not mandatory templates. Evidence references stand for links to existing records; replace model settings with verified choices when publishing a prompt.

### Active child

Before:

```markdown
Current: parser implemented; integration remains.
Previous status: blocked on #41. Start from parser-v1.
Plan: research parsing, implement, test, integrate.
Launch prompt: start from parser-v1; run all standard procedures ...
Latest run: [many lines of runtime output]
```

After:

```markdown
Status: parser implemented on parser-v2 at abc123; PR #51 awaits review.
Outcome: accept quoted fields without changing unquoted input.
Remaining: integrate #51 into main and pass the acceptance cases in docs/parser.md.
Blocker: PR #51 review. Source includes #41's prerequisite fix (PR #51 evidence).
Evidence: targeted cases pass (CI run 81); integrated behavior is unverified.
Next session: see parent #40's “Next session” prompt. Follow AGENTS.md.
```

### Coordinating parent

Before:

```markdown
Current: #43 is ready from parser-v2.
Old gates: finish #41; use parser-v1 for #43.
Sessions: [repeated child plans, evidence logs and prompts for #42–#44]
```

After:

````markdown
| Child | Status | Remaining gate or blocker |
|---|---|---|
| #42 Parser | Intermediate outcome accepted; source abc123 | Integration owned by #43; evidence in #42 |
| #43 Delivery | Ready | Integrate PR #51 and pass docs/parser.md acceptance cases on main |
| #44 Stress test | Deferred | Activate after #43 and an agreed load target |

Remaining parent gate: #43's integration and acceptance evidence. #44 is outside this delivery.

### Next session

Model / effort / client: <verified settings>. Rationale: integration and acceptance checks.

```text
In sample-project, complete #43 under parent #40 from parser-v2 at abc123
(PR #51, unmerged). Read AGENTS.md, #43 and docs/parser.md for scope and checks.
Verify the accepted source, integrate and validate the quoted-field behavior.
Follow the shared work-record policy to reconcile and read back the owner,
parent table, remaining gates, next prompt and affected dependents before finishing.
```
````

### Closed issue

Before:

```markdown
Done. Earlier: integration pending; rerun the suite tomorrow.
Next prompt: resume parser-v1 ...
[completed checklists and repeated run logs]
```

After:

```markdown
Completed: quoted fields accepted; unquoted behavior preserved.
Delivery: PR #51 merged into main at def456; required changes verified there.
Acceptance: docs/parser.md cases pass on def456 (CI run 89).
Limit: stress testing was outside accepted scope; deferred work owned by #44.
```

For a deferred or superseded closure, use a disposition such as “Deferred, not implemented; #44 owns reactivation after an agreed load target” or “Superseded by #45; no completion claimed,” with any material evidence and limits. Do not retain a runnable continuation prompt in the closed issue.
