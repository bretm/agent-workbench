"""Default client detection uses only stub executables and disposable homes."""
import json
import unittest

import test_installer as fixtures
from workbench.cli import load_state


class DetectionTests(unittest.TestCase):
    tearDown = fixtures.InstallerTests.tearDown
    cli = fixtures.InstallerTests.cli
    config = fixtures.InstallerTests.config
    tree = fixtures.InstallerTests.tree

    def setUp(self):
        fixtures.InstallerTests.setUp(self)
        self.executables = {'codex': 'codex', 'claude': 'claude', 'antigravity': 'agy'}
        self.versions = {name: json.loads((self.source / 'adapters' / f'{name}.json').read_text())['verified_version']
                         for name in self.executables}

    def available(self, *names):
        for name, executable in self.executables.items():
            path = self.bin / executable
            if name in names:
                path.write_text('#!/bin/sh\nprintf "%s\\n" "' + self.versions[name] + '"\n')
                path.chmod(0o755)
            elif path.exists():
                path.unlink()

    def test_fresh_detection_configures_only_available_clients(self):
        combinations = [('codex',), ('claude',), ('antigravity',),
                        ('codex', 'claude'), ('codex', 'antigravity'),
                        ('claude', 'antigravity'), ('codex', 'claude', 'antigravity')]
        for index, names in enumerate(combinations):
            with self.subTest(clients=names):
                self.available(*names)
                self.home = self.root / f'home-{index}'
                self.home.mkdir()
                self.state = self.home / '.local/state/agent-workbench'
                before = self.tree(self.home)
                code, output = self.cli('install')
                self.assertEqual(code, 0, output)
                self.assertIn('DETECTED installed clients: ' + ', '.join(names), output)
                self.assertEqual(before, self.tree(self.home))
                code, output = self.cli('install', '--apply')
                self.assertEqual(code, 0, output)
                self.assertEqual(load_state(self.state)['harnesses'], list(names))
                for name, directory in [('codex', '.codex'), ('claude', '.claude'), ('antigravity', '.gemini')]:
                    self.assertEqual((self.home / directory).exists(), name in names)
                self.assertEqual(self.cli('check')[0], 0)

    def test_no_clients_fails_without_writes(self):
        self.available()
        before = self.tree(self.home)
        for command, args in [('install', []), ('install', ['--apply']),
                              ('update', ['--apply']), ('reset-workflow', ['--inventory'])]:
            with self.subTest(command=command, args=args):
                code, output = self.cli(command, *args)
                self.assertEqual(code, 2, output)
                self.assertIn('found on PATH', output)
                self.assertEqual(before, self.tree(self.home))

    def test_config_overrides_detection_and_flags_override_config(self):
        self.available('codex', 'claude', 'antigravity')
        config = self.config({'harnesses': ['codex']})
        code, output = self.cli('install', '--config', config, '--harness', 'claude', '--apply')
        self.assertEqual(code, 0, output)
        self.assertEqual(load_state(self.state)['harnesses'], ['claude'])
        self.assertFalse((self.home / '.codex').exists())
        self.assertFalse((self.home / '.gemini').exists())
        code, output = self.cli('install', '--config', config, '--apply')
        self.assertEqual(code, 0, output)
        self.assertEqual(load_state(self.state)['harnesses'], ['claude', 'codex'])
        self.assertFalse((self.home / '.gemini').exists())

    def test_explicit_missing_client_is_not_skipped(self):
        self.available('codex')
        before = self.tree(self.home)
        for args in [('--harness', 'claude'), ('--config', self.config({'harnesses': ['claude']}))]:
            with self.subTest(selection=args):
                code, output = self.cli('install', *args, '--apply')
                self.assertEqual(code, 2, output)
                self.assertIn('claude: not installed', output)
                self.assertEqual(before, self.tree(self.home))

    def test_detected_unverified_version_blocks_apply(self):
        self.available('codex', 'claude', 'antigravity')
        (self.bin / 'agy').write_text('#!/bin/sh\nprintf "999.0.0\\n"\n')
        before = self.tree(self.home)
        code, output = self.cli('install', '--apply')
        self.assertEqual(code, 2, output)
        self.assertIn('antigravity: adapter verified on', output)
        self.assertEqual(before, self.tree(self.home))

    def test_recorded_targets_do_not_expand_when_new_clients_appear(self):
        self.available('codex')
        self.assertEqual(self.cli('install', '--apply')[0], 0)
        self.available('codex', 'claude', 'antigravity')
        reference = self.source / 'agreements/working.md'
        reference.write_text(reference.read_text() + '\nFixture rule.\n')
        self.assertEqual(self.cli('check')[0], 1)
        for command in ['update', 'install']:
            code, output = self.cli(command, '--apply')
            self.assertEqual(code, 0, output)
            self.assertEqual(load_state(self.state)['harnesses'], ['codex'])
            self.assertFalse((self.home / '.claude').exists())
            self.assertFalse((self.home / '.gemini').exists())
        self.assertEqual(self.cli('check')[0], 0)

    def test_missing_recorded_client_still_blocks(self):
        self.available('codex')
        self.assertEqual(self.cli('install', '--apply')[0], 0)
        self.available('claude')
        before = self.tree(self.home)
        for command in ['check', 'update', 'install']:
            args = [] if command == 'check' else ['--apply']
            code, output = self.cli(command, *args)
            self.assertEqual(code, 2, output)
            self.assertIn('codex: not installed', output)
            self.assertEqual(before, self.tree(self.home))

    def test_reset_detection_is_capability_limited_and_review_freezes_targets(self):
        self.available('codex', 'antigravity')
        before = self.tree(self.home)
        code, output = self.cli('reset-workflow', '--inventory')
        self.assertEqual(code, 0, output)
        self.assertEqual(before, self.tree(self.home))
        review = json.loads(output)
        self.assertEqual(review['harnesses'], ['codex'])
        config = self.config(review)
        self.available('codex', 'claude', 'antigravity')
        code, output = self.cli('reset-workflow', '--config', config, '--apply')
        self.assertEqual(code, 0, output)
        self.assertEqual(load_state(self.state)['harnesses'], ['codex'])
        self.assertFalse((self.home / '.claude').exists())
        self.assertFalse((self.home / '.gemini').exists())

    def test_only_unsupported_reset_client_fails_without_writes(self):
        self.available('antigravity')
        before = self.tree(self.home)
        code, output = self.cli('reset-workflow', '--inventory')
        self.assertEqual(code, 2, output)
        self.assertIn('No supported agent clients with verified workflow-reset support found on PATH', output)
        self.assertEqual(before, self.tree(self.home))

    def test_custom_manifest_candidates_are_filtered_by_presence(self):
        self.available('codex', 'claude', 'antigravity')
        path = self.source / 'workbench.json'
        manifest = json.loads(path.read_text())
        manifest['default_harnesses'] = ['claude', 'antigravity']
        path.write_text(json.dumps(manifest))
        self.available('codex', 'antigravity')
        code, output = self.cli('install', '--apply')
        self.assertEqual(code, 0, output)
        self.assertEqual(load_state(self.state)['harnesses'], ['antigravity'])
        self.assertFalse((self.home / '.codex').exists())


if __name__ == '__main__':
    unittest.main()
