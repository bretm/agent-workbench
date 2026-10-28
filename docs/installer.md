# Installer guide

The workbench adds its skills and agreements alongside each client's built-in capabilities. It preserves bundled skills, commands and their configuration, including Codex's system skills and Claude's account-synced skills. An optional workflow reset retires reviewed personal customizations while retaining those client-managed defaults.

## macOS setup

The same workbench commands work on Linux and macOS, including Intel and Apple Silicon Macs. Check that your shell finds Python 3.11+ and Git:

```sh
python3 --version
git --version
```

If needed, install a current Python from [python.org](https://www.python.org/downloads/macos/) and Git through [Apple's Command Line Tools](https://developer.apple.com/xcode/resources/). Install your coding assistants separately and make their CLI commands available on PATH before previewing workbench installation.

Assistant configuration paths follow the same adapter defaults on both systems. Workbench state and backups remain in `~/.local/state/agent-workbench`; `--state-dir` can override that location. See the [validation record](validation.md#macos-support) for native test evidence and client-loading limits.

## Commands

Run commands from the workbench checkout. Commands that change files show a read-only preview by default. Add `--apply` after reviewing the preview, or use `--interactive` to review and confirm in one command. `--dry-run` explicitly requests a preview; `--diff` includes planned file changes.

```sh
python3 awb.py validate             # validate this checkout
python3 awb.py install              # preview installation
python3 awb.py install --apply
python3 awb.py check                # check the installed files and versions
python3 awb.py update               # preview changes from this checkout
python3 awb.py update --apply
python3 awb.py rollback             # preview undoing the latest transaction
python3 awb.py rollback --apply
python3 awb.py uninstall            # preview removing all owned changes
python3 awb.py uninstall --apply
python3 awb.py recover              # preview recovery after an interrupted change
python3 awb.py recover --apply
```

Use `python3 awb.py --help` or `python3 awb.py install --help` for options. Exit codes are **0** for a successful preview/apply or healthy check, **1** for an absent or stale installation, **2** for a conflict, unsupported prerequisite or usage error, and **3** for I/O or malformed data errors.

## Select assistants and projects

On a fresh install, detection looks for `codex`, `claude` and `agy` on PATH. You can choose explicitly with `--harness`, repeated for each assistant. Install and authenticate assistants separately using [Codex setup](https://learn.chatgpt.com/docs/codex/cli), [Claude Code setup](https://code.claude.com/docs/en/setup) or [Antigravity CLI setup](https://antigravity.google/docs/cli/install/). The installer does not install agents or change authentication.

```sh
python3 awb.py install --harness claude
python3 awb.py install --harness antigravity
python3 awb.py discover
python3 awb.py install --harness codex --harness claude \
  --repo "$HOME/git/Project One" --repo "$HOME/git/Project Two"
```

These commands only preview or inspect. Add `--apply` to the chosen install command after review. Discovery only suggests candidates. Select Git roots or linked worktree roots explicitly; selecting a worktree does not also select its main checkout.

Antigravity uses `agy --version`, shares `~/.agents/skills` with Codex, and receives working agreements in `~/.gemini/AGENTS.md`. Project `AGENTS.md` loads natively. Claude receives an `@AGENTS.md` compatibility import where needed. Project integration adds a pointer to local project facts; existing project instructions are preserved.

Updates keep the recorded assistants and projects. Add new targets explicitly. Removing a target from configuration does not uninstall it; removal currently applies to the full installation.

## Private personal context

Run `python3 awb.py context setup` to save personal facts and preferences outside repositories. The default is `~/.agents/agent-workbench/`; `--context-dir` or `AWB_CONTEXT_DIR` selects another location. Installation records that root and places its pointer and bundled helper command in supported clients’ instructions. Updates retain the recorded root unless overridden; explicit flags, then the environment, take precedence. Context is user-owned and survives update, rollback, and uninstall. See [private context](../reference/private-context.md) and [model guidance](model-guidance.md).

## Local configuration

Keep project facts and exceptions in a local, uncommitted JSON file:

```json
{
  "harnesses": ["codex", "claude"],
  "repositories": [{
    "path": "/path/to/Project One",
    "facts": {
      "documentation": ["docs/architecture.md"],
      "tracker": "GitHub: owner/project",
      "build": ["make build"],
      "test": ["make test"],
      "exceptions": ["Keep the existing offline work record authoritative until tracker adoption."]
    }
  }]
}
```

Use `python3 awb.py install --config /path/to/local.json`, then the same command with `--apply`. `--repo` overrides the configured repository selection. A repository object's `policy_conflicts` list records unresolved conflicts; a nonempty list blocks the whole apply. Resolve those conflicts before removing the blocker. Installation does not rewrite existing project policies.

`--home`, `--state-dir`, `--codex-home`, `--claude-home` and `--harness-home NAME=PATH` support temporary test installations and local path overrides. Agent configuration directories otherwise follow supported environment variables and are recorded for later checks. Use real directory paths; symlinked destination parents are rejected.

On macOS, paths under `/tmp` and `/var` can pass through system symlinks. Use the real path for state and assistant-home overrides, such as `/private/tmp/workbench-state` instead of `/tmp/workbench-state`. The selected user-home root and project roots are resolved automatically; links inside a destination path still require an explicit real path.

`--harness-home antigravity=PATH` overrides the installer destination corresponding to `~/.gemini`; it does not tell Antigravity to use that destination. No Antigravity home environment variable is assumed. User-scoped skills still use the selected `--home`.

## Optional browser tools

The Playwright CLI skill is included, but Node, Playwright and browsers are installed separately. Their absence does not block workbench installation or checks. The adapted skill targets `@playwright/cli` 0.1.22:

```sh
npm install -g @playwright/cli@0.1.22
playwright-cli --version
playwright-cli --help
```

Use Node.js 20 or newer as the documented setup baseline. The pinned package declares Node >=18; the upstream setup documentation used during integration requires >=20. Check browser compatibility and system dependencies for your environment. The CLI may download a missing browser on first use. See [official setup](https://playwright.dev/agent-cli/installation) and [pinned provenance](../reference/upstream.md#playwright-cli).

If a project already has a compatible Playwright installation, check `./node_modules/.bin/playwright --version` and `./node_modules/.bin/playwright cli --help`. When supported, use that local `playwright cli` command instead of installing globally.

Manage the skill with `awb.py install` or `update`. Do not run `playwright-cli install --skills` over workbench-owned links. Existing upstream skill installations need a reviewed [migration](migration.md).

Keep browser output and authentication state in ignored `.local/playwright/` or a temporary directory. This repository also ignores `.playwright/`, `.playwright-cli/`, `playwright-report/`, `test-results/` and `*.auth-state.json`; check equivalent ignore rules in each target project. The installer does not add them to other repositories. Read the [browser skill](../skills/playwright-cli/SKILL.md) for session handling and output configuration.

## Design skills

The manifest includes **ui-ux-pro-max** and **design-taste-frontend** (Taste). Both are pinned, locally controlled adaptations distributed through the normal workbench install/update transaction. Their scripts, data, references, starter assets and license notices travel with the installed snapshot. Do not run upstream skill installers over workbench-owned links. See [provenance and changes](../reference/upstream.md).

UI UX Pro Max provides searchable guidance for web, mobile and desktop interfaces. Its bundled helper needs Python 3 and uses only the standard library; searches run locally without network access. Commands in the skill use the absolute installed skill directory, so they work from any project. Generated design-system documents are optional: read existing project guidance first and supply the target project's output directory explicitly when persisting recommendations.

Taste uses the published skill name `design-taste-frontend`. It includes separate workflows for public websites and web application screens. The full inspector requires Node.js 22+ and an installed Chrome, Edge or Chromium; `CHROME_PATH` can select an existing browser. The source lint helper supports Node 18+. Image search/download needs network access and keeps source credits. The workbench does not install these runtimes, browsers, dependencies or hooks. If unavailable, use the documented fallback and report which checks could not run.

Taste writes task output and draw history under `.taste-skill/` by default. Keep that directory ignored in each target project, or select private output with `--out`; this repository's ignore rules do not propagate to other projects. The browser helper launches a fresh temporary profile and removes only its own process/profile. The pinned upstream package has the shared scene stage but no scene catalogue or individual demos, so drawing a direction does not select scroll scenes.

Choose one visual direction for each surface. Taste can establish and refine that direction, while UI UX Pro Max supplies focused accessibility, interaction and platform guidance. Existing brand decisions and project conventions take precedence over either skill's defaults. Use the project's test suite and the Playwright CLI skill for functional browser verification when appropriate.

## Implementation

The CLI uses Python's standard library. `planner.py` builds desired path/section operations from the manifest and adapter data without writing. `storage.py` handles atomic replacement and managed blocks. `transactions.py` handles durable preimages, locking and recovery. `cli.py` handles targeting, previews and exit codes.

## Ownership

Each installed path has a state entry with its type, expected bytes/link or managed block and original preimage. State records workbench version, source path, Git revision when available, the SHA-256 content-pack hash, installed CLI versions, configurable harness homes and selected repositories. Each snapshot contains the project's MIT license and upstream origin/revision and license notices with its skills. The project license does not supersede upstream terms; the installed attribution reference identifies the applicable third-party licenses. A missing Git revision is explicitly null; the content hash still identifies exactly what was installed.

Regular instruction files receive one delimited section. The installer does not replace unrelated content or adopt an existing section marker. It refuses linked instruction files except for an existing project compatibility link to that project's `AGENTS.md`, which is used without adoption. Existing Claude imports are likewise used without ownership. Other pre-existing files, even byte-identical ones, are conflicts. Exact-link migrations are the only allowed replacement of an unowned path.

Owned section drift blocks updates/removal; outside edits are allowed and preserved, including edits incorporated into a subsequent update. Owned files and links require exact expected content and permissions. Broken links are inspected without following them. Symlinked destination parents are rejected so selecting one target cannot silently write through another. Authentication files, model defaults and permissions configuration remain unchanged. Ordinary installation leaves settings intact; workflow reset adds only verified skill-visibility controls.

Project facts are generated JSON, kept separate from shared behavior. A conflicting pre-existing facts file is not adopted. Project templates/hooks, instruction hierarchy and issue policies remain project-owned. The installer flags native duplicate skill names at global/selected project roots but does not attempt to interpret all prose conflicts.

## Apply and recovery

`reset-workflow` is an explicit exception to ordinary non-adoption: a local review inventory authorizes retiring exactly fingerprinted personal workflow paths. It does not grant arbitrary file replacement or touch project policy. Reset and installation operations on the same path coalesce into one journaled preimage/postimage. Retired regular directories move atomically into state archives; full tree preimages include binary bytes, permissions and literal symlink targets. Cross-filesystem directory retirement is rejected before destination changes. Recovery recognizes the brief absent-path interval between directory archival and replacement. Archives and journals remain private and retained.

Reset instruction files use managed sections with an initial retired preimage. Updates preserve outside edits; removal restores the old prose alongside those edits. If the old instruction was a symlink, later outside edits block restoration rather than being discarded. Plugin visibility uses comment-delimited managed TOML; checks and rollback preserve unrelated setting text. Reset diffs expose only the owned configuration section.

Before applying, all conflicts and prerequisites must be resolved. Every destination is checked against the preview preimage again. Mutations acquire an exclusive nonblocking local lock. A journal stores **all** preimages and postimages before the first destination change; it is also the backup. Journals/state use mode 0600, with a newly created state root mode 0700. Instruction permissions are preserved.

Each file or link replacement uses a temporary sibling and atomic rename; regular writes and containing directories are synced. Rollback, recovery and uninstall use their local journal/state and do not require a healthy canonical content pack or an installed agent. A transaction can still fail between destinations. Its journal stays pending and blocks new installs, updates and uninstall. `recover` previews the inverse and `recover --apply` reverses it, restoring the prior state.

Recovery checks actual preimages/postimages instead of relying on a progress counter. It recognizes both untouched and already-restored operations. If the user changed a path in the meantime, recovery reports conflicts and leaves every destination unchanged until they are resolved. Edits outside managed sections survive rollback. An interrupted rollback uses the same pending journal and recovery path.

`rollback` reverses the newest active transaction. Repeated rollback walks earlier transactions. `uninstall` restores initial preimages for all owned destinations, preserving unrelated and subsequent changes. It never deletes state/backups or created empty directories. Backups may contain private instruction text: keep state local, do not commit or sync it as shared configuration. Resolve drift by comparing journal preimages and current content, preserving the user's edits in canonical/project-owned content before retrying; there is no automatic discard option.

## Scope and limits

v1 installs all skills selected in the version-controlled manifest, including dependency closure. Adding harnesses is additive. Updating a removed desired skill restores its original link/file only when unchanged in an additive installation; after workflow reset it stays retired until deliberate uninstall/rollback; retired competing upstream links remain explicitly owned retirement entries until uninstall/rollback. Old content snapshots remain tracked for drift and recovery. There is no selective uninstall or garbage collection yet; full uninstall or transaction rollback is the explicit removal path.

Use absolute (or `~`) paths in local config to keep targets stable between launch directories; relative paths resolve from the invoking directory. Explicit CLI paths may be relative to the working directory. The installer accepts selected Git/worktree roots without editing Git metadata or issuing Git mutations. It performs no network actions except running installed CLIs' version probes. Repository discovery never feeds installation selection.

Health checks establish local content integrity, prerequisite versions, root discovery conflicts and freshness against the checkout. They do not establish inference access, runtime obedience, managed enterprise policy compatibility or nested-directory behavior for every project. Disabled skills, custom instruction-size limits, plugins and session flags may affect runtime loading; verify the harness's actual loaded context when adopting the setup.

Client selection uses explicit CLI flags, local configuration, recorded installation targets, then fresh-install detection, in that order. Detection checks supported adapter executables on PATH; absent clients are skipped without creating their client-specific configuration. All supported adapters are candidates unless a custom manifest restricts `default_harnesses`. No detected clients is an error without writes. Detected clients still need verified versions, and explicitly selected or recorded missing clients still block apply. Detection is rerun during each fresh preview/apply; review the printed targets before applying.

Adding Antigravity includes it in fresh-install detection when `agy` is present; it does not implicitly add it to an existing installation. Its shared user skill links have the same ownership entries as Codex links. Reset state separately records its covered harnesses, so an ordinary adapter addition does not expand a prior reset's configuration-retirement scope. Fresh reset detection considers only installed adapters with verified reset support. Antigravity currently supports ordinary installation only; explicitly selecting it for reset fails before writes. Saved reset inventories fix their target list for later apply.

Explicit harness selection scopes reset-workflow health checks to those targets. Unselected harnesses' unmanaged workflow does not block adding or checking another harness; an unscoped `check` still reports every installed harness's reset-health conflicts. Owned-content integrity checks always cover all recorded entries.
