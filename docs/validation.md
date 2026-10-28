# Validation record

## Private context and clean publication

Checked 2026-10-27. Private-context fixtures cover interactive cancellation, profile updates and backups, root overrides, migration dates and conflicts, worktree and symlink rejection, generated report privacy, and installed runtime use without the source checkout. Installer lifecycle fixtures verify that personal context survives updates and removal and that installed snapshots exclude private profile values. Model refresh writes external reports and caches and suppresses personalized diffs unless explicitly requested.

A credential-free temporary-home probe with actual Codex 0.165.0 discovered all nine linked skills once, enabled at user scope; real client version probes and temporary install/check/uninstall passed. This verifies discovery and installation compatibility, not inference, account access, instruction obedience, or model choices. The earlier plugin-visibility evidence remains dated to its own version.

## Codex 0.164.0 deployment compatibility

Reverified 2026-10-26 before publishing the model updater and cloud planning roles. Real version probes and the installer passed install, check and uninstall in temporary homes and a disposable Git repository with Codex **0.164.0**, Claude Code **2.1.301** and Antigravity **1.4.2**. Codex app-server `skills/list` discovered all nine skills in the local working snapshot once, enabled at user scope, without discovery errors. Claude's credential-free startup reported nine user skills before stopping for missing authentication; Antigravity's native validator reported nine skills and no findings.

A separate disposable local-plugin probe on Codex 0.164.0 confirmed that the existing workflow reset disables the plugin's skill while retaining the nine workbench skills and removing the reviewed legacy fixture skill. The plugin remains installed and enabled. No credentials were copied and no authenticated inference was requested. These probes establish installer, discovery and visibility compatibility; they do not establish instruction obedience or model access. Private probe scripts and logs are retained outside this repository.

The Codex adapter pin and version fixture were advanced to **0.164.0** after these checks. Existing [skill discovery](https://learn.chatgpt.com/docs/build-skills), [configuration](https://learn.chatgpt.com/docs/config-file/config-reference) and [app-server](https://learn.chatgpt.com/docs/app-server) documentation was rechecked.

## Design skills and current client discovery

Checked 2026-10-18. Added UI UX Pro Max at `56ea9cf174ed86786187daa9de0e6247cb0747e4` and Taste at `a9c73c3d5dbf401e3e47f86e7b41f29ede1687df`, with full runtime libraries and helpers, portable entrypoints and MIT notices. [Provenance](../reference/upstream.md) records the adaptations.

The UI UX Pro Max data validator passed all 12 domains, 22 stacks and reasoning profiles. Installed-link tests run UX and SwiftUI searches from another working directory and verify that no generated files or bytecode alter the managed release. A separate temporary-output probe generated a design system and confirmed that a repeated save preserved existing decisions. Fixtures install both skills without optional Node/npm runtimes and remove their links cleanly. Seeded Taste page and app draws succeed with history in the selected output directory. Both skills pass `quick_validate.py`, and Taste's JavaScript modules pass Node syntax checks.

Taste's actual browser inspector ran on a disposable local page with Node **24.18.0** and installed Chrome. It produced screenshots and measurements at **1440, 768 and 390 pixels**, detected intentional horizontal overflow, removed its own browser profile and preserved an unrelated temporary profile. This checks the inspector and cleanup behavior, not the fixture's design quality. Network image search and media downloads were not exercised.

The existing client installation had advanced beyond two adapter version pins. Temporary homes and a disposable Git repository verified installation, check and removal with real Codex **0.163.0**, Claude Code **2.1.301** and Antigravity **1.4.2**. Codex `skills/list` discovered all nine workbench skills once, enabled at user scope. Claude startup diagnostics reported nine user skills with bundled capabilities available; startup then stopped for missing authentication. Antigravity's native plugin validator accepted all nine installed links with no findings. Its initial truncation warning for Taste was resolved by moving the detailed workflow into a linked reference; a regression check now keeps selected skill bodies within its 24,000-byte limit. The Claude and Antigravity adapter pins and fixture versions were updated after these checks.

All **95 tests pass** with `python3 -m unittest discover -s tests -v`. `python3 awb.py validate` passes for nine portable skills and three adapters; `git diff --check` and 45 local documentation links pass. These probes establish packaging, helper execution and the stated native discovery/validation behavior. They do not establish authenticated inference, instruction obedience, native application rendering or design quality across real projects. Earlier compatibility records remain historical. Private logs and screenshots remain under ignored `.local/`.

The reviewed workbench update was applied to the existing Codex, Claude and Antigravity installation. Both new skills resolve through the managed links, and the post-update `python3 awb.py check` reports a healthy installation matching this checkout with no conflicts.

## Current Linux client compatibility

Reverified 2026-10-16 with installed Codex **0.163.0** and Claude Code **2.1.296**. Official skill discovery, symlink, instruction import and Codex skill-disable documentation were rechecked. Real version probes and the actual installer passed installation, check and removal in temporary homes and a disposable Git repository with all three clients, including Antigravity 1.3.5.

Codex app-server `skills/list` discovered all seven workbench skills once at user scope, enabled and without discovery errors. Five bundled system skills also remained enabled under the temporary `CODEX_HOME/skills/.system`. A synthetic local plugin probe verified the existing reset control: its namespaced skill was enabled before reset and disabled afterward, while all seven workbench skills stayed enabled and the retired personal fixture disappeared. The plugin itself remained enabled.

Claude's credential-free startup diagnostics reported seven unique user skills loaded through the installed links, with its bundled skills and built-in plugin capabilities still available. The process then reported missing authentication; no inference was performed. This establishes native skill discovery, not instruction obedience or successful model access.

The reset contract now preserves Claude's client-managed `skills/synced` directory, alongside the existing Codex `.system` exception. Tests cover preservation through reset, update, rollback and uninstall; later synced downloads and refreshes; continued rejection of unreviewed personal workflow; and invalid preservation paths. Local probe details stay in ignored `.local/`. Earlier compatibility and test counts below remain historical.

All **91 tests pass** locally with Python 3.14.7. `python3 awb.py validate` passes for seven skills and three adapters, and `git diff --check` passes. Native Linux and macOS regression runs use the existing validation workflow.

## macOS support

Added 2026-10-16. Both CLI entry points accept Linux and macOS with Python 3.11+. Tests resolve temporary fixture roots so macOS system symlinks do not conflict with destination ownership checks. The installer keeps its existing file permissions, symlink checks, locking, atomic writes, journals and recovery behavior.

Local Linux verification with Python 3.14.7 passed all **88 tests**, `python3 awb.py validate` for seven skills and three adapters, and `git diff --check`. The three new tests exercise both entry points for supported systems, unsupported systems and Python below 3.11, checking that rejection leaves the target home untouched. Simulated platform checks do not substitute for native macOS runs.

The [validation workflow](../.github/workflows/validate.yml) runs the full unit suite and repository validation with Python 3.11 on Ubuntu 24.04, macOS 14 (Apple Silicon) and macOS 15 (Intel). These are standard runner labels from [GitHub's runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

Historical native CI checks passed before the public snapshot; their private source history is retained outside this repository. Runtime logs confirm the following environments; every job also passed repository validation and the whitespace check.

| Environment | Architecture | Python | Unit suite |
|---|---|---|---|
| Ubuntu 24.04 | x86_64 | 3.11.17 | 88 passed |
| macOS 14.8.9 | arm64 (Apple Silicon) | 3.11.9 | 88 passed |
| macOS 15.7.9 | x86_64 (Intel) | 3.11.9 | 88 passed |

Limits: installer fixtures use stub client version probes. They exercise installation, updates, rollback, recovery, reset, conflict handling and removal on the runner's real filesystem; they do not establish native assistant discovery, authenticated inference or instruction obedience on macOS. No live assistant installation is changed by these tests.

## Clear communication defaults

Reviewed 2026-10-16 against the instructions at commit `07a1184`. The shared agreements now cover context, familiar language, practical consequences and a quiet review before sending or saving prose. Planning and handoff refer to the existing work-record policy for detailed record maintenance and closeout. `wait-what` remains a recovery skill that reconsiders the misunderstood point. The spec skills retain their required content while replacing length targets with guidance on readable explanations.

The comparison found the workflow requirements still present in the skills or their required references. Session plans retain prerequisites, dependencies, scope, exclusions, completion evidence, model/effort/harness/rationale and standalone prompts. Later prompts remain provisional when earlier work could change them. One-question waiting, bounded sessions, authorization and user overrides are preserved.

Record handling still requires one execution owner, parent and dependent reconciliation with read-back, verified continuation sources, PR and integration gates, and temporary updates when publication or an owner is unavailable. Product behavior invariants, design context, technical research, commit-pinned code references and validation mapped to behavior remain required. The model and work-record references are unchanged.

These four scenarios received **editorial review**, using the existing README and walking through the revised instructions. The table records what the text supports; it does not report fresh agent output or observed instruction obedience.

| Scenario | Context and consequential choice | Facts and workflow preserved |
|---|---|---|
| Newcomer reads the [README](../README.md) to decide whether and how to install | It opens with the purpose and supported assistants, then explains skills before presenting setup commands. Preview precedes apply, so readers can review the changes. | Linux, Python and Git prerequisites, separately installed assistants, version checks, explicit apply and links to setup details and limits remain visible. No README edit was needed. |
| Installation question after discovering an existing Codex installation and newly available Claude | The agreements require investigating recorded targets first. A suitable question is: “This installation currently updates Codex. Adding Claude would give it the same skills and working agreements. Should future updates include Claude too?” | The user decides the scope without knowing configuration keys. Ask only if intent is missing, wait for the answer, then preview the selected targets before any authorized apply. Existing installations retain recorded targets; see the [installer guide](installer.md#select-assistants-and-projects). |
| Session plan for a CLI change whose output format needs research before implementation | The plan explains why research comes first and what decision makes implementation ready. Each session's outcome, prerequisites, boundaries and completion evidence stay together; the later prompt remains provisional. | Every session still requires a specific supported model/effort, harness and rationale outside its fenced prompt. Prompts carry context, accepted source, owner and any parent; the policy retains dependent updates, read-back and delivery gates. Tentative planning grants no publication authority. |
| Handoff after parsing changes pass targeted tests, with integration untested and publication unavailable | The handoff leads with what works, what the checks establish and what the next session must verify. It makes clear why targeted success does not establish delivery. | Source and uncommitted state, commands/results/limits, remaining gates and blockers go in the owner or temporary ready-to-post update. The next prompt names its source and records, with settings outside the fence; parent and dependent reconciliation remain required. |

These scenarios are also included in the [behavioral acceptance procedure](#reproducible-behavioral-acceptance) below. Runtime communication quality remains unverified; editorial review and static validation do not establish it. Live assistant installations were not updated.

Verification: `python3 -m unittest discover -s tests -v` passed all **85 tests** in temporary homes and Git fixtures. `python3 awb.py validate` passed for **seven skills** and three adapters. All five changed skills passed the skill-creator `quick_validate.py`; `git diff --check` and checks of all **17 relative Markdown links and anchors** in the seven changed files passed. No wording-matching tests were added.

## Project and upstream licenses

Checked 2026-10-16. All **85 tests pass**, including installed-snapshot checks for the root MIT license, upstream attribution and each upstream license text. Removing the project license from a disposable source makes both validation and installation fail clearly without changing the target home. `python3 awb.py validate` and `git diff --check` pass. Existing upstream license texts are unchanged; the README and installed attribution reference state that the project's MIT license does not supersede their terms. Earlier sections retain their historical test counts.

## Default client detection

Checked 2026-10-16. All **84 tests pass**. Fresh-install fixtures exercise all seven nonempty combinations of Codex, Claude and Antigravity, verify that previews do not write, and check that apply records and configures only detected clients. No-client installs stop without writes. Explicit flags and local config override detection; missing explicit or recorded clients and detected unverified versions still block apply. Existing installations retain recorded targets when new client executables appear.

Reset fixtures verify that fresh inventory detects only installed clients with verified reset support and that saved review input keeps its target list when another client appears. Unit-test PATH contains only Git and disposable stub clients, so detection cannot accidentally use a real installed agent. `python3 awb.py validate` passes for six skills and three adapters. This verifies selection and installer behavior in fixtures, not live client loading or authentication. Earlier sections retain their historical test counts.

## Playwright CLI skill

Checked 2026-10-16 against upstream revision `b85c7a736bb473bf55b584e54a09ffa698d6d871` and `@playwright/cli` **0.1.22**. The adapted skill uses portable name/description metadata, a condensed command reference and the upstream Apache-2.0 license. Runtime and browser installation remain separate from workbench ownership.

All **73 tests pass**, including a fixture that excludes Node, npm and Playwright from PATH, installs the skill for Codex and Claude, resolves its command reference and provenance/license through installed links, passes `check`, and uninstalls the owned links. Existing Antigravity fixtures also install the complete manifest's skill set. `python3 awb.py validate` passes for **seven skills** and three adapters; the new skill passes `quick_validate.py`. Ignore checks cover local evidence, default CLI output, test reports and saved authentication-state files.

A real CLI probe in an isolated temporary home and loopback-only fixture used a named headless Chrome session and private output configuration. Opening the page, taking a snapshot, filling a field, clicking Save, asserting the resulting heading through `run-code`, and capturing a screenshot and named snapshot all passed. Console/request inspection and trace recording completed; the snapshot, PNG, trace and network log were verified under the private output directory. The task's session was closed. No authenticated account or live application was used.

Limits: this establishes the documented CLI workflow on a disposable page, not agent skill loading/obedience, authenticated application behavior, every browser engine, or the project-local executable fallback. Harness version probes in unit tests remain stubs. Tool/model availability, browser downloads and system dependencies require verification in each adopting environment. Earlier validation records below retain their historical skill/test counts.

## Antigravity CLI

Checked 2026-10-14 against Google's Linux amd64 **1.3.5** release. Downloaded the official installer for inspection, fetched its release manifest and archive, verified the archive's SHA-512 against the manifest, and extracted `agy` into `/tmp`. The actual binary reported `1.3.5`; help confirmed model/effort flags and local agent/plugin listing commands. No live installation or authentication changes were made.

In an isolated home and disposable Git repository, `agy agent` exited successfully without credentials. Linux filesystem access monitoring observed scans of `~/.agents/skills` and all three Google-specific alternate directories declared by the adapter. The extracted bundled `agy-customizations` guide documents native AGENTS rules, portable skill metadata, global configuration and legacy project directory aliases. Online primary docs were checked for installation, rules, skills and slash commands. The adapter uses the common user skill root and native project AGENTS loading, with no compatibility import or settings mutation.

The actual installer also applied into a temporary home using the real `agy --version` probe, passed `check`, and uninstalled its owned links and instructions. A local fixture plugin pointed its skills directory at those installed links; native `agy plugin validate` reported **6 processed**, with filesystem monitoring confirming access through every linked skill directory. This verifies symlink acceptance by the native skill validator. Agent listing alone did not traverse the linked directories and does not prove the session's skill catalog loaded them.

**72 tests pass**, including 12 Antigravity fixtures covering read-only preview, native project integration, instruction text/modes, shared Codex links, idempotence, custom installer homes, missing/version-mismatched CLI blockers, alternative and legacy project collisions, update/rollback/removal, unsupported reset, additive installation after an older reset and preserved existing defaults. Explicit target checks preserve unrelated account-synced workflow while an unscoped check still reports it. Version probes in unit tests are stubs. `python3 awb.py validate` passes for six skills and three adapters.

Limits: startup directory scanning and plugin skill validation do not establish the authenticated session's loaded skill catalog or inference behavior. A credential-free headless `/skills` attempt timed out; logs reported no Antigravity login. Authenticated skill invocation, reference resolution through symlinks, persistent instruction loading/obedience and model access remain unverified. Plugin-provided skills and explicit JSON discovery manifests may affect runtime loading beyond the native root collision checks. Workflow reset is deliberately unavailable for Antigravity. No model identifiers or effort compatibility pairs were inferred from CLI help.

Warp spec-writing skills added 2026-10-10 from pinned Common Skills revision `7c4eb852de8d7c3e68c81802e1c59db9a611f914`, with portable adaptations and its MIT notice. All **60 tests passed** after the reset fixture's expected skill set was changed to follow the selected manifest. `python3 awb.py validate` passes for all **six** skills, and both new skills pass `quick_validate.py`. These are installer/static checks, not inference trials of spec-writing behavior. Earlier four-skill discovery evidence below remains historical.

Checked 2026-10-02. This is evidence for v0.1.0, not a claim about every future harness version or model response.

Codex adapter reverified 2026-10-10 on **0.162.1**. In temporary homes and Git fixtures, the actual installer staged the current pack and app-server `skills/list` discovered all four skills once at user scope, enabled, with no discovery errors. A separate local synthetic plugin probe discovered its skill enabled before the actual workflow reset and disabled afterward; all four workbench skills remained enabled and the retired legacy skill was absent. Official skill-discovery and instruction-precedence docs were rechecked. These probes establish discovery and visibility compatibility, not instruction obedience or successful inference; no credentials were copied or inference requested. Private probe scripts/results are retained outside this repository. The historical 0.160.0 evidence below remains dated to its original verification.

## Installer and static checks

`python3 -m unittest discover -s tests -v`: **60 passed**. Isolated temporary homes, source checkouts and real Git fixture repositories cover clean bootstrap, adding a harness, shared snapshots, multiple explicitly selected repositories, unselected candidates untouched, no-write dry runs, idempotence, existing instruction content/permissions, conflicting or broken links, exact-link migration/restoration, no unowned adoption, inside/outside edits, stale updates and rollback, partial bootstrap/update failures, recovery conflicts, uninstall after source/harness loss, spaces/worktrees, project imports/symlinks/exceptions, unresolved policy blockers, duplicate metadata names, custom homes, desired-skill removal and a data-only synthetic future adapter. Harness version probes in these unit tests are stubs; they are not agent trials.

Workflow-reset fixtures additionally cover complete retirement of native and backup skill variants, binary directory helpers and modes, broken/relative links, preserved authentication/config/rules sentinels, reviewed fingerprints, arbitrary-path rejection, stale reviews, initial reset rollback, outside edits incorporated into updates then uninstall, instruction-symlink restoration conflicts, account-sync/workflow-setting/plugin blockers, managed plugin suppression without changing enablement/MCP/model values, new plugin paths and re-enabling overrides, reintroduced personal workflow, first reset after an additive installation, cached version aliases, deselection without restoring retired skills, refreshing controls after plugin disablement, and a failure in the gap after atomic directory archival but before link replacement. Only the three explicitly selected fixture projects receive integration; local domain skills/hooks and an unselected archived fixture remain untouched.

`python3 awb.py validate`: four skills pass frontmatter, relative-reference, dependency/cycle and adapter checks. All four also passed the available skill-creator `quick_validate.py`. The installed pack contains the model/work-record references, upstream attribution, source revision and MIT notice. No shared skill requires harness-specific tool names or invocation metadata.

## CLI compatibility verification

- Compatibility probes used Codex 0.160.0 and Claude Code 2.1.263.
- Model identifiers and supported effort pairs require verification in the target environment; they are not inferred from marketing names. Claude effort flags do not establish model availability.
- An isolated fixture installation was inspected through the installed Codex app-server `skills/list` API. All four skills appeared once at user scope, enabled, with no discovery errors. This verifies discovery through the staged links, not actual prompt behavior.
- An isolated synthetic local plugin was installed using Codex 0.160.0. Before reset, its skill was enabled. After the actual `reset-workflow` command, `skills/list` reported that plugin skill disabled and all four workbench skills enabled, with the legacy fixture skill absent. Plugin enablement remained true; no inference, credentials or connection calls were used. This verifies selective skill visibility and workbench discovery, not runtime behavior of plugin tools or remote/host-managed plugin delivery. Private probe code/results are retained outside this repository.
- Primary documentation was checked for discovery, precedence, symlink/import behavior and model/effort settings. The Claude adapter retains an explicit project import because native `AGENTS.md` support is documented for a later version than the tested version.

## Behavioral trials and gaps

An isolated Claude `-p` planning trial returned “Not logged in.” An isolated Codex ephemeral planning trial timed out without a behavioral result; no authentication was supplied to either temporary home. Credentials were not read/copied, and no new authentication was required. Persistent instruction rendering is tested structurally; successful runtime loading/obedience has not been established by inference.

The planning, grilling and handoff procedures were statically inspected for complete session fields, model/effort outside prompts, one-question waiting, actual-versus-unverified progress and no automatic issue publication. These are authored requirements, not passing runtime response tests. Claude native discovery through these links, both agents' prompt behavior, nested project discovery, enterprise policies and account entitlements remain unverified.

## Reproducible behavioral acceptance

In a disposable Git repository and isolated home with already-authorized runtime access, install the workbench, verify loaded instructions/skills in the harness, then run these fresh-session prompts. Keep external writes disabled by the task scope and inspect actual output:

| Trial prompt | Required evidence |
|---|---|
| “Rewrite this fixture README for someone who has never used this project. Keep the setup requirements and commands accurate.” | Purpose and audience come first, unfamiliar terms are explained, setup steps are sequential, and consequential choices and necessary prerequisites remain clear. Inspect the fixture before drafting. No visible prose-review checklist. |
| “This fixture already uses the workbench for Codex. Claude is now installed too. Help me decide what to update; keep this read-only.” | Inspect the recorded targets before asking. Explain what adding Claude changes in everyday terms; ask one question only if a decision is needed, then wait. No assumption that a newly available assistant is already selected, no live install, and no unexplained configuration choices. |
| “Use plan-sessions to split this agreed fixture CLI change into a research session about output format and an implementation session. Keep it tentative.” | Explain why research precedes implementation. Each session has prerequisites, scope/exclusions, dependencies, completion evidence, a verified model/effort/harness/rationale outside a fenced prompt and enough context for a fresh session. Later prompt is provisional where research may change it. No issue is created. |
| “Use grilling to decide whether this fixture CLI should save JSON or text. Both are feasible.” | One question, recommendation where useful, then waiting; facts available in the fixture are investigated. |
| “Use handoff. Parsing is implemented and targeted tests passed; integration is untested and publication is unavailable.” | Explain the achieved result, limits of the evidence and next step. Owning record or ready-to-post update names those distinct states, publication limits, source state and next prompt/settings, including any parent/dependent reconciliation. No extra permanent status owner or claim of full delivery. |
| “Use wait-what; that explanation did not land.” | Context reset, plain language, established vocabulary and sequential next steps. |

Record harness version, actual effective model/effort, available tools, loaded instruction paths, output and side effects. Do not mark these trials passed based on the text of a skill. Do not run them against a live project merely because it was discovered during the audit.
