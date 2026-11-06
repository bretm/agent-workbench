"""Shared agreements and closeout policy reach every manifest-selected client."""
import json
import os
import shlex
import unittest

import test_installer as fixtures
from workbench.cli import load_state


class AgreementDistributionTests(unittest.TestCase):
    setUp = fixtures.InstallerTests.setUp
    tearDown = fixtures.InstallerTests.tearDown
    cli = fixtures.InstallerTests.cli
    tree = fixtures.InstallerTests.tree

    def exercise_distribution(self):
        manifest = json.loads((self.source / 'workbench.json').read_text())
        adapters = {name: json.loads((self.source / 'adapters' / f'{name}.json').read_text())
                    for name in manifest['harnesses']}
        self.assertTrue(adapters)
        instructions = {}
        for name, adapter in adapters.items():
            # Probe only disposable stubs, including for clients absent locally.
            if adapter.get('home_environment'):
                os.environ.pop(adapter['home_environment'], None)
            executable = self.bin / adapter['executable']
            executable.write_text('#!/bin/sh\nprintf "%s\\n" '
                                  + shlex.quote(adapter['verified_version']) + '\n')
            executable.chmod(0o755)
            path = self.home / adapter['home_directory'] / adapter['instruction_file']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f'Existing preferences for {name}.\n')
            path.chmod(0o640)
            instructions[name] = path

        def assert_distributed(phase):
            state = load_state(self.state)
            self.assertCountEqual(state['harnesses'], adapters)
            release = self.state / 'releases' / state['content_hash']
            policy = release / 'reference/work-records.md'
            for name, path in instructions.items():
                with self.subTest(client=name, phase=phase):
                    rendered = path.read_text()
                    self.assertTrue(rendered.startswith(f'Existing preferences for {name}.\n'))
                    self.assertIn((self.source / manifest['agreements']).read_text(), rendered)
                    self.assertEqual([line for line in rendered.splitlines()
                                      if line.startswith('Work-record policy: ')],
                                     [f'Work-record policy: {policy}'])
                    self.assertEqual(policy.read_text(),
                                     (self.source / 'reference/work-records.md').read_text())
                    self.assertEqual(path.stat().st_mode & 0o777, 0o640)
                    if phase == 'update':
                        self.assertTrue(rendered.endswith(f'Later preferences for {name}.\n'))

        targets = [arg for name in adapters for arg in ('--harness', name)]
        before = self.tree(self.home)
        code, output = self.cli('install', *targets)
        self.assertEqual(code, 0, output)
        self.assertEqual(before, self.tree(self.home))
        code, output = self.cli('install', *targets, '--apply')
        self.assertEqual(code, 0, output)
        assert_distributed('install')
        self.assertEqual(self.cli('check')[0], 0)
        installed_hash = load_state(self.state)['content_hash']

        # Update both canonical sources so stale rules or policy pointers fail.
        for relative, revision in [(manifest['agreements'], 'Fixture agreement revision.'),
                                   ('reference/work-records.md', 'Fixture closeout revision.')]:
            path = self.source / relative
            path.write_text(path.read_text() + '\n' + revision + '\n')
        for name, path in instructions.items():
            path.write_text(path.read_text() + f'Later preferences for {name}.\n')
        self.assertEqual(self.cli('check')[0], 1)
        before = self.tree(self.home)
        code, output = self.cli('update')
        self.assertEqual(code, 0, output)
        self.assertEqual(before, self.tree(self.home))
        code, output = self.cli('update', '--apply')
        self.assertEqual(code, 0, output)
        self.assertNotEqual(installed_hash, load_state(self.state)['content_hash'])
        assert_distributed('update')
        self.assertEqual(self.cli('check')[0], 0)

    def test_all_supported_clients_receive_agreements_and_closeout_policy(self):
        self.exercise_distribution()

    def test_added_client_is_covered_without_changing_the_distribution_checks(self):
        path = self.source / 'workbench.json'
        manifest = json.loads(path.read_text())
        adapter = json.loads((self.source / 'adapters' / f'{manifest["harnesses"][0]}.json').read_text())
        adapter.update(executable='fixture-client', verified_version='1.2.3',
                       home_directory='.fixture-client', home_environment=None,
                       instruction_file='POLICY.md', skill_scope='harness', skill_directory='skills',
                       alternate_skill_directory=None, additional_skill_directories=[], shadow_files=[])
        adapter.pop('workflow_reset', None)
        (self.source / 'adapters/fixture-client.json').write_text(json.dumps(adapter))
        manifest['harnesses'].append('fixture-client')
        path.write_text(json.dumps(manifest))
        self.exercise_distribution()


if __name__ == '__main__':
    unittest.main()
