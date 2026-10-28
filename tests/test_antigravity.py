"""Antigravity adapter lifecycle; all writes use disposable homes and Git roots."""
import json
import os
import unittest

import test_installer as fixtures
from workbench.cli import load_state


class AntigravityTests(unittest.TestCase):
    tearDown = fixtures.InstallerTests.tearDown
    cli = fixtures.InstallerTests.cli
    config = fixtures.InstallerTests.config
    tree = fixtures.InstallerTests.tree
    repo = fixtures.InstallerTests.repo

    def setUp(self):
        fixtures.InstallerTests.setUp(self)
        self.agy = self.bin / 'agy'
        self.agy.write_text('#!/bin/sh\nprintf "1.4.2\\n"\n')
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
        self.assertEqual(settings.read_text(), '{"model": "fixture", "toolPermission": "strict"}\n')
        self.assertTrue((repo / 'AGENTS.md').is_file())
        self.assertFalse((repo / 'GEMINI.md').exists())
        for name in json.loads((self.source / 'workbench.json').read_text())['skills']:
            self.assertTrue((self.home / '.agents/skills' / name / 'SKILL.md').is_file())
        self.assertFalse((self.home / '.gemini/config/skills').exists())
        before = self.tree(self.home), self.tree(repo)
        self.install('--repo', repo)
        self.assertEqual(before, (self.tree(self.home), self.tree(repo)))
        self.assertEqual(self.cli('check')[0], 0)

    def test_codex_and_antigravity_share_one_set_of_skill_links(self):
        code, output = self.cli('install', '--harness', 'codex', '--apply')
        self.assertEqual(code, 0, output)
        link = self.home / '.agents/skills/handoff'
        target = os.readlink(link)
        self.install()
        self.assertEqual(os.readlink(link), target)
        self.assertEqual(set(load_state(self.state)['harnesses']), {'codex', 'antigravity'})
        self.assertEqual(self.cli('check')[0], 0)
        self.assertEqual(self.cli('rollback', '--apply')[0], 0)
        self.assertTrue(link.is_symlink())
        self.assertFalse((self.home / '.gemini/AGENTS.md').exists())
        self.assertEqual(self.cli('check')[0], 0)

    def test_update_rollback_and_uninstall_preserve_outside_edits(self):
        self.install()
        link = self.home / '.agents/skills/handoff'
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

    def test_custom_home_is_recorded_for_update_and_check(self):
        custom = self.root / 'custom Google home'
        self.install('--harness-home', f'antigravity={custom}')
        self.assertTrue((custom / 'AGENTS.md').is_file())
        self.assertFalse((self.home / '.gemini/AGENTS.md').exists())
        self.assertTrue((self.home / '.agents/skills/handoff').is_symlink())
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
        self.assertIn('adapter verified on 1.4.2', output)
        self.assertEqual(before, self.tree(self.home))

    def test_google_skill_locations_block_competing_names(self):
        for location in ['config/skills', 'skills', 'antigravity-cli/skills']:
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
        manifest = self.source / 'workbench.json'
        data = json.loads(manifest.read_text())
        data['default_harnesses'] = ['unknown']
        manifest.write_text(json.dumps(data))
        self.assertEqual(self.cli('validate')[0], 2)


if __name__ == '__main__':
    unittest.main()
