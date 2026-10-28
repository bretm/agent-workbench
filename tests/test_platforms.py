"""Platform gates use disposable homes; native behavior is exercised in CI."""
import contextlib
import io
import runpy
import sys
import unittest
from unittest.mock import patch

import test_installer as fixtures


class PlatformTests(unittest.TestCase):
    setUp = fixtures.InstallerTests.setUp
    tearDown = fixtures.InstallerTests.tearDown
    cli = fixtures.InstallerTests.cli
    tree = fixtures.InstallerTests.tree

    def entry(self, *args):
        output = io.StringIO()
        argv = [str(fixtures.SOURCE / 'awb.py'), *map(str, args),
                '--home', str(self.home), '--source', str(self.source)]
        with patch.object(sys, 'argv', argv), contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            with self.assertRaises(SystemExit) as result:
                runpy.run_path(argv[0], run_name='__main__')
        return result.exception.code, output.getvalue()

    def test_linux_and_macos_enter_cli_without_writes(self):
        before = self.tree(self.home)
        for platform in ['linux', 'darwin']:
            with self.subTest(platform=platform), patch.object(sys, 'platform', platform):
                for invoke in [self.entry, self.cli]:
                    code, output = invoke('validate')
                    self.assertEqual(code, 0, output)
                    self.assertIn('Valid:', output)
                    self.assertEqual(before, self.tree(self.home))

    def test_unsupported_platforms_fail_before_writes(self):
        before = self.tree(self.home)
        for platform in ['win32', 'freebsd14']:
            with self.subTest(platform=platform), patch.object(sys, 'platform', platform):
                for invoke in [self.entry, self.cli]:
                    code, output = invoke('install', '--apply')
                    self.assertEqual(code, 2, output)
                    self.assertEqual(before, self.tree(self.home))

    def test_old_python_fails_before_writes(self):
        before = self.tree(self.home)
        with patch.object(sys, 'version_info', (3, 10, 0)):
            for invoke in [self.entry, self.cli]:
                code, output = invoke('install', '--apply')
                self.assertEqual(code, 2, output)
                self.assertEqual(before, self.tree(self.home))


if __name__ == '__main__':
    unittest.main()
