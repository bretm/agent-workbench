import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from workbench.cli import main, load_state
from workbench.planner import empty_state, installation
from workbench.storage import BEGIN, Conflict, file_value, write_value
from workbench.transactions import apply, locked, pending, restore

SOURCE = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='awb fixtures ')
        # macOS temporary roots may pass through /var -> /private/var.
        # Fixtures use real paths, just as destination ownership checks require.
        self.root = Path(self.temp.name).resolve()
        self.home = self.root / 'test home'
        self.home.mkdir()
        self.source = self.root / 'checkout'
        self.source.mkdir()
        for name in ['skills', 'reference', 'agreements', 'adapters', 'workbench', 'runtime']:
            shutil.copytree(SOURCE / name, self.source / name)
        for name in ['workbench.json', 'LICENSE']:
            shutil.copy2(SOURCE / name, self.source / name)
        self.state = self.home / '.local/state/agent-workbench'
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        (self.bin / 'git').symlink_to(shutil.which('git'))
        for name, version in [('codex', 'codex-cli 0.165.0'), ('claude', '2.1.301 (Claude Code)')]:
            p = self.bin / name
            p.write_text('#!/bin/sh\nprintf "%s\\n" "' + version + '"\n')
            p.chmod(0o755)
        env = {k: v for k, v in os.environ.items() if k not in ['CODEX_HOME', 'CLAUDE_CONFIG_DIR']}
        env['PATH'] = str(self.bin)
        self.env = patch.dict(os.environ, env, clear=True)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def cli(self, command, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = main([command, '--home', str(self.home), '--source', str(self.source), *map(str, args)])
        return code, out.getvalue()

    def install(self, *args):
        code, output = self.cli('install', '--harness', 'codex', '--apply', *args)
        self.assertEqual(code, 0, output)
        return output

    def repo(self, name):
        p = self.root / 'git' / name
        p.mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(p)], check=True)
        return p

    def config(self, data):
        p = self.root / 'local config.json'
        p.write_text(json.dumps(data))
        return p

    def tree(self, root):
        return {str(p.relative_to(root)): ('link', os.readlink(p)) if p.is_symlink()
                else ('file', p.read_bytes(), p.stat().st_mode) if p.is_file() else ('dir',)
                for p in root.rglob('*')}

    def test_clean_bootstrap_check_and_idempotence(self):
        self.install()
        self.assertTrue((self.home / '.agents/skills/plan-sessions/SKILL.md').is_file())
        self.assertIn('Personal working agreements', (self.home / '.codex/AGENTS.md').read_text())
        self.assertEqual(self.cli('check')[0], 0)
        before = self.tree(self.home)
        self.install()
        self.assertEqual(before, self.tree(self.home))

    def test_project_and_upstream_licenses_are_distributed(self):
        self.install()
        release = self.state / 'releases' / load_state(self.state)['content_hash']
        self.assertEqual((release / 'LICENSE').read_bytes(), (self.source / 'LICENSE').read_bytes())
        self.assertEqual((release / 'reference/upstream.md').read_bytes(),
                         (self.source / 'reference/upstream.md').read_bytes())
        upstream_licenses = list((self.source / 'reference').glob('*LICENSE*.txt'))
        self.assertTrue(upstream_licenses)
        for source in upstream_licenses:
            with self.subTest(license=source.name):
                self.assertEqual((release / 'reference' / source.name).read_bytes(), source.read_bytes())
        self.assertEqual(self.cli('check')[0], 0)

    def test_missing_project_license_blocks_validation_and_apply(self):
        (self.source / 'LICENSE').unlink()
        before = self.tree(self.home)
        for command, args in [('validate', []), ('install', ['--harness', 'codex', '--apply'])]:
            with self.subTest(command=command):
                code, output = self.cli(command, *args)
                self.assertEqual(code, 2, output)
                self.assertIn('missing canonical content LICENSE', output)
                self.assertEqual(before, self.tree(self.home))

    def test_add_harness_and_shared_snapshot(self):
        self.install()
        code, output = self.cli('install', '--harness', 'claude', '--apply')
        self.assertEqual(code, 0, output)
        for name in ['plan-sessions', 'handoff', 'grilling', 'wait-what']:
            self.assertEqual((self.home / '.agents/skills' / name).resolve(),
                             (self.home / '.claude/skills' / name).resolve())
        self.assertEqual(self.cli('check')[0], 0)
        self.assertEqual(len(list((self.state / 'releases').iterdir())), 1)

    def test_browser_skill_without_runtime_and_owned_removal(self):
        self.assertIsNone(shutil.which('playwright-cli'))
        self.assertIsNone(shutil.which('node'))
        self.assertIsNone(shutil.which('npm'))
        self.install('--harness', 'claude')
        for root in ['.agents/skills', '.claude/skills']:
            skill = self.home / root / 'playwright-cli'
            self.assertTrue(skill.is_symlink())
            self.assertTrue((skill / 'references/browser-commands.md').is_file())
            canonical = skill.resolve()
            self.assertTrue((canonical / '../../reference/PLAYWRIGHT-CLI-LICENSE.txt').resolve().is_file())
            self.assertTrue((canonical / '../../reference/upstream.md').resolve().is_file())
        self.assertEqual(self.cli('check')[0], 0)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        for root in ['.agents/skills', '.claude/skills']:
            self.assertFalse((self.home / root / 'playwright-cli').is_symlink())

    def test_design_skill_resources_install_without_optional_runtimes(self):
        self.assertIsNone(shutil.which('node'))
        self.assertIsNone(shutil.which('npm'))
        self.install('--harness', 'claude')
        resources = {
            'ui-ux-pro-max': ['scripts/search.py', 'data/stacks/swiftui.csv',
                              'references/quick-reference.md'],
            'design-taste-frontend': ['scripts/lib/cdp.mjs', 'library/app.json',
                                      'assets/charts.js', 'references/app-screens.md'],
        }
        for root in ['.agents/skills', '.claude/skills']:
            for name, files in resources.items():
                skill = self.home / root / name
                self.assertTrue(skill.is_symlink())
                for rel in files:
                    self.assertTrue((skill / rel).is_file(), rel)
        self.assertEqual(self.cli('check')[0], 0)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        for root in ['.agents/skills', '.claude/skills']:
            for name in resources:
                self.assertFalse((self.home / root / name).is_symlink())

    def test_installed_design_search_from_another_directory_preserves_release(self):
        self.install()
        skill = self.home / '.agents/skills/ui-ux-pro-max'
        before = self.tree(skill.resolve())
        for query, selector, value in [('error summary validation', '--domain', 'ux'),
                                       ('keyboard focus', '--stack', 'swiftui')]:
            result = subprocess.run(
                [sys.executable, str(skill / 'scripts/search.py'), query,
                 selector, value, '--json'], cwd=self.root,
                capture_output=True, text=True, timeout=20,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertGreater(data['count'], 0)
            self.assertEqual(data['stack' if selector == '--stack' else 'domain'], value)
        self.assertEqual(before, self.tree(skill.resolve()))
        self.assertEqual(self.cli('check')[0], 0)

    def test_explicit_repositories_discovery_unselected_unchanged(self):
        a, b, c = [self.repo(x) for x in ['repo one', 'repo two', 'unselected']]
        before = self.tree(c)
        code, output = self.cli('discover', '--root', self.root / 'git')
        self.assertEqual(code, 0, output)
        self.assertIn('unselected', output)
        self.install('--repo', a, '--repo', b)
        self.assertTrue((a / 'AGENTS.md').exists())
        self.assertTrue((b / 'AGENTS.md').exists())
        self.assertEqual(before, self.tree(c))

    def test_dry_run_has_no_changes_including_state(self):
        a = self.repo('project')
        before_home, before_repo = self.tree(self.home), self.tree(a)
        code, output = self.cli('install', '--harness', 'codex', '--repo', a, '--dry-run')
        self.assertEqual(code, 0, output)
        self.assertEqual(before_home, self.tree(self.home))
        self.assertEqual(before_repo, self.tree(a))

    def test_existing_instructions_and_permissions_preserved(self):
        p = self.home / '.codex/AGENTS.md'
        p.parent.mkdir()
        p.write_text('Keep project decisions local.\n')
        p.chmod(0o640)
        self.install()
        self.assertTrue(p.read_text().startswith('Keep project decisions local.\n'))
        self.assertEqual(p.stat().st_mode & 0o777, 0o640)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        self.assertEqual(p.read_text(), 'Keep project decisions local.\n')
        self.assertEqual(p.stat().st_mode & 0o777, 0o640)

    def test_conflicting_file_or_broken_link_blocks_all_changes(self):
        p = self.home / '.agents/skills/handoff'
        p.parent.mkdir(parents=True)
        p.symlink_to('/nonexistent/upstream/handoff')
        before = self.tree(self.home)
        code, output = self.cli('install', '--harness', 'codex', '--apply')
        self.assertEqual(code, 2, output)
        self.assertIn('explicit migration', output)
        self.assertEqual(before, self.tree(self.home))

    def test_no_adoption_even_identical_unowned_link(self):
        self.install()
        state = load_state(self.state)
        p = self.home / '.agents/skills/handoff'
        del state['entries'][str(p)]
        write_value(self.state / 'state.json', file_value(json.dumps(state), 0o600))
        self.assertEqual(self.cli('install', '--harness', 'codex', '--apply')[0], 2)

    def test_drift_in_managed_section_blocks_update_uninstall(self):
        self.install()
        p = self.home / '.codex/AGENTS.md'
        p.write_text(p.read_text().replace('Ask one question', 'Ask five questions'))
        before = self.tree(self.home)
        self.assertEqual(self.cli('update', '--apply')[0], 2)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 2)
        self.assertEqual(before, self.tree(self.home))

    def test_update_snapshot_and_rollback(self):
        self.install()
        p = self.home / '.agents/skills/handoff'
        old = os.readlink(p)
        ref = self.source / 'reference/models.md'
        ref.write_text(ref.read_text() + '\nReviewed model access.\n')
        self.assertEqual(self.cli('check')[0], 1)
        code, output = self.cli('update', '--apply')
        self.assertEqual(code, 0, output)
        self.assertNotEqual(os.readlink(p), old)
        self.assertEqual(self.cli('check')[0], 0)
        self.assertEqual(self.cli('rollback', '--apply')[0], 0)
        self.assertEqual(os.readlink(p), old)
        self.assertEqual(self.cli('check')[0], 1)

    def test_partial_failure_recovery(self):
        plan = installation(self.source, self.home, self.state, empty_state(), {}, ['codex'], [], {})
        before = self.tree(self.home)
        with locked(self.state):
            with self.assertRaises(OSError):
                apply(plan, self.state, fail_after=5)
        self.assertEqual(len(pending(self.state)), 1)
        self.assertEqual(self.cli('install', '--harness', 'codex', '--apply')[0], 2)
        self.assertEqual(self.cli('recover', '--dry-run')[0], 0)
        code, output = self.cli('recover', '--apply')
        self.assertEqual(code, 0, output)
        self.assertEqual(pending(self.state), [])
        self.assertFalse((self.home / '.agents/skills/handoff').is_symlink())
        self.assertFalse((self.home / '.codex/AGENTS.md').exists())
        self.install()

    def test_recovery_conflict_preserves_user_change(self):
        plan = installation(self.source, self.home, self.state, empty_state(), {}, ['codex'], [], {})
        with locked(self.state):
            with self.assertRaises(OSError):
                apply(plan, self.state, fail_after=1)
        p = Path(plan.operations[0]['path'])
        p.unlink()
        p.write_text('Subsequent user content')
        self.assertEqual(self.cli('recover', '--apply')[0], 2)
        self.assertEqual(p.read_text(), 'Subsequent user content')

    def test_rollback_and_uninstall_preserve_subsequent_outside_edits(self):
        self.install()
        p = self.home / '.codex/AGENTS.md'
        p.write_text(p.read_text() + '\nUser adds project preference.\n')
        code, output = self.cli('rollback', '--apply')
        self.assertEqual(code, 0, output)
        self.assertIn('User adds project preference.', p.read_text())
        self.assertNotIn(BEGIN, p.read_text())
        self.install()
        p.write_text(p.read_text() + '\nAnother user preference.\n')
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        self.assertIn('Another user preference.', p.read_text())
        self.assertNotIn(BEGIN, p.read_text())

    def test_worktree_path_with_spaces(self):
        repo = self.repo('main checkout')
        subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                        'commit', '-q', '--allow-empty', '-m', 'fixture'], check=True)
        tree = self.root / 'linked worktree'
        subprocess.run(['git', '-C', str(repo), 'worktree', 'add', '-q', '-b', 'fixture', str(tree)], check=True)
        self.install('--repo', tree)
        self.assertTrue((tree / 'AGENTS.md').exists())
        self.assertFalse((repo / 'AGENTS.md').exists())

    def test_project_compatibility_import_and_symlink_not_adopted(self):
        a, b = self.repo('with import'), self.repo('with symlink')
        (a / 'CLAUDE.md').write_text('@AGENTS.md\nAdditional local rules.\n')
        (b / 'AGENTS.md').write_text('Existing policy.\n')
        (b / 'CLAUDE.md').symlink_to('AGENTS.md')
        before = (a / 'CLAUDE.md').read_text()
        code, output = self.cli('install', '--harness', 'claude', '--repo', a, '--repo', b, '--apply')
        self.assertEqual(code, 0, output)
        self.assertEqual((a / 'CLAUDE.md').read_text(), before)
        self.assertTrue((b / 'CLAUDE.md').is_symlink())
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        self.assertTrue((b / 'CLAUDE.md').is_symlink())
        self.assertEqual((a / 'CLAUDE.md').read_text(), before)

    def test_explicit_exact_link_migration_and_restoration(self):
        directory = self.home / '.agents/skills'
        directory.mkdir(parents=True)
        (directory / 'grilling').symlink_to('/upstream/grilling')
        (directory / 'grill-me').symlink_to('/upstream/grill-me')
        config = self.config({'migrations': [
            {'path': str(directory / 'grilling'), 'action': 'replace', 'target': '/upstream/grilling'},
            {'path': str(directory / 'grill-me'), 'action': 'retire', 'target': '/upstream/grill-me'}]})
        self.install('--config', config)
        self.assertFalse((directory / 'grill-me').is_symlink())
        self.install('--config', config)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        self.assertEqual(os.readlink(directory / 'grilling'), '/upstream/grilling')
        self.assertEqual(os.readlink(directory / 'grill-me'), '/upstream/grill-me')

    def test_migration_wrong_target_and_arbitrary_path_rejected(self):
        p = self.home / '.agents/skills/handoff'
        p.parent.mkdir(parents=True)
        p.symlink_to('/upstream/handoff')
        config = self.config({'migrations': [{'path': str(p), 'action': 'replace', 'target': '/wrong'}]})
        self.assertEqual(self.cli('install', '--harness', 'codex', '--config', config, '--apply')[0], 2)
        config = self.config({'migrations': [{'path': str(self.home / 'other'), 'action': 'retire', 'target': '/x'}]})
        self.assertEqual(self.cli('install', '--harness', 'codex', '--config', config, '--apply')[0], 2)

    def test_project_config_exception_and_unresolved_conflict(self):
        repo = self.repo('document owned work')
        config = self.config({'harnesses': ['codex'], 'repositories': [
            {'path': str(repo), 'facts': {'documentation': ['existing/docs'], 'exceptions': ['Work status stays in docs/work.md']},
             'policy_conflicts': ['Two active status owners']}]})
        self.assertEqual(self.cli('install', '--config', config, '--apply')[0], 2)
        self.assertFalse((repo / 'AGENTS.md').exists())
        data = json.loads(config.read_text())
        del data['repositories'][0]['policy_conflicts']
        config.write_text(json.dumps(data))
        self.assertEqual(self.cli('install', '--config', config, '--apply')[0], 0)
        self.assertIn('Work status stays', (repo / '.agent-workbench.json').read_text())

    def test_override_and_symlinked_parent_block(self):
        p = self.home / '.codex/AGENTS.override.md'
        p.parent.mkdir()
        p.write_text('Temporary overrides')
        self.assertEqual(self.cli('install', '--harness', 'codex', '--apply')[0], 2)
        p.unlink()
        elsewhere = self.root / 'elsewhere'
        elsewhere.mkdir()
        (self.home / '.agents').symlink_to(elsewhere)
        self.assertEqual(self.cli('install', '--harness', 'codex', '--apply')[0], 2)
        self.assertEqual(list(elsewhere.iterdir()), [])

    def test_missing_harness_actionable_and_no_mutations(self):
        (self.bin / 'codex').unlink()
        with patch('workbench.planner.shutil.which', return_value=None):
            code, output = self.cli('install', '--harness', 'codex', '--apply')
        self.assertEqual(code, 2)
        self.assertIn('no automatic installation', output)
        self.assertFalse(self.state.exists())

    def test_version_mismatch_blocks_apply(self):
        (self.bin / 'codex').write_text('#!/bin/sh\necho "codex-cli 0.1.0"\n')
        self.assertEqual(self.cli('install', '--harness', 'codex', '--apply')[0], 2)

    def test_snapshot_drift_blocks_link_update(self):
        self.install()
        p = self.home / '.agents/skills/handoff/SKILL.md'
        p.write_text(p.read_text() + '\nLocal adaptation\n')
        self.assertEqual(self.cli('check')[0], 2)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 2)

    def test_unowned_project_config_conflict(self):
        repo = self.repo('existing facts')
        (repo / '.agent-workbench.json').write_text('{"test":"existing"}')
        self.assertEqual(self.cli('install', '--harness', 'codex', '--repo', repo, '--apply')[0], 2)
        self.assertFalse((repo / 'AGENTS.md').exists())

    def test_validate_missing_dependency_and_reference(self):
        self.assertEqual(self.cli('validate')[0], 0)
        (self.source / 'reference/models.md').unlink()
        self.assertNotEqual(self.cli('validate')[0], 0)

    def test_read_only_commands_reject_apply(self):
        self.assertEqual(self.cli('discover', '--apply')[0], 2)
        self.assertEqual(self.cli('validate', '--apply')[0], 2)

    def test_stale_plan_cannot_overwrite_new_file(self):
        plan = installation(self.source, self.home, self.state, empty_state(), {}, ['codex'], [], {})
        p = self.home / '.codex/AGENTS.md'
        p.parent.mkdir()
        p.write_text('Created after preview')
        with locked(self.state), self.assertRaises(Conflict):
            apply(plan, self.state)
        self.assertEqual(p.read_text(), 'Created after preview')

    def test_config_and_authentication_files_unchanged(self):
        p = self.home / '.codex/config.toml'
        p.parent.mkdir()
        p.write_text('model = "fixture"\n')
        auth = self.home / '.codex/auth.json'
        auth.write_text('fixture sentinel, not a credential')
        self.install()
        self.assertEqual(p.read_text(), 'model = "fixture"\n')
        self.assertEqual(auth.read_text(), 'fixture sentinel, not a credential')

    def test_uninstall_preserves_user_edit_absorbed_by_update(self):
        self.install()
        p = self.home / '.codex/AGENTS.md'
        p.write_text('User prefix.\n' + p.read_text() + '\nUser suffix.\n')
        ref = self.source / 'agreements/working.md'
        ref.write_text(ref.read_text() + '\nUpdated canonical rules.\n')
        self.assertEqual(self.cli('update', '--apply')[0], 0)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        self.assertIn('User prefix.', p.read_text())
        self.assertIn('User suffix.', p.read_text())
        self.assertNotIn(BEGIN, p.read_text())

    def test_removed_desired_skill_and_rollback(self):
        self.install()
        manifest = json.loads((self.source / 'workbench.json').read_text())
        del manifest['skills']['wait-what']
        (self.source / 'workbench.json').write_text(json.dumps(manifest))
        code, output = self.cli('update', '--apply')
        self.assertEqual(code, 0, output)
        self.assertFalse((self.home / '.agents/skills/wait-what').is_symlink())
        self.assertEqual(self.cli('check')[0], 0)
        self.assertEqual(self.cli('rollback', '--apply')[0], 0)
        self.assertTrue((self.home / '.agents/skills/wait-what/SKILL.md').is_file())

    def test_future_adapter_data_uses_same_core(self):
        adapter = json.loads((self.source / 'adapters/codex.json').read_text())
        adapter.update(home_directory='.fixture-agent', skill_directory='.fixture-agent/skills')
        (self.source / 'adapters/fixture-agent.json').write_text(json.dumps(adapter))
        manifest = json.loads((self.source / 'workbench.json').read_text())
        manifest['harnesses'].append('fixture-agent')
        (self.source / 'workbench.json').write_text(json.dumps(manifest))
        code, output = self.cli('install', '--harness', 'fixture-agent', '--apply')
        self.assertEqual(code, 0, output)
        self.assertTrue((self.home / '.fixture-agent/skills/handoff/SKILL.md').is_file())
        self.assertTrue((self.home / '.fixture-agent/AGENTS.md').is_file())

    def test_duplicate_skill_metadata_and_project_names_block(self):
        directory = self.home / '.agents/skills/other-folder'
        directory.mkdir(parents=True)
        (directory / 'SKILL.md').write_text('---\nname: handoff\ndescription: A competing handoff\n---\n')
        self.assertEqual(self.cli('install', '--harness', 'codex', '--apply')[0], 2)
        shutil.rmtree(directory)
        repo = self.repo('local workflow')
        directory = repo / '.agents/skills/grilling'
        directory.mkdir(parents=True)
        (directory / 'SKILL.md').write_text('---\nname: grilling\ndescription: Project probing\n---\n')
        self.assertEqual(self.cli('install', '--harness', 'codex', '--repo', repo, '--apply')[0], 2)
        self.assertFalse((repo / 'AGENTS.md').exists())

    def test_configurable_harness_home_roundtrip(self):
        custom = self.root / 'custom codex home'
        self.install('--harness-home', 'codex=' + str(custom))
        self.assertTrue((custom / 'AGENTS.md').exists())
        self.assertFalse((self.home / '.codex/AGENTS.md').exists())
        self.assertEqual(self.cli('check')[0], 0)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        self.assertFalse((custom / 'AGENTS.md').exists())

    def test_missing_local_config_never_selects_defaults(self):
        code, output = self.cli('install', '--config', self.root / 'missing.json', '--apply')
        self.assertEqual(code, 2, output)
        self.assertFalse(self.state.exists())

    def test_partial_update_recovery_restores_previous_installation(self):
        self.install()
        state = load_state(self.state)
        p = self.home / '.agents/skills/plan-sessions'
        old_target = os.readlink(p)
        rules = self.source / 'agreements/working.md'
        rules.write_text(rules.read_text() + '\nReviewed update.\n')
        plan = installation(self.source, self.home, self.state, state, {}, ['codex'], [], {})
        with locked(self.state), self.assertRaises(OSError):
            apply(plan, self.state, fail_after=2)
        self.assertNotEqual(os.readlink(p), old_target)
        self.assertEqual(self.cli('recover', '--apply')[0], 0)
        self.assertEqual(os.readlink(p), old_target)
        self.assertEqual(load_state(self.state), state)

    def test_uninstall_does_not_require_healthy_canonical_source_or_harness(self):
        self.install()
        (self.source / 'reference/models.md').unlink()
        with patch('workbench.planner.shutil.which', return_value=None):
            code, output = self.cli('uninstall', '--apply')
        self.assertEqual(code, 0, output)
        self.assertFalse((self.home / '.agents/skills/handoff').is_symlink())

    def test_unknown_configuration_and_empty_harness_list_block(self):
        for data in [{'harneses': ['codex']}, {'harnesses': []}]:
            config = self.config(data)
            self.assertEqual(self.cli('install', '--config', config, '--apply')[0], 2)
            self.assertFalse(self.state.exists())

    def test_interactive_confirmation_is_one_question(self):
        with patch('sys.stdin.isatty', return_value=True), patch('builtins.input', return_value='y') as question:
            code, output = self.cli('install', '--harness', 'codex', '--interactive')
        self.assertEqual(code, 0, output)
        question.assert_called_once()
        self.assertTrue((self.home / '.agents/skills/plan-sessions').is_symlink())

    def test_failure_after_state_commit_still_recovers(self):
        import workbench.transactions as transactions
        plan = installation(self.source, self.home, self.state, empty_state(), {}, ['codex'], [], {})
        real_save = transactions.save
        def fail_completion(path, data):
            if data.get('status') == 'complete':
                raise OSError('injected completion journal failure')
            real_save(path, data)
        with locked(self.state), patch('workbench.transactions.save', side_effect=fail_completion), self.assertRaises(OSError):
            apply(plan, self.state)
        self.assertTrue((self.home / '.agents/skills/handoff').is_symlink())
        self.assertEqual(self.cli('recover', '--apply')[0], 0)
        self.assertFalse((self.home / '.agents/skills/handoff').is_symlink())

    def test_rollback_changed_owned_link_is_a_conflict(self):
        self.install()
        p = self.home / '.agents/skills/handoff'
        p.unlink()
        p.symlink_to('/user/subsequent/handoff')
        code, output = self.cli('rollback', '--apply')
        self.assertEqual(code, 2, output)
        self.assertEqual(os.readlink(p), '/user/subsequent/handoff')


    def test_private_context_pointer_runtime_and_lifecycle(self):
        private = self.home / '.agents/agent-workbench'
        private.mkdir(parents=True)
        marker = private / 'user-owned.json'
        marker.write_text('PRIVATE-FIXTURE-KEEP')
        self.install()
        rules = (self.home / '.codex/AGENTS.md').read_text()
        self.assertIn(str(private), rules)
        state = load_state(self.state)
        self.assertEqual(state['context_dir'], str(private))
        self.assertFalse(any('PRIVATE-FIXTURE-KEEP' in p.read_text() for p in (self.state / 'releases').rglob('*') if p.is_file()))
        helper = next((self.state / 'releases').glob('*/runtime/awb-local.py'))
        result = subprocess.run([sys.executable, '-B', str(helper), 'context', 'show', '--context-dir', str(private)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.cli('update', '--apply')[0], 0)
        self.assertEqual(self.cli('uninstall', '--apply')[0], 0)
        self.assertEqual(marker.read_text(), 'PRIVATE-FIXTURE-KEEP')

    def test_context_root_override_is_recorded_and_environment_can_change_it(self):
        private = self.root / 'external-context'
        self.install('--context-dir', str(private))
        self.assertEqual(load_state(self.state)['context_dir'], str(private))
        self.assertEqual(self.cli('update', '--apply')[0], 0)
        self.assertEqual(load_state(self.state)['context_dir'], str(private))
        another = self.root / 'another-context'
        with patch.dict(os.environ, {'AWB_CONTEXT_DIR': str(another)}):
            self.assertEqual(self.cli('update', '--apply')[0], 0)
        self.assertEqual(load_state(self.state)['context_dir'], str(another))

if __name__ == '__main__':
    unittest.main()
