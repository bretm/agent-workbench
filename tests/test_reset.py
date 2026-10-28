import json
import os
from pathlib import Path
import tomllib
import unittest
from unittest.mock import patch

import test_installer as fixtures
from workbench.cli import load_state
from workbench.planner import empty_state
from workbench.reset import inventory, reset_installation
from workbench.storage import snapshot
from workbench.transactions import apply, locked, pending


class ResetTests(unittest.TestCase):
    setUp = fixtures.InstallerTests.setUp
    tearDown = fixtures.InstallerTests.tearDown
    cli = fixtures.InstallerTests.cli
    config = fixtures.InstallerTests.config
    tree = fixtures.InstallerTests.tree
    repo = fixtures.InstallerTests.repo

    def legacy(self):
        p = self.home / '.agents/skills/handoff'
        p.mkdir(parents=True)
        (p / 'SKILL.md').write_text('---\nname: handoff\ndescription: old\n---\nOld workflow.\n')
        (p / 'helper').write_bytes(b'\x00\xff helper')
        (p / 'helper').chmod(0o750)
        (p / 'external').symlink_to('/missing/do-not-follow')
        (p.parent / 'skill-scout.backup').symlink_to('/missing/backup')
        c = self.home / '.claude/skills/grill-me'
        c.parent.mkdir(parents=True)
        c.symlink_to('../../.agents/skills/handoff')
        for rel in ['.codex/AGENTS.md', '.codex/AGENTS.override.md', '.claude/CLAUDE.md', '.claude/commands/old.md', 'AGENTS.md']:
            f = self.home / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text('Legacy workflow.\n')
            f.chmod(0o640)
        system = self.home / '.codex/skills/.system'
        system.mkdir(parents=True)
        (system / 'builtin').write_text('built in')
        for rel in ['.codex/config.toml', '.codex/rules/default.rules', '.claude/settings.json', '.codex/auth.json']:
            f = self.home / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text('{}\n' if f.suffix == '.json' else '# operational configuration\n')

    def review(self):
        code, output = self.cli('reset-workflow', '--inventory')
        self.assertEqual(code, 0, output)
        return self.config(json.loads(output))

    def reset(self, config=None, *args):
        config = config or self.review()
        code, output = self.cli('reset-workflow', '--config', config, '--apply', *args)
        self.assertEqual(code, 0, output)
        return config

    def test_inventory_preview_and_dry_run_never_write(self):
        self.legacy()
        before = self.tree(self.home)
        config = self.review()
        self.assertEqual(self.tree(self.home), before)
        code, output = self.cli('reset-workflow', '--config', config, '--dry-run')
        self.assertEqual(code, 0, output)
        self.assertIn('ARCHIVE / RETIRE', output)
        self.assertEqual(self.tree(self.home), before)
        self.assertEqual(self.cli('reset-workflow', '--inventory', '--apply')[0], 2)

    def test_full_retirement_preserves_system_auth_settings_and_targets(self):
        self.legacy()
        sentinels = {p: p.read_bytes() for p in [self.home / x for x in ['.codex/auth.json', '.codex/config.toml', '.codex/rules/default.rules', '.claude/settings.json', '.codex/skills/.system/builtin']]}
        self.reset()
        names = set(json.loads((self.source / 'workbench.json').read_text())['skills'])
        for rel in ['.agents/skills', '.claude/skills']:
            self.assertEqual({p.name for p in (self.home / rel).iterdir()}, names)
        self.assertFalse((self.home / 'AGENTS.md').exists())
        for rel in ['.codex/AGENTS.md', '.claude/CLAUDE.md']:
            self.assertNotIn('Legacy', (self.home / rel).read_text())
        for p, expected in sentinels.items():
            self.assertEqual(p.read_bytes(), expected)
        self.assertEqual(self.cli('check')[0], 0)

    def test_reset_is_idempotent_and_updates_preserve_outside_changes(self):
        self.legacy()
        config = self.reset()
        before = self.tree(self.home)
        self.reset(config)
        self.assertEqual(self.tree(self.home), before)
        p = self.home / '.codex/AGENTS.md'
        p.write_text(p.read_text() + '\nSubsequent personal instruction.\n')
        r = self.source / 'reference/models.md'
        r.write_text(r.read_text() + '\nNew reference.\n')
        code, output = self.cli('update', '--apply')
        self.assertEqual(code, 0, output)
        code, output = self.cli('uninstall', '--apply')
        self.assertEqual(code, 0, output)
        self.assertIn('Legacy workflow.', p.read_text())
        self.assertIn('Subsequent personal instruction.', p.read_text())

    def test_uninstall_restores_directory_bytes_modes_and_literal_links(self):
        self.legacy()
        original = {str(p): snapshot(p, tree=True) for p in [self.home / x for x in ['.agents/skills/handoff', '.agents/skills/skill-scout.backup', '.claude/skills/grill-me', '.codex/AGENTS.md', 'AGENTS.md']]}
        self.reset()
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        for p, expected in original.items():
            self.assertEqual(snapshot(Path(p), tree=True), expected)

    def test_initial_rollback_preserves_later_instruction_edits(self):
        self.legacy()
        self.reset()
        p = self.home / '.claude/CLAUDE.md'
        p.write_text(p.read_text() + '\nLater outside edit.\n')
        code, output = self.cli('rollback', '--apply')
        self.assertEqual(code, 0, output)
        self.assertIn('Legacy workflow.', p.read_text())
        self.assertIn('Later outside edit.', p.read_text())

    def test_new_or_changed_workflow_requires_new_review(self):
        self.legacy()
        config = self.review()
        p = self.home / '.agents/skills/handoff/helper'
        p.write_text('changed after review')
        before = self.tree(self.home)
        self.assertEqual(self.cli('reset-workflow', '--config', config, '--apply')[0], 2)
        self.assertEqual(before, self.tree(self.home))
        self.assertEqual(self.cli('reset-workflow', '--apply')[0], 2)

    def test_arbitrary_reset_path_rejected(self):
        config = self.review()
        data = json.loads(config.read_text())
        data['workflow_reset']['entries'].append({'path': str(self.home / '.codex/auth.json'), 'fingerprint': 'fake', 'kind': 'file', 'action': 'retire'})
        config.write_text(json.dumps(data))
        self.assertEqual(self.cli('reset-workflow', '--config', config, '--apply')[0], 2)

    def test_enabled_plugins_block_reset_without_disabling_connections(self):
        self.legacy()
        p = self.home / '.codex/config.toml'
        p.write_text('[plugins."example@marketplace"]\nenabled = true\n[mcp_servers.keep]\nurl = "https://example.invalid"\n')
        config = self.review()
        before = self.tree(self.home)
        code, output = self.cli('reset-workflow', '--config', config, '--apply')
        self.assertEqual(code, 2, output)
        self.assertIn('selective skill suppression not verified', output)
        self.assertEqual(before, self.tree(self.home))
        # Removing blockers from the review never bypasses current discovery.
        data = json.loads(config.read_text());data['workflow_reset']['blockers'] = []
        config.write_text(json.dumps(data))
        self.assertEqual(self.cli('reset-workflow', '--config', config, '--apply')[0], 2)

    def test_workflow_settings_still_block_reset_with_synced_skills(self):
        self.legacy()
        p = self.home / '.claude/settings.json'
        p.write_text('{"outputStyle":"old","theme":"dark"}')
        (self.home / '.claude/skills/synced').mkdir()
        config = self.review()
        code, output = self.cli('reset-workflow', '--config', config, '--apply')
        self.assertEqual(code, 2, output)
        self.assertIn('per-key migration', output)

    def test_bundled_and_synced_skills_survive_reset_update_and_removal(self):
        self.legacy()
        synced = self.home / '.claude/skills/synced/account/pdf/SKILL.md'
        synced.parent.mkdir(parents=True)
        synced.write_text('---\nname: pdf\ndescription: Client-provided PDF skill\n---\nRead PDFs.')
        defaults = [self.home / '.codex/skills/.system', self.home / '.claude/skills/synced']
        before = [snapshot(p, tree=True) for p in defaults]
        review = json.loads(self.review().read_text())['workflow_reset']
        self.assertFalse(review['blockers'], review['blockers'])
        self.assertFalse(any(e['path'].startswith(str(defaults[1])) for e in review['entries']))
        self.reset()
        self.assertEqual([snapshot(p, tree=True) for p in defaults], before)
        reference = self.source / 'agreements/working.md'
        reference.write_text(reference.read_text() + '\nFixture update.\n')
        for command in ['update', 'rollback', 'uninstall']:
            code, output = self.cli(command, '--apply')
            self.assertEqual(code, 0, output)
            self.assertEqual([snapshot(p, tree=True) for p in defaults], before)

    def test_synced_skills_can_appear_and_refresh_after_reset(self):
        self.legacy()
        self.reset()
        synced = self.home / '.claude/skills/synced/account/pdf/SKILL.md'
        synced.parent.mkdir(parents=True)
        for content in ['Initial synced skill.', 'Refreshed synced skill.']:
            synced.write_text(content)
            code, output = self.cli('check')
            self.assertEqual(code, 0, output)
            self.assertEqual(synced.read_text(), content)
        personal = self.home / '.claude/skills/unreviewed/SKILL.md'
        personal.parent.mkdir()
        personal.write_text('Unreviewed personal workflow.')
        self.assertEqual(self.cli('check')[0], 2)

    def test_preserved_skill_directories_reject_paths(self):
        path = self.source / 'adapters/claude.json'
        original = json.loads(path.read_text())
        for value in [['../synced'], ['/tmp/defaults'], ['.'], 'synced']:
            with self.subTest(value=value):
                data = json.loads(json.dumps(original))
                data['workflow_reset']['preserved_skill_directories'] = value
                path.write_text(json.dumps(data))
                self.assertEqual(self.cli('validate')[0], 2)

    def test_partial_reset_failure_and_recovery(self):
        self.legacy()
        original = snapshot(self.home / '.agents/skills/handoff', tree=True)
        config = json.loads(self.review().read_text())
        plan = reset_installation(self.source, self.home, self.state, empty_state(), config, [], [], {})
        self.assertFalse(plan.conflicts, plan.conflicts)
        with locked(self.state):
            with self.assertRaises(OSError):
                apply(plan, self.state, fail_after=3)
        self.assertTrue(pending(self.state))
        code, output = self.cli('recover', '--apply')
        self.assertEqual(code, 0, output)
        self.assertEqual(snapshot(self.home / '.agents/skills/handoff', tree=True), original)
        self.reset()

    def test_health_detects_reintroduced_skill_and_uninstall_preserves_it(self):
        self.legacy()
        self.reset()
        p = self.home / '.agents/skills/unreviewed'
        p.mkdir();(p / 'SKILL.md').write_text('new unrelated skill')
        self.assertEqual(self.cli('check')[0], 2)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        self.assertEqual((p / 'SKILL.md').read_text(), 'new unrelated skill')

    def test_selected_projects_only_and_project_skills_preserved(self):
        self.legacy()
        a,b,c,d = [self.repo(name) for name in ['project-one','project-two','project-three','archived']]
        local = c / '.claude/skills/new-adr'
        local.mkdir(parents=True);(local / 'SKILL.md').write_text('domain skill')
        settings = c / '.claude/settings.json';settings.write_text('{"hooks":{"PreToolUse":[]}}')
        before = self.tree(d)
        self.reset(None, '--repo', a, '--repo', b, '--repo', c)
        self.assertEqual(before, self.tree(d))
        self.assertEqual((local / 'SKILL.md').read_text(), 'domain skill')
        self.assertEqual(settings.read_text(), '{"hooks":{"PreToolUse":[]}}')

    def test_changed_owned_skill_or_recreated_retired_path_blocks_removal(self):
        self.legacy()
        self.reset()
        p = self.home / 'AGENTS.md';p.write_text('Subsequent replacement')
        before = self.tree(self.home)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 2)
        self.assertEqual(self.cli('rollback', '--apply')[0], 2)
        self.assertEqual(before, self.tree(self.home))

    def test_ordinary_install_rejects_reset_review(self):
        self.assertEqual(self.cli('install', '--config', self.review(), '--apply')[0], 2)

    def plugin(self):
        directory = self.home / '.codex/plugins/cache/fixture/example/1.0.0'
        (directory / '.codex-plugin').mkdir(parents=True)
        (directory / '.codex-plugin/plugin.json').write_text('{"name":"example","skills":"./skills/"}')
        skill = directory / 'skills/example/SKILL.md';skill.parent.mkdir(parents=True)
        skill.write_text('---\nname: fixture-plugin-skill\ndescription: fixture\n---\nFixture.')
        p = self.home / '.codex/config.toml'
        p.write_text('model = "keep-model"\n[plugins."example@fixture"]\nenabled = true\n[mcp_servers.keep]\nurl = "https://example.invalid"\n')
        return p, skill

    def test_verified_plugin_control_preserves_settings_updates_and_removal(self):
        self.legacy()
        p, skill = self.plugin()
        original = p.read_text()
        config = self.reset()
        data = tomllib.loads(p.read_text())
        self.assertEqual(data['skills']['config'], [{'path': str(skill), 'enabled': False}])
        self.assertTrue(data['plugins']['example@fixture']['enabled'])
        self.assertEqual(data['model'], 'keep-model')
        self.assertEqual(self.cli('check')[0], 0)
        before = self.tree(self.home)
        self.reset(config)
        self.assertEqual(before, self.tree(self.home))
        p.write_text(p.read_text() + '\n[mcp_servers.later]\nurl = "https://later.invalid"\n')
        self.assertEqual(self.cli('update', '--apply')[0], 0)
        code, output = self.cli('uninstall', '--apply')
        self.assertEqual(code, 0, output)
        self.assertTrue(p.read_text().startswith(original))
        self.assertIn('mcp_servers.later', p.read_text())
        self.assertNotIn('skills.config', p.read_text())

    def test_new_plugin_paths_and_reenablement_block_health(self):
        self.legacy()
        p, skill = self.plugin()
        self.reset()
        original = p.read_text()
        p.write_text(original + '\n[[skills.config]]\npath = '+json.dumps(str(skill))+'\nenabled = true\n')
        self.assertEqual(self.cli('check')[0], 2)
        self.assertEqual(self.cli('update', '--apply')[0], 2)
        p.write_text(original)
        another = skill.parent.parent / 'extra/SKILL.md';another.parent.mkdir();another.write_text('extra plugin skill')
        self.assertEqual(self.cli('check')[0], 2)
        self.assertEqual(self.cli('update', '--apply')[0], 2)

    def test_failure_between_directory_archive_and_link_write_recovers(self):
        self.legacy()
        original = snapshot(self.home / '.agents/skills/handoff', tree=True)
        config = json.loads(self.review().read_text())
        plan = reset_installation(self.source, self.home, self.state, empty_state(), config, [], [], {})
        target = self.home / '.agents/skills/handoff'
        real_replace = os.replace
        def interrupt_link(source, destination):
            if Path(destination) == target and Path(source).is_symlink():
                raise OSError('failure after directory archive')
            return real_replace(source, destination)
        with locked(self.state), patch('workbench.storage.os.replace', side_effect=interrupt_link):
            with self.assertRaises(OSError):
                apply(plan, self.state)
        self.assertFalse(target.exists())
        code, output = self.cli('recover', '--apply')
        self.assertEqual(code, 0, output)
        self.assertEqual(snapshot(target, tree=True), original)

    def test_linked_instruction_restoration_reports_outside_edit_conflict(self):
        self.legacy()
        p = self.home / '.codex/AGENTS.md';p.unlink();p.symlink_to('/missing/old-instruction')
        self.reset()
        p.write_text(p.read_text()+'Later outside edit.\n')
        self.assertEqual(self.cli('rollback', '--apply')[0], 2)
        self.assertIn('Later outside edit.', p.read_text())

    def test_reset_after_additive_install_retires_legacy_prose(self):
        p = self.home / '.codex/AGENTS.md';p.parent.mkdir()
        p.write_text('Legacy personal workflow.\n')
        code, output = self.cli('install', '--harness', 'codex', '--apply')
        self.assertEqual(code, 0, output)
        self.reset()
        self.assertNotIn('Legacy personal workflow.', p.read_text())
        self.assertEqual(self.cli('check')[0], 0)
        code, output = self.cli('uninstall', '--apply')
        self.assertEqual(code, 0, output)
        self.assertIn('Legacy personal workflow.', p.read_text())
        self.assertNotIn('agent-workbench:begin', p.read_text())

    def test_cached_latest_alias_is_disabled_without_following_for_mutation(self):
        self.legacy()
        p, skill = self.plugin()
        alias = skill.parents[2].parent / 'latest'
        alias.symlink_to('1.0.0')
        self.reset()
        paths = {e['path'] for e in tomllib.loads(p.read_text())['skills']['config']}
        self.assertEqual(len(paths), 2)
        self.assertIn(str(alias / 'skills/example/SKILL.md'), paths)
        self.assertEqual(self.cli('check')[0], 0)

    def test_deselection_never_reintroduces_retired_legacy_skill(self):
        self.legacy()
        self.reset()
        p = self.source / 'workbench.json';data = json.loads(p.read_text());del data['skills']['handoff'];p.write_text(json.dumps(data))
        code, output = self.cli('update', '--apply')
        self.assertEqual(code, 0, output)
        self.assertFalse((self.home / '.agents/skills/handoff').exists())
        self.assertEqual(self.cli('check')[0], 0)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        self.assertTrue((self.home / '.agents/skills/handoff/helper').is_file())

    def test_refresh_after_disabling_last_plugin_removes_old_controls(self):
        self.legacy()
        p, skill = self.plugin()
        self.reset()
        p.write_text(p.read_text().replace('enabled = true', 'enabled = false'))
        self.assertEqual(self.cli('check')[0], 2)
        self.reset()
        self.assertNotIn('skills.config', p.read_text())
        self.assertEqual(self.cli('check')[0], 0)
