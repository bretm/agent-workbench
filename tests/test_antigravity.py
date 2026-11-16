"""Antigravity adapter lifecycle; all writes use disposable homes and Git roots."""
import json
import os
import unittest

import test_installer as fixtures
from workbench.cli import load_state
from workbench.planner import empty_state, installation, removal
from workbench.storage import Conflict
from workbench.transactions import apply


class AntigravityTests(unittest.TestCase):
    tearDown = fixtures.InstallerTests.tearDown
    cli = fixtures.InstallerTests.cli
    config = fixtures.InstallerTests.config
    tree = fixtures.InstallerTests.tree
    repo = fixtures.InstallerTests.repo

    def setUp(self):
        fixtures.InstallerTests.setUp(self)
        self.agy = self.bin / 'agy'
        self.agy.write_text('#!/bin/sh\nprintf "1.5.9\\n"\n')
        self.agy.chmod(0o755)

    def install(self, *args):
        code, output = self.cli('install', '--harness', 'antigravity', *args, '--apply')
        self.assertEqual(code, 0, output)

    def test_bootstrap_preview_native_project_and_idempotence(self):
        repo = self.repo('Google project')
        instructions = self.home / '.gemini/AGENTS.md'
        instructions.parent.mkdir()
        instructions.write_text('Existing Google preferences.\n')
        instructions.chmod(0o640)
        settings = instructions.parent / 'antigravity-cli/settings.json'
        settings.parent.mkdir()
        settings.write_text('{"model": "fixture", "toolPermission": "strict"}\n')
        before = self.tree(self.home), self.tree(repo)
        code, output = self.cli('install', '--harness', 'antigravity', '--repo', repo)
        self.assertEqual(code, 0, output)
        self.assertEqual(before, (self.tree(self.home), self.tree(repo)))
        self.install('--repo', repo)
        self.assertIn('Existing Google preferences.', instructions.read_text())
        self.assertIn('Personal working agreements', instructions.read_text())
        self.assertEqual(instructions.stat().st_mode & 0o777, 0o640)
        self.assertEqual(json.loads(settings.read_text()), {
            'model': 'fixture', 'toolPermission': 'strict',
            'permissions': {'allow': [f'read_file({self.home / ".agents"})']}})
        self.assertTrue((repo / 'AGENTS.md').is_file())
        self.assertFalse((repo / 'GEMINI.md').exists())
        for name in json.loads((self.source / 'workbench.json').read_text())['skills']:
            link = self.home / '.gemini/config/skills' / name
            self.assertTrue(link.is_symlink())
            self.assertTrue((link / 'SKILL.md').is_file())
        self.assertFalse((self.home / '.agents/skills').exists())
        before = self.tree(self.home), self.tree(repo)
        self.install('--repo', repo)
        self.assertEqual(before, (self.tree(self.home), self.tree(repo)))
        self.assertEqual(self.cli('check')[0], 0)

    @property
    def settings(self):
        return self.home / '.gemini/antigravity-cli/settings.json'

    @property
    def read_grant(self):
        return f'read_file({self.home / ".agents"})'

    def save_settings(self, data):
        self.settings.parent.mkdir(parents=True, exist_ok=True)
        self.settings.write_text(json.dumps(data) + '\n')

    def test_read_permission_is_private_previewed_and_reversible(self):
        before = self.tree(self.home)
        code, output = self.cli('install', '--harness', 'antigravity', '--diff')
        self.assertEqual(code, 0, output)
        self.assertIn(self.read_grant, output)
        self.assertEqual(before, self.tree(self.home))
        self.install()
        self.assertEqual(json.loads(self.settings.read_text()), {'permissions': {'allow': [self.read_grant]}})
        self.assertEqual(self.settings.stat().st_mode & 0o777, 0o600)
        self.assertFalse(json.loads(self.settings.read_text()).get('allowNonWorkspaceAccess', False))
        self.assertEqual(self.cli('rollback', '--apply')[0], 0)
        self.assertFalse(self.settings.exists())
        self.install()
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        self.assertFalse(self.settings.exists())
        self.assertEqual(self.cli('rollback', '--apply')[0], 0)
        self.assertEqual(json.loads(self.settings.read_text()), {'permissions': {'allow': [self.read_grant]}})
        self.assertEqual(self.cli('check')[0], 0)

    def test_preexisting_grant_remains_unowned_and_byte_identical(self):
        data = {'model': 'fixture', 'permissions': {'allow': ['command(gh)', self.read_grant]}}
        self.save_settings(data)
        before = self.settings.read_bytes()
        self.install()
        self.assertNotIn(str(self.settings), load_state(self.state)['entries'])
        self.assertEqual(self.settings.read_bytes(), before)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        self.assertEqual(self.settings.read_bytes(), before)

    def test_permission_lifecycle_preserves_user_settings_and_explicit_controls(self):
        data = {'model': 'fixture', 'allowNonWorkspaceAccess': False, 'toolPermission': 'strict',
                'permissions': {'allow': ['command(gh)'], 'ask': [self.read_grant],
                                'deny': ['write_file(*)']}, 'future': {'untouched': True}}
        self.save_settings(data)
        self.settings.chmod(0o640)
        before = self.settings.read_bytes()
        self.install()
        saved = json.loads(self.settings.read_text())
        saved['permissions']['allow'].remove(self.read_grant)
        self.assertEqual(saved, data)
        self.assertEqual(self.settings.stat().st_mode & 0o777, 0o640)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        self.assertEqual(self.settings.read_bytes(), before)

    def test_later_user_settings_survive_update_rollback_and_uninstall(self):
        self.save_settings({'model': 'old'})
        self.install()
        data = json.loads(self.settings.read_text())
        data.update(model='new', allowNonWorkspaceAccess=True)
        data['permissions']['allow'].append('command(gh)')
        self.save_settings(data)
        reference = self.source / 'reference/models.md'
        reference.write_text(reference.read_text() + '\nUpdated fixture.\n')
        code, output = self.cli('update', '--apply')
        self.assertEqual(code, 0, output)
        self.assertEqual(self.cli('check')[0], 0)
        self.assertEqual(self.cli('rollback', '--apply')[0], 0)
        self.assertEqual(json.loads(self.settings.read_text()), data)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        data['permissions']['allow'].remove(self.read_grant)
        self.assertEqual(json.loads(self.settings.read_text()), data)

    def test_initial_rollback_preserves_later_user_settings(self):
        self.install()
        data = json.loads(self.settings.read_text())
        data['model'] = 'new'
        self.save_settings(data)
        self.assertEqual(self.cli('rollback', '--apply')[0], 0)
        self.assertEqual(json.loads(self.settings.read_text()), {'model': 'new'})

    def test_existing_empty_permission_containers_survive_removal(self):
        for data in ({'permissions': {}}, {'permissions': {'allow': []}}):
            with self.subTest(data=data):
                self.save_settings(data)
                self.install()
                saved = json.loads(self.settings.read_text())
                saved['model'] = 'later'
                self.save_settings(saved)
                self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
                self.assertEqual(json.loads(self.settings.read_text()), {**data, 'model': 'later'})

    def test_upgrade_adds_permission_and_rollback_keeps_previous_install(self):
        adapter = self.source / 'adapters/antigravity.json'
        current = adapter.read_text()
        legacy = json.loads(current)
        del legacy['read_permissions']
        adapter.write_text(json.dumps(legacy))
        self.install()
        self.assertFalse(self.settings.exists())
        adapter.write_text(current)
        before = self.tree(self.home)
        code, output = self.cli('update')
        self.assertEqual(code, 0, output)
        self.assertIn(self.read_grant, output)
        self.assertEqual(before, self.tree(self.home))
        self.assertEqual(self.cli('update', '--apply')[0], 0)
        self.assertIn(self.read_grant, json.loads(self.settings.read_text())['permissions']['allow'])
        self.assertEqual(self.cli('rollback', '--apply')[0], 0)
        self.assertFalse(self.settings.exists())
        self.assertTrue((self.home / '.gemini/config/skills/handoff').is_symlink())

    def test_permission_drift_blocks_update_and_uninstall_without_writes(self):
        self.install()
        for grants in ([], [self.read_grant, self.read_grant]):
            self.save_settings({'permissions': {'allow': grants}})
            before = self.tree(self.home)
            for command in ('check', 'update', 'uninstall'):
                code, output = self.cli(command, *([] if command == 'check' else ['--apply']))
                self.assertEqual(code, 2, output)
                self.assertEqual(before, self.tree(self.home))

    def test_invalid_or_linked_settings_block_before_writes(self):
        self.settings.parent.mkdir(parents=True)
        for text in ('{', '[]', '{"permissions": []}', '{"permissions": {"allow": "*"}}',
                     '{"permissions": {"deny": [false]}}'):
            with self.subTest(text=text):
                self.settings.write_text(text)
                before = self.tree(self.home)
                code, output = self.cli('install', '--harness', 'antigravity', '--apply')
                self.assertEqual(code, 2, output)
                self.assertEqual(before, self.tree(self.home))
        self.settings.unlink()
        target = self.root / 'linked-settings.json'
        target.write_text('{}')
        self.settings.symlink_to(target)
        before = self.tree(self.home)
        code, output = self.cli('install', '--harness', 'antigravity', '--apply')
        self.assertEqual(code, 2, output)
        self.assertEqual(before, self.tree(self.home))
        self.assertEqual(target.read_text(), '{}')

    def test_permission_recovery_preserves_later_settings_and_rechecks_preview(self):
        plan = installation(self.source, self.home, self.state, empty_state(), {}, ['antigravity'], [], {})
        index = next(i for i, op in enumerate(plan.operations, 1) if op['type'] == 'json-permissions')
        with self.assertRaises(OSError):
            apply(plan, self.state, fail_after=index)
        saved = json.loads(self.settings.read_text())
        saved['model'] = 'later'
        self.save_settings(saved)
        self.assertEqual(self.cli('recover', '--apply')[0], 0)
        self.assertEqual(json.loads(self.settings.read_text()), {'model': 'later'})
        plan = installation(self.source, self.home, self.state, empty_state(), {}, ['antigravity'], [], {})
        self.save_settings({'model': 'changed after preview'})
        with self.assertRaises(Conflict):
            apply(plan, self.state)

    def test_permission_diff_does_not_expose_unrelated_settings(self):
        self.save_settings({'private': 'fixture-private-value'})
        code, output = self.cli('install', '--harness', 'antigravity', '--diff')
        self.assertEqual(code, 0, output)
        self.assertIn(self.read_grant, output)
        self.assertNotIn('fixture-private-value', output)

    def test_interrupted_uninstall_recovery_restores_grant_and_keeps_user_edits(self):
        self.install()
        plan = removal(load_state(self.state))
        index = next(i for i, op in enumerate(plan.operations, 1) if op['type'] == 'json-permissions')
        with self.assertRaises(OSError):
            apply(plan, self.state, fail_after=index)
        self.save_settings({'model': 'changed during uninstall'})
        self.assertEqual(self.cli('recover', '--apply')[0], 0)
        self.assertEqual(json.loads(self.settings.read_text()), {
            'model': 'changed during uninstall', 'permissions': {'allow': [self.read_grant]}})
        self.assertEqual(self.cli('check')[0], 0)

    def test_codex_and_antigravity_link_native_locations_to_one_content_pack(self):
        code, output = self.cli('install', '--harness', 'codex', '--apply')
        self.assertEqual(code, 0, output)
        link = self.home / '.agents/skills/handoff'
        target = os.readlink(link)
        self.install()
        self.assertEqual(os.readlink(link), target)
        native = self.home / '.gemini/config/skills/handoff'
        self.assertEqual(native.resolve(), link.resolve())
        self.assertEqual(set(load_state(self.state)['harnesses']), {'codex', 'antigravity'})
        self.assertEqual(self.cli('check')[0], 0)
        self.assertEqual(self.cli('rollback', '--apply')[0], 0)
        self.assertTrue(link.is_symlink())
        self.assertFalse(native.is_symlink())
        self.assertFalse((self.home / '.gemini/AGENTS.md').exists())
        self.assertEqual(self.cli('check')[0], 0)

    def test_update_rollback_and_uninstall_preserve_outside_edits(self):
        self.install()
        link = self.home / '.gemini/config/skills/handoff'
        target = os.readlink(link)
        instructions = self.home / '.gemini/AGENTS.md'
        instructions.write_text(instructions.read_text() + '\nNew Google preference.\n')
        reference = self.source / 'reference/models.md'
        reference.write_text(reference.read_text() + '\nFixture reference update.\n')
        self.assertEqual(self.cli('check')[0], 1)
        self.assertEqual(self.cli('update', '--apply')[0], 0)
        self.assertNotEqual(os.readlink(link), target)
        self.assertEqual(self.cli('check')[0], 0)
        self.assertEqual(self.cli('rollback', '--apply')[0], 0)
        self.assertEqual(os.readlink(link), target)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        self.assertFalse(link.is_symlink())
        self.assertEqual(instructions.read_text().strip(), 'New Google preference.')

    def test_upgrade_from_shared_location_preserves_codex_and_can_rollback(self):
        adapter = self.source / 'adapters/antigravity.json'
        current = adapter.read_text()
        legacy = json.loads(current)
        legacy.update(skill_scope='user', skill_directory='.agents/skills',
                      alternate_skill_directory='config/skills')
        adapter.write_text(json.dumps(legacy))
        self.install('--harness', 'codex')
        shared = self.home / '.agents/skills/handoff'
        target = os.readlink(shared)
        native = self.home / '.gemini/config/skills/handoff'
        adapter.write_text(current)
        before = self.tree(self.home)
        code, output = self.cli('update', '--harness', 'antigravity')
        self.assertEqual(code, 0, output)
        self.assertEqual(before, self.tree(self.home))
        code, output = self.cli('update', '--harness', 'antigravity', '--apply')
        self.assertEqual(code, 0, output)
        self.assertTrue(native.is_symlink())
        self.assertEqual(os.readlink(shared), target)
        self.assertEqual(self.cli('check', '--harness', 'antigravity')[0], 0)
        self.assertEqual(self.cli('rollback', '--apply')[0], 0)
        self.assertFalse(native.is_symlink())
        self.assertEqual(os.readlink(shared), target)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        self.assertFalse(shared.is_symlink())

    def test_custom_home_is_recorded_for_update_and_check(self):
        custom = self.root / 'custom Google home'
        self.install('--harness-home', f'antigravity={custom}')
        self.assertTrue((custom / 'AGENTS.md').is_file())
        self.assertFalse((self.home / '.gemini/AGENTS.md').exists())
        self.assertTrue((custom / 'config/skills/handoff').is_symlink())
        self.assertEqual(json.loads((custom / 'antigravity-cli/settings.json').read_text()), {
            'permissions': {'allow': [self.read_grant]}})
        self.assertFalse((self.home / '.agents/skills').exists())
        self.assertEqual(load_state(self.state)['homes']['antigravity'], str(custom))
        self.assertEqual(self.cli('check')[0], 0)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        self.assertFalse((custom / 'AGENTS.md').exists())

    def test_missing_cli_and_unverified_version_block_without_writes(self):
        self.agy.unlink()
        before = self.tree(self.home)
        code, output = self.cli('install', '--harness', 'antigravity', '--apply')
        self.assertEqual(code, 2, output)
        self.assertIn('https://antigravity.google/docs/cli/install/', output)
        self.assertEqual(before, self.tree(self.home))
        self.agy.write_text('#!/bin/sh\nprintf "1.3.6\\n"\n')
        self.agy.chmod(0o755)
        code, output = self.cli('install', '--harness', 'antigravity', '--apply')
        self.assertEqual(code, 2, output)
        self.assertIn('adapter verified on 1.5.9', output)
        self.assertEqual(before, self.tree(self.home))

    def test_google_skill_locations_block_competing_names(self):
        for location in ['skills', 'antigravity-cli/skills']:
            with self.subTest(location=location):
                skill = self.home / '.gemini' / location / 'renamed-skill/SKILL.md'
                skill.parent.mkdir(parents=True)
                skill.write_text('---\nname: handoff\ndescription: competing workflow\n---\n')
                before = self.tree(self.home)
                code, output = self.cli('install', '--harness', 'antigravity', '--apply')
                self.assertEqual(code, 2, output)
                self.assertIn('competing discovery location', output)
                self.assertEqual(before, self.tree(self.home))
                unrelated = skill.parent.parent / 'unrelated-link'
                unrelated.symlink_to('/missing/awb-fixture-skill')
                code, output = self.cli('discover')
                self.assertEqual(code, 0, output)
                self.assertIn(f'LINK {unrelated}', output)
                unrelated.unlink()
                skill.unlink()

    def test_legacy_project_skill_collision_blocks_apply(self):
        repo = self.repo('legacy Google skills')
        skill = repo / '_agent/skills/handoff/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('---\nname: handoff\ndescription: legacy\n---\n')
        code, output = self.cli('install', '--harness', 'antigravity', '--repo', repo, '--apply')
        self.assertEqual(code, 2, output)
        self.assertIn('project skill competes', output)
        self.assertFalse((repo / 'AGENTS.md').exists())
        self.assertFalse(self.state.exists())

    def test_reset_is_explicitly_unsupported(self):
        before = self.tree(self.home)
        code, output = self.cli('reset-workflow', '--harness', 'antigravity', '--inventory')
        self.assertEqual(code, 2, output)
        self.assertIn('no verified workflow-reset discovery contract', output)
        self.assertEqual(before, self.tree(self.home))

    def test_additive_install_after_reset_including_legacy_state(self):
        code, output = self.cli('reset-workflow', '--harness', 'codex', '--inventory')
        self.assertEqual(code, 0, output)
        review = self.config(json.loads(output))
        code, output = self.cli('reset-workflow', '--config', review, '--apply')
        self.assertEqual(code, 0, output)
        state = load_state(self.state)
        self.assertEqual(state['workflow_reset']['harnesses'], ['codex'])
        del state['workflow_reset']['harnesses']
        (self.state / 'state.json').write_text(json.dumps(state))
        self.install()
        self.assertEqual(self.cli('check')[0], 0)

    def test_detection_skips_missing_google_cli(self):
        self.agy.unlink()
        code, output = self.cli('install', '--apply')
        self.assertEqual(code, 0, output)
        self.assertEqual(set(load_state(self.state)['harnesses']), {'codex', 'claude'})

    def test_explicit_target_preserves_and_does_not_gate_on_other_reset_workflow(self):
        code, output = self.cli('reset-workflow', '--harness', 'claude', '--inventory')
        self.assertEqual(code, 0, output)
        review = self.config(json.loads(output))
        code, output = self.cli('reset-workflow', '--config', review, '--apply')
        self.assertEqual(code, 0, output)
        custom = self.home / '.claude/skills/unreviewed/SKILL.md'
        custom.parent.mkdir(parents=True)
        custom.write_text('---\nname: unreviewed\ndescription: Personal procedure\n---\n')
        before = self.tree(self.home / '.claude')
        self.install()
        self.assertEqual(before, self.tree(self.home / '.claude'))
        code, output = self.cli('check', '--harness', 'antigravity')
        self.assertEqual(code, 0, output)
        code, output = self.cli('check')
        self.assertEqual(code, 2, output)
        self.assertIn('unmanaged workflow appeared', output)

    def test_unsafe_additional_discovery_path_and_unknown_default_rejected(self):
        adapter = self.source / 'adapters/antigravity.json'
        original = adapter.read_text()
        data = json.loads(original)
        data['additional_skill_directories'] = ['../escape']
        adapter.write_text(json.dumps(data))
        self.assertEqual(self.cli('validate')[0], 2)
        adapter.write_text(original)
        for contract in ({'settings_file': '../escape', 'user_directories': ['.agents']},
                         {'settings_file': 'settings.json', 'user_directories': ['../escape']},
                         {'settings_file': 'settings.json', 'user_directories': ['.']},
                         {'settings_file': 'settings.json', 'user_directories': ['./']},
                         {'settings_file': 'settings.json', 'user_directories': '.agents'}):
            data = json.loads(original)
            data['read_permissions'] = contract
            adapter.write_text(json.dumps(data))
            self.assertEqual(self.cli('validate')[0], 2)
        adapter.write_text(original)
        manifest = self.source / 'workbench.json'
        data = json.loads(manifest.read_text())
        data['default_harnesses'] = ['unknown']
        manifest.write_text(json.dumps(data))
        self.assertEqual(self.cli('validate')[0], 2)


if __name__ == '__main__':
    unittest.main()
