import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1]
NODE = shutil.which('node')


class PortableEntrypointTests(unittest.TestCase):
    def test_selected_skill_bodies_fit_antigravity_native_limit(self):
        manifest = json.loads((SOURCE / 'workbench.json').read_text())
        for name in manifest['skills']:
            with self.subTest(skill=name):
                body = (SOURCE / 'skills' / name / 'SKILL.md').read_text().split('---', 2)[2]
                self.assertLessEqual(len(body.encode('utf-8')), 24000,
                                     'Antigravity truncates skill bodies above 24000 bytes')


@unittest.skipUnless(NODE, 'Taste helper verification requires an existing Node runtime')
class TasteOutputTests(unittest.TestCase):
    def test_page_and_app_draws_keep_history_in_selected_output(self):
        script = SOURCE / 'skills/design-taste-frontend/scripts/draw.mjs'
        env = dict(os.environ)
        env.pop('TASTE_SKILL_HISTORY', None)
        with tempfile.TemporaryDirectory(prefix='awb taste ') as temp:
            root = Path(temp)
            for mode, args in [('page', ['--sector', 'saas', '--sections', 'features,footer']),
                               ('app', ['--app', '--kind', 'workspace'])]:
                with self.subTest(mode=mode):
                    output = root / mode
                    result = subprocess.run(
                        [NODE, str(script), *args, '--brief', 'A project planning tool',
                         '--seed', '42', '--out', str(output)],
                        cwd=root, env=env, capture_output=True, text=True, timeout=20,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    sheet = json.loads((output / 'direction.json').read_text())
                    self.assertEqual(sheet['seed'], 42)
                    self.assertTrue((output / 'history.json').is_file())
                    self.assertTrue(json.loads((output / 'history.json').read_text()))
                    self.assertFalse((root / '.taste-skill').exists())
