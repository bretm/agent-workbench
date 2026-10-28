"""Private context uses temporary homes and never reads the operator's profiles."""
from contextlib import redirect_stdout, redirect_stderr
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

from workbench import context, model_guidance as mg
from workbench.cli import main as cli
from workbench.planner import pack, validate

SOURCE = Path(__file__).resolve().parents[1]


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name).resolve()
        self.root = self.directory / 'private'
        self.data = {'schema': 1, 'assistants': ['fixture-client'], 'provider_order': ['fixture-provider']}

    def invoke(self, *args):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            result = cli(['context', *args, '--context-dir', str(self.root)])
        return result, output.getvalue()

    def test_update_preview_apply_backup_and_unknown(self):
        path = self.directory / 'input.json'
        path.write_text(json.dumps(self.data))
        self.assertIn('Unknown', self.invoke('show')[1])
        self.assertEqual(self.invoke('update', '--input', str(path))[0], 0)
        self.assertFalse(self.root.exists())
        self.assertEqual(self.invoke('update', '--input', str(path), '--apply')[0], 0)
        dest = self.root / 'context/models.json'
        self.assertEqual(json.loads(dest.read_text()), self.data)
        self.assertEqual(dest.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.root.stat().st_mode & 0o777, 0o700)
        self.assertIn('models.json', (self.root / 'context/INDEX.md').read_text())
        path.write_text(json.dumps({**self.data, 'provider_order': []}))
        self.invoke('update', '--input', str(path), '--apply')
        backup = list((self.root / 'backups').glob('*.json'))
        self.assertEqual(len(backup), 1)
        self.assertEqual(json.loads(backup[0].read_text()), self.data)

    def test_escaping_index_fails_before_saving_profile(self):
        (self.root / 'context').mkdir(parents=True)
        elsewhere = self.directory / 'outside.md'
        elsewhere.write_text('private notes')
        (self.root / 'context/INDEX.md').symlink_to(elsewhere)
        with self.assertRaises(ValueError):
            context.update_topic(self.root, 'models', self.data, True)
        self.assertFalse((self.root / 'context/models.json').exists())
        self.assertEqual(elsewhere.read_text(), 'private notes')

    def test_home_override_and_environment(self):
        with patch.dict(os.environ, {'AWB_CONTEXT_DIR': str(self.root)}):
            self.assertEqual(context.context_root(home=self.directory), self.root)
            explicit = self.directory / 'explicit'
            self.assertEqual(context.context_root(explicit), explicit)
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(context.context_root(home=self.directory), self.directory / '.agents/agent-workbench')

    def test_worktree_symlink_and_escape_rejected(self):
        repo = self.directory / 'repo'
        repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        with self.assertRaises(ValueError):
            context.context_root(repo / 'future/child')
        link = self.directory / 'link'
        link.symlink_to(repo, target_is_directory=True)
        with self.assertRaises(ValueError):
            context.context_root(link / 'child')
        self.root.mkdir()
        (self.root / 'context').symlink_to(repo, target_is_directory=True)
        with self.assertRaises(ValueError):
            context.update_topic(self.root, 'models', self.data, True)
        with self.assertRaises(ValueError):
            context.private_path(self.root, self.directory / 'escape')

    def test_invalid_data_does_not_write(self):
        for topic, data in [('models', {'schema': 1, 'access': 'bad'}),
                            ('../escape', self.data),
                            ('hardware', {'schema': 1, 'machines': [{'name': 'x', 'memory_gib': True}]}),
                            ('hardware', {'schema': 1, 'machines': [{'name': 'x', 'memory_gib': 8, 'reserve_gib': 8}]})]:
            with self.subTest(topic=topic), self.assertRaises(ValueError):
                context.update_topic(self.root, topic, data, True)
        self.assertFalse(self.root.exists())

    def test_setup_cancel_and_eof_do_not_write(self):
        # 9 model questions, add-hardware question, final confirmation.
        with patch.object(sys.stdin, 'isatty', return_value=True), patch('builtins.input', return_value=''):
            self.assertEqual(self.invoke('setup')[0], 0)
        self.assertFalse(self.root.exists())
        with patch.object(sys.stdin, 'isatty', return_value=True), patch('builtins.input', side_effect=EOFError):
            self.assertEqual(self.invoke('setup')[0], 2)
        self.assertFalse(self.root.exists())

    def test_setup_preserves_existing_unknown_fields_and_preferences(self):
        models = {**self.data, 'role_preferences': {'implementation': 'fixture-model/high'}, 'custom': 'keep'}
        context.update_topic(self.root, 'models', models, True)
        with patch.object(sys.stdin, 'isatty', return_value=True), patch('builtins.input', side_effect=[''] * 10 + ['y']):
            self.assertEqual(self.invoke('setup')[0], 0)
        self.assertEqual(json.loads((self.root / 'context/models.json').read_text()), {**models, 'access': [], 'rotation': '', 'role_preferences': {**models['role_preferences'], 'light': '', 'investigation': '', 'reasoning': '', 'visual': ''}})

    def test_migration_dates_conflicts_and_source_preservation(self):
        legacy = self.directory / 'legacy'
        legacy.mkdir()
        data = {'schema': 1, 'machines': [], 'observed_at': '2025-01-01'}
        source = legacy / 'model-hardware.json'
        source.write_text(json.dumps(data))
        self.assertEqual(self.invoke('migrate', '--from', str(legacy))[0], 0)
        self.assertFalse(self.root.exists())
        self.assertEqual(self.invoke('migrate', '--from', str(legacy), '--apply')[0], 0)
        self.assertEqual(json.loads((self.root / 'context/hardware.json').read_text()), data)
        self.assertIn('hardware.json', (self.root / 'context/INDEX.md').read_text())
        self.assertTrue(source.exists())
        source.write_text(json.dumps({**data, 'observed_at': '2025-01-02'}))
        self.assertEqual(self.invoke('migrate', '--from', str(legacy), '--apply')[0], 2)

    def test_installed_runtime_without_source_or_private_data(self):
        sentinel = 'PERSONAL-INVENTORY-DO-NOT-PUBLISH'
        context.update_topic(self.root, 'models', {**self.data, 'notes': sentinel}, True)
        files = pack(SOURCE, validate(SOURCE))
        self.assertFalse(any(sentinel in data for data in files.values()))
        release = self.directory / 'release'
        for rel, data in files.items():
            dest = release / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(data)
        result = subprocess.run([sys.executable, '-B', str(release / 'runtime/awb-local.py'), 'context', 'show', '--context-dir', str(self.root)], cwd=self.directory, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(sentinel, result.stdout)
        result = subprocess.run([sys.executable, '-B', str(release / 'runtime/awb-local.py'), 'models', '--help'], cwd=self.directory, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_model_output_rejected_before_fetch_for_worktree_and_symlink(self):
        repo = self.directory / 'repo'
        repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        link = self.directory / 'alias'
        link.symlink_to(repo, target_is_directory=True)
        for output in [repo / 'report.md', link / 'report.md']:
            with patch.object(mg, 'refresh', side_effect=AssertionError('must reject before fetch')), redirect_stderr(io.StringIO()):
                self.assertEqual(mg.main(['--context-dir', str(self.root), '--output', str(output)]), 2)
        self.assertFalse(self.root.exists())

    def test_refresh_defaults_stay_private_and_do_not_print_inventory(self):
        # Use the public-page fixture catalog, never the operator's cache.
        import test_model_guidance as fixtures
        context.update_topic(self.root, 'hardware', {'schema': 1, 'machines': [
            {'name': 'PRIVATE-FIXTURE-INVENTORY', 'memory_gib': 48, 'reserve_gib': 8}]}, True)
        cache = self.root / 'cache/artificial-analysis.json'
        context.write_private(cache, json.dumps(fixtures.snapshot()))
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            self.assertEqual(mg.main(['--context-dir', str(self.root), '--offline', '--apply']), 0)
        report = self.root / 'generated/model-guidance.md'
        self.assertIn('PRIVATE-FIXTURE-INVENTORY', report.read_text())
        self.assertNotIn('PRIVATE-FIXTURE-INVENTORY', output.getvalue())
        self.assertEqual(report.stat().st_mode & 0o777, 0o600)
        self.assertFalse(any('PRIVATE-FIXTURE-INVENTORY' in text for text in pack(SOURCE, validate(SOURCE)).values()))


if __name__ == '__main__':
    unittest.main()
