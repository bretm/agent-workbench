---
name: grilling
description: Stress-test a plan, design, or decision when asked to grill it, using one question per turn and bounded probing.
---

Read the proposed decision and relevant repository evidence. Map the decisions and their dependencies privately; find facts in the repository rather than asking the user to retrieve them.

Choose the highest-impact unresolved decision whose prerequisites are settled. Ask ONE clear question, give a concise recommendation and reason where useful, then stop and wait for the answer. Do not bundle additional questions into prose, a list, or a tool call. Adapt the next question to the answer.

Stop when enough is known to make the requested decision: material alternatives, constraints, risks and acceptance are understood. Summarize the recommendation, agreed decisions and remaining uncertainty. Do not probe every imaginable branch or require another confirmation when the user has already authorized the resulting work. Planning does not automatically publish issues.

Adapted from Matt Pocock's grilling and grill-me concept; the batching, harness-specific tool and mandatory delegation requirements were removed. See [attribution](../../reference/upstream.md).

When relevant personal facts or preferences affect this task, use [private context](../../reference/private-context.md). Load only the needed topics; ask about consequential unknowns and save confirmed updates through its tool. Keep personalized profiles and reports private.
