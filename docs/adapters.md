# Agent adapter contract

Shared content uses only portable `name` and `description` frontmatter, Markdown and relative references. No shared skill requires a particular question, issue, shell or skill-invocation tool. Tool names and invocation syntax belong in adapter documentation, not skills.

An adapter is a JSON file in `adapters/`, selected by `workbench.json`:

| Field | Meaning |
|---|---|
| `schema` | Currently 1 |
| `executable`, `verified_version` | Read-only `--version` probe and exact verified version |
| `home_directory`, `home_environment` | Default harness home relative to user home; supported environment override, or null when none is verified |
| `instruction_file` | Persistent global instruction file relative to harness home |
| `skill_scope`, `skill_directory` | `user` or `harness` root plus native relative skill path |
| `alternate_skill_directory` | Optional additional native location relative to harness home, checked for competing names |
| `additional_skill_directories` | Optional list of further native locations relative to harness home, checked for competing names |
| `shadow_files`, `project_shadow_files` | Files that may prevent default instruction loading |
| `project_skill_directories` | Native paths checked for duplicate personal skill names in a selected project root |
| `project_bridge` | Optional project compatibility file containing `@AGENTS.md`; null when native AGENTS loading suffices |
| `setup_url` | Official setup instructions for missing executable |

All adapter paths must be relative, contained paths. Core installation operates on files, links and managed sections. The current bridge primitive is a Markdown import; a future harness with a different mechanism may need a new primitive, without changing shared skills or transaction semantics. Do not pretend an unsupported import works. `--harness NAME` and `--harness-home NAME=PATH` accept manifest-selected future adapters without new hard-coded CLI switches.

The manifest's `harnesses` lists available adapters. On a fresh install, the core detects each adapter's `executable` on PATH and selects only installed clients. Optional `default_harnesses` restricts the detection candidates; when omitted, all available adapters are candidates. Explicit CLI/config selection and recorded installation targets take precedence. Detection does not imply version compatibility: the selected adapters' normal version probes still gate apply. No detected candidates is a clear error without writes.

Fresh reset inventory uses the same detection rule but only considers adapters declaring `workflow_reset`. Explicit and recorded selections are not silently filtered by capability or presence; unsupported reset targets and missing executables remain errors at their existing validation gates. A reviewed inventory records its client selection.

## Verified implementations

The installer supports Linux and macOS with the same adapter paths. The native client discovery probes below were run on Linux; macOS installer tests use stub client version probes and do not establish native client loading or instruction obedience. See [macOS evidence](validation.md#macos-support).

Codex 0.165.0 (reverified 2026-10-27): user skills are linked once through `~/.agents/skills`; no duplicate links are installed in `~/.codex/skills`. Bundled system skills remain enabled under `CODEX_HOME/skills/.system` (default `~/.codex/skills/.system`). Global agreements render into `CODEX_HOME/AGENTS.md` (default `~/.codex/AGENTS.md`). Overrides are flagged because they can shadow the chosen instruction file. Project `AGENTS.md` is native. Isolated app-server discovery and plugin skill visibility probes passed; see [validation evidence and limits](validation.md#current-linux-client-compatibility). Sources: [skill discovery and symlinks](https://learn.chatgpt.com/docs/build-skills), [instruction precedence](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

Claude Code 2.1.296 (reverified 2026-10-16): personal skills use its own `skills/` directory, default `~/.claude/skills`; `CLAUDE_CONFIG_DIR` changes that home. Global agreements render into its `CLAUDE.md`. The project `CLAUDE.md` import of `@AGENTS.md` remains compatible with native AGENTS loading and preserves existing local content. Bundled skills and commands remain enabled, and `skills/synced` is preserved as a client-managed directory through reset and health checks. Credential-free startup diagnostics discovered all seven installed skills through their links; inference and instruction obedience remain unverified. Sources: [skills and account sync](https://code.claude.com/docs/en/skills), [memory and imports](https://code.claude.com/docs/en/memory), [config location](https://code.claude.com/docs/en/settings).

Google Antigravity CLI 1.3.5 (checked 2026-10-14): executable `agy`; agreements render into `~/.gemini/AGENTS.md`; project `AGENTS.md` is native. Skills share Codex's `~/.agents/skills` links. An isolated native startup probe scanned that directory and the Google discovery locations `~/.gemini/config/skills`, `~/.gemini/skills` and `~/.gemini/antigravity-cli/skills`; the adapter checks these alternatives for competing names. Project checks include `.agents`, `.agent`, `_agents` and `_agent` skill directories. No home environment override is assumed. `--harness-home antigravity=PATH` relocates installer destinations, not the CLI's runtime configuration. Workflow reset is unavailable until plugin visibility and configuration discovery have a verified contract.

Sources: [installation](https://antigravity.google/docs/cli/install/), [rules and native AGENTS loading](https://antigravity.google/docs/rules/), [skills](https://antigravity.google/docs/skills/), and the 1.3.5 binary's bundled `agy-customizations` guide. The online CLI skill table lists `antigravity-cli/skills`, while the bundled guide describes shared `config/skills`; local probes established that startup also scans the common `.agents/skills` root. This establishes directory discovery, not authenticated loading of every skill or instruction obedience. See [exact evidence and gaps](validation.md#antigravity-cli).

Canonical references and license text accompany the installed content pack. Resolve references relative to the canonical target of the discovered skill path; all native skills point to that same pack. This relative layout is validated and Codex discovery was exercised. No agent-specific metadata or forced model/effort is embedded in shared skills.

## Add another harness

Workflow reset is an optional adapter capability. `workflow_reset` declares bounded harness/user workflow paths, built-in directory exceptions, settings metadata, workflow-bearing keys and additional settings sources. A future adapter without this contract can install normally but cannot reset. Discovery emits review fingerprints; it never authorizes retirement. Core reset logic uses these declarations rather than agent-specific directory assumptions.

The workbench is additive to client-provided defaults. Declare bundled skill folders in `builtin_skill_directories` and other retained client-managed folders in the optional `preserved_skill_directories`. Each entry must be a single directory name. These folders are excluded from retirement and remain outside workbench ownership; clients can refresh them without failing health checks. Claude declares `synced` separately because account-synced content can include both vendor-provided and user-selected skills. Verify the client's bundled skills and commands remain available before updating its adapter version.

Reset state records the harnesses covered by that reset. Adding another harness ordinarily does not grant retirement authority over its configuration or extend reset health checks to it. Older reset state derives its coverage from the previously installed harnesses before an additive install expands that list.

The Codex contract also declares its plugin cache and verified TOML skill-control template. The core inventories cached plugin manifests, fingerprints skill paths and manages only the added control section. Missing manifests or unsupported formats block. Claude has no verified selective plugin control, so enabled plugins block its reset. Adapter version verification must cover both discovery and any declared visibility control.

1. Verify an installed version and primary docs: skill discovery, symlinks, metadata, persistent instructions, precedence, imports, effort control and runtime tool boundaries.
2. Add adapter data and a manifest entry. Use native global discovery if supported; do not duplicate personal workflow into projects unnecessarily.
3. Populate model capability/access evidence in the shared reference, keeping preference separate.
4. Exercise isolated bootstrap, adding the harness, conflicts, discovery and removal. Run representative prompts only when existing access permits; record behavioral limits separately.
5. Revalidate before changing `verified_version`. Exact version gating deliberately avoids extrapolating current docs to old CLIs or claiming unknown newer compatibility.

Pi is not implemented. Autonomous orchestrators are outside this contract.
