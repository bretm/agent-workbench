# Reviewable migration

Keep machine inventories, audit reports and migration previews in ignored `.local/`. This reusable baseline does not authorize changes to any adopting project.

## Existing upstream skills

For a complete clean slate, follow the workflow reset below. The narrower exact-link migration remains available for users who deliberately retain a larger collection; use the reset when replacing an entire personal workflow collection.

The initial workbench has one `grilling` implementation; it replaces the useful probing concept behind upstream `grill-me`/`grilling`. `handoff` is a session boundary skill, not autonomous goal submission. `wait-what` preserves the upstream context reset and vocabulary guidance. Attribution, MIT license and pinned source revision accompany the adaptations. `plan-sessions` is new.

Existing selected-name links conflict, even if they already point to identical content. The upstream `grill-me` alias and `claude-handoff` variant also compete. Preserve them until an exact migration is reviewed. A local migration object names a **specific symlink**, its literal observed target, and an action:

```json
{
  "harnesses": ["codex"],
  "repositories": [],
  "migrations": [
    {"path": "/home/user/.agents/skills/grilling", "action": "replace", "target": "/home/user/upstream/skills/productivity/grilling"},
    {"path": "/home/user/.agents/skills/grill-me", "action": "retire", "target": "/home/user/upstream/skills/productivity/grill-me"}
  ]
}
```

Paths and targets above are illustrative. Use `discover` to inspect actual links. A relative link target must stay literal, not be rewritten as its resolved target. Migration is limited to selected harness skill locations. Wrong targets, ordinary directories/files, arbitrary paths, managed drift and unsolved aliases block all changes. Backup journals let uninstall restore upstream links. Competing variants are not installed alongside personalized replacements.

Other upstream skills may refer to `grilling`, `handoff`, `CONTEXT.md`, harness-specific tools or issue publication conventions. A selective migration must review these callers because replacing a dependency changes behavior. The clean-slate reset retires the whole discovered personal collection, including backup variants, so its callers are not left competing with the baseline. Source checkouts are preserved. Reintroduce additional skills deliberately, with their dependencies and provenance.

## Clean personal workflow

Run `reset-workflow --inventory` to emit a local JSON review input. It records retirement paths, exact symlink/tree/file fingerprints, plugin skill paths, built-in exceptions and blockers. It contains no authentication or operational setting values. Review it and use `reset-workflow --config FILE --dry-run`; the same command with `--apply` is the deliberate migration. No inventory is automatically approved. A new or changed discovered workflow requires refreshed review.

The adapter enumerates personal skill directories, legacy prompts/commands/agents/styles, and persistent personal instruction sources. Reviewed legacy instruction files are retired and replaced with the workbench agreements; the first reset also reviews legacy prose preserved by an earlier additive installation. Later outside user edits remain user-owned. Empty native global files retain their prior permissions. Entire regular skill directories, including binary helpers, are backed up without following symlinks. Journals retain exact prior content and directory modes; real directories move atomically into `STATE/archives/TRANSACTION/`. This requires the archive and original directory to share a filesystem and is validated before destination changes. Backups remain outside discovery and are not garbage-collected.

On Codex 0.160.0, each discovered skill in an enabled cached plugin is disabled through a managed `[[skills.config]]` TOML section. Plugin enablement, model preferences, MCP configuration, approval controls and other text remain intact. Diff output for this section shows only its owned entries, never the surrounding settings. The installed CLI verified disabling an isolated plugin skill while keeping its plugin enabled. [Official OpenAI documentation](https://learn.chatgpt.com/docs/build-skills) describes the path control.

Claude plugin skills are not affected by `skillOverrides`; disabling the plugin also affects its other capabilities. Enabled user-configured Claude plugins therefore block this workflow-only reset until that tradeoff is separately resolved. Existing custom skill controls, workflow-bearing settings and missing plugin manifests also block rather than being guessed away. Claude's account-synced skills are retained alongside the workbench, including when the client downloads or refreshes them after reset. [Claude skill documentation](https://code.claude.com/docs/en/skills) describes these boundaries. No settings file is wholesale replaced.

The workbench adds to client defaults. Built-in harness skills and commands, Claude's account-synced skills, Codex approval rules, operational settings and project-specific procedure skills/hooks remain explicit exceptions. Codex's bundled skills live under `CODEX_HOME/skills/.system`; Claude's synced skills live under `CLAUDE_CONFIG_DIR/skills/synced`, using `~/.codex` and `~/.claude` when no home override is set. Host-managed instructions, remotely delivered plugins, account sync, session flags and enterprise policies can add context outside the inventoried home. Retained client defaults are part of the intended context; runtime verification is still required to establish what a session loads. Start fresh sessions; already-loaded old instructions are not erased from an existing conversation.

After reset, `check` detects reintroduced personal workflow, changed plugin paths/content, conflicting visibility entries and ordinary managed drift. Updates never silently approve new plugin skills. Refresh the reset inventory when plugin versions change. Uninstall/rollback restore the initial retired content, preserving outside instruction/config edits; conflicting replacements are reported. Restoring an old instruction symlink alongside later text edits requires manual reconciliation.

## Active project baseline

Select migration targets explicitly in local, uncommitted configuration. Discovery is advisory; archived, inactive and unselected repositories remain outside the migration.

Review each project's policy independently of mechanical integration. Preserve its execution owner, design/evidence conventions, domain procedures and operational safeguards. Keep proposed diffs, exceptions and source fingerprints in ignored `.local/`.

## Each project separately

1. Inspect existing instructions, tracker, work records, docs and gates. Read the concrete local audit proposal and recheck the current checkout; it is a dated sample, not live authority.
2. Identify the intended execution owner and exceptions. A document-owned queue or offline tracker can remain local. A nonempty `policy_conflicts` list deliberately blocks installation until the conflict is settled.
3. Reconcile active work and unfinished criteria with the chosen owner. Obtain authorization before publishing issues. Historical plans and handoffs can become evidence snapshots or pointers without losing evidence or falsely marking work complete.
4. Put doc locations, tracker, commands and exceptions in local installer input. Preserve project hooks, evidence standards, terminology and specialized boundaries.
5. Preview an explicitly named repository, review the managed pointer/import, and apply only that selection. No discovery-to-install pipeline exists.

Tentative planning becomes tracked work only when adopted and publication is authorized. Once adopted, issue scope/status owns execution under the baseline; repository design/evidence is linked, not duplicated. If a project retains another division, record the exact exception rather than maintaining two active owners.

## Across machines and upstream revisions

Keep adaptations, model reference and adapter versions in the workbench checkout. Fetch reviewed changes on each machine and run `check`, `update`, then `update --apply`. The content hash detects a stale installation even without a version-number change. State, home overrides, absolute paths, backups and private audit details stay local and are not transferred as shared defaults.

Review upstream diffs against the recorded revision and license; merge useful changes intentionally into personal skills. The installer has no upstream updater. Version drift of an installed CLI is a verification task, not permission to guess support or change its settings.
