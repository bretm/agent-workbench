# Skill provenance

Original material in agent-workbench is licensed under the [MIT License](../LICENSE), copyright (c) 2026 bretm. Third-party material, including copied and adapted portions, remains subject to its original licenses and notices. This repository's MIT license does not replace or supersede those terms. The sections below identify the applicable sources, attribution and license texts.

## UI UX Pro Max

Source: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.
Inspected revision: `56ea9cf174ed86786187daa9de0e6247cb0747e4`, 2026-10-18.
License: [MIT, copyright 2024 Next Level Builder](UI-UX-PRO-MAX-LICENSE.txt).

| Adopted skill | Source paths | Adaptation / dependency resolution |
|---|---|---|
| ui-ux-pro-max | .claude/skills/ui-ux-pro-max/SKILL.md; references/; data/; scripts/*.py | Full runtime data, references and search helpers retained. Description shortened; plugin-specific script paths replaced with the installed skill directory and Python 3 `-B`; search and validation entrypoints suppress bytecode in managed releases. Existing design decisions and focused UX queries take precedence over generating a new system. Upstream development tests omitted from the installed pack. No dependency on another skill, package installer or network service for search. |

Source paths above are relative to the pinned repository root. Dataset provenance and font/icon metadata remain bundled. The workbench distributes guidance and search data, not font binaries or third-party framework packages. Review future changes against this revision; workbench updates never fetch upstream code automatically.

## Taste Skill

Source: https://github.com/Leonxlnx/taste-skill.
Inspected revision: `a9c73c3d5dbf401e3e47f86e7b41f29ede1687df`, 2026-10-18.
License: [MIT, copyright 2026 Leonxlnx](TASTE-SKILL-LICENSE.txt).

| Adopted skill | Source paths | Adaptation / dependency resolution |
|---|---|---|
| design-taste-frontend | skills/taste-skill/SKILL.md; references/; scripts/; library/; assets/ | Full page/app guidance, design libraries, runtime scripts and starter assets retained. Original detailed entrypoint moved to references/page-workflow.md to avoid native instruction truncation; a portable entrypoint routes to page/app guidance. Workbench scope, brand precedence, bounded review and private output guidance added. Draw history defaults to the chosen output directory rather than the user home; browser cleanup no longer sweeps other temporary profiles. Upstream README and evaluation fixtures omitted. No dependency on another skill or installer-owned runtime. |

Source paths above are relative to the pinned repository root. The full inspector needs Node 22+ and an existing browser; image search accesses upstream public media services and retains credits. The pin includes the shared scene stage but no scene catalogue or individual demos; this limitation is explicit in the skill. Website research and media references retain their upstream metadata; referenced media are not bundled image downloads. These are locally controlled adaptations, not synchronized mirrors.

## Playwright CLI

Source: https://github.com/microsoft/playwright-cli.
Inspected revision: `b85c7a736bb473bf55b584e54a09ffa698d6d871`, 2026-10-16; package version `@playwright/cli` **0.1.22**.
License: [Apache-2.0](PLAYWRIGHT-CLI-LICENSE.txt), Microsoft Corporation. No upstream NOTICE file was present at this revision.

| Adopted skill | Source paths | Adaptation / dependency resolution |
|---|---|---|
| playwright-cli | skills/playwright-cli/SKILL.md; references/running-code.md; references/session-management.md; references/storage-state.md; references/playwright-tests.md; references/tracing.md | Modified adaptation: short portable entrypoint and condensed command reference; harness-specific allowed-tools metadata removed; task-scoped sessions, existing project tests, runtime discovery and private evidence conventions added. Automatic package/bootstrap installation, broad session cleanup, mandatory test-plan documents, and publication recipes omitted. No dependency on another skill or installer-owned runtime. |

The upstream reference paths in the table are relative to `skills/playwright-cli/`. This repository distributes adapted guidance and the upstream license, not the CLI package or browser binaries. Verify runtime availability separately. Review future upstream changes against the pinned revision; installer updates never download upstream content.

## Warp Common Skills

Source: https://github.com/warpdotdev/common-skills.
Inspected revision: `7c4eb852de8d7c3e68c81802e1c59db9a611f914`, 2026-10-10.
License: [MIT, copyright 2026 Denver Technologies, Inc.](WARP-COMMON-SKILLS-LICENSE.txt).

| Adopted skill | Source path | Adaptation / dependency resolution |
|---|---|---|
| write-product-spec | .agents/skills/write-product-spec/SKILL.md | Numbered observable behavior and companion technical design retained. Project paths, templates and metadata take precedence; one question at a time; shared work-record policy; unavailable tool and implementation-skill references removed. |
| write-tech-spec | .agents/skills/write-tech-spec/SKILL.md | Repository research, commit-pinned references, design tradeoffs and validation mapped to behavior retained. Project conventions and existing authority take precedence; automatic prototyping and Warp subagent planning removed. Depends on write-product-spec and plan-sessions. |

These are locally controlled adaptations, not synchronized upstream mirrors. Review future changes against the pinned source. Installer updates distribute this repository's content, never upstream downloads.

## Matt Pocock and original workbench skills

Source: https://github.com/mattpocock/skills.
Inspected revision: `6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`, 2026-10-02.
License: [MIT, copyright 2026 Matt Pocock](MATT-POCOCK-LICENSE.txt).

| Adopted skill | Source paths | Adaptation / dependency resolution |
|---|---|---|
| grilling | skills/productivity/grilling/SKILL.md; skills/productivity/grill-me/SKILL.md | One question per turn; bounded decision; repository investigation. Upstream grill-me calls a harness-specific Skill tool to load grilling. One portable skill replaces both; no delegation or tool dependency. |
| wait-what | skills/productivity/wait-what/SKILL.md | Context reset and simplified language retained; no unsupported invocation metadata. CONTEXT.md and CONTEXT-MAP.md are optional project inputs. |
| handoff | skills/productivity/handoff/SKILL.md | Existing work owner, evidence and next prompt replace always writing a temporary document. Harness-specific Skill calls removed. Depends on plan-sessions prompt requirements and shared references. |
| plan-sessions | Original work in agent-workbench | Shared model and work-record references; no external runtime dependency. |

These are locally controlled adaptations, not synchronized upstream mirrors. Review upstream changes as diffs against the pinned source; update this revision and license only after deliberately incorporating them. Installer updates use this repository's content, never upstream downloads.
