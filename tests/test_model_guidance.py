"""Model evidence refresh uses synthetic pages and disposable paths, never live clients."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from workbench import model_guidance as mg


def raw(slug, creator='OpenAI', **extra):
    return {'id': 'aa-' + slug, 'slug': slug, 'name': slug,
            'creator': {'name': creator}, 'releaseDate': '2026-10-20',
            'isOpenWeights': False, 'parameters': None, 'intelligenceIndex': 50,
            **extra}


def catalog():
    return [raw('sol'), raw('claude', 'Anthropic'), raw('gemini', 'Google'),
            raw('local', 'Other', isOpenWeights=True, parameters=27)]


def snapshot(records=None, **extra):
    return {'schema': 1, 'source': mg.MODELS_URL, 'fetched_at': '2026-10-20T12:00:00+00:00',
            'complete': True, 'models': list(map(mg.normalize, records or catalog())), **extra}


def page(records, split=False):
    payload = '28:["$","component",null,' + json.dumps({'initialModels': records}) + ']\n'
    chunks = [payload[:30], payload[30:]] if split else [payload]
    return '<html>' + ''.join('<script>self.__next_f.push(' + json.dumps([1, c]) + ')</script>' for c in chunks) + '</html>'


class ModelGuidanceTests(unittest.TestCase):
    def test_public_page_parser_handles_split_frames_without_executing_scripts(self):
        records = catalog()
        html = '<script>throw new Error("do not run")</script>' + page(records, split=True)
        self.assertEqual(mg.page_records(html), records)

    def test_public_page_reuses_concrete_catalog_records_for_react_references(self):
        records = catalog()
        payload = 'f:' + json.dumps({'currentModel': records[0], 'models': records[1:],
                                     'initialModels': ['$f:currentModel', '$f:models:0']})
        html = '<script>self.__next_f.push(' + json.dumps([1, payload]) + ')</script>'
        self.assertEqual(mg.page_records(html), records)
        self.assertEqual(mg.normalize(raw('QwQ-32B-Preview'))['slug'], 'QwQ-32B-Preview')

    def test_missing_or_truncated_public_data_fails(self):
        for html in ['<html>Blocked</html>', page([]), page(catalog()).replace('initialModels', 'newFormat')]:
            with self.subTest(html=html[:60]), self.assertRaises(mg.RefreshError):
                mg.page_records(html)

    def test_bad_source_values_remain_unknown_and_dates_and_slugs_are_checked(self):
        for value in [None, True, -1, float('nan'), float('inf'), '42']:
            with self.subTest(value=value):
                model = mg.normalize(raw('test', intelligenceIndex=value, parameters=value))
                self.assertIsNone(model['intelligence'])
                self.assertIsNone(model['parameters_billion'])
        self.assertEqual(mg.normalize(raw('zero', intelligenceIndex=0))['intelligence'], 0)
        for data in [raw('../bad'), raw('bad', releaseDate='not a date')]:
            with self.assertRaises(mg.RefreshError):
                mg.normalize(data)

    def test_detail_cost_object_and_estimated_score_are_preserved(self):
        model = mg.normalize(raw('sol', intelligenceIndexCostPerTask={'cost': {'total': 0.32}},
                                 intelligenceIndexIsEstimated=True))
        self.assertEqual(model['cost_per_task'], 0.32)
        doc = mg.render(snapshot([raw('sol', intelligenceIndexIsEstimated=True)] + catalog()[1:]), [])
        self.assertIn('| 50.0* |', doc)

    def test_local_estimate_uses_total_parameters_and_separate_budgets(self):
        machines = [{'name': 'workstation-a', 'memory_gib': 80, 'reserve_gib': 10},
                    {'name': 'workstation-b', 'memory_gib': 30, 'reserve_gib': 4},
                    {'name': 'unknown', 'memory_gib': None, 'reserve_gib': 4}]
        small = mg.normalize(raw('small', isOpenWeights=True, parameters=27))
        moe = mg.normalize(raw('moe', isOpenWeights=True, parameters=120, inferenceParametersActiveBillions=3))
        huge = mg.normalize(raw('huge', isOpenWeights=True, parameters=600, inferenceParametersActiveBillions=3))
        unknown = mg.normalize(raw('unknown', isOpenWeights=True))
        self.assertEqual(mg.local_machines(small, machines, 6), ['workstation-a', 'workstation-b'])
        self.assertEqual(mg.local_machines(small, machines, 8), ['workstation-a'])
        for bits in (6, 8):
            self.assertEqual(mg.local_machines(moe, machines, bits), [])
            self.assertEqual(mg.local_machines(huge, machines, bits), [])
            self.assertEqual(mg.local_machines(unknown, machines, bits), [])
        self.assertAlmostEqual(mg.weight_gib(27, 6), 21.6882, places=3)
        self.assertAlmostEqual(mg.weight_gib(27, 8), 28.9176, places=3)
        self.assertEqual(mg.local_machines(moe, machines, 16), [])

    def test_generated_evidence_preserves_handwritten_reference(self):
        before = '# Model guidance\n\nKeep verified pairs.\n'
        first = mg.replace_section(before, 'first')
        self.assertIn('Keep verified pairs.', first)
        generated = mg.START + '\nold\n' + mg.END
        before = '# Guidance\n\n' + generated + '\nUser notes.\n'
        after = mg.replace_section(before, mg.START + '\nnew\n' + mg.END)
        self.assertEqual(after, '# Guidance\n\n' + mg.START + '\nnew\n' + mg.END + '\nUser notes.\n')
        for text in [mg.START, mg.END, mg.END + mg.START, generated + generated]:
            with self.assertRaises(mg.RefreshError):
                mg.replace_section(text, 'new')

    def test_render_keeps_missing_scores_unknown_groups_variants_and_escapes_names(self):
        records = catalog() + [raw('local-low', 'Other', isOpenWeights=True, parameters=27,
                                   intelligenceIndex=None, release={'slug': 'local'}),
                               raw('unknown-size', 'Other', isOpenWeights=True, name='Unknown | <script>')]
        doc = mg.render(snapshot(records), [{'name': 'workstation-a', 'memory_gib': 80, 'reserve_gib': 10}])
        self.assertIn('Catalog checked 2026-10-20', doc)
        self.assertIn('1 release(s) meet', doc)
        self.assertNotIn('(https://artificialanalysis.ai/models/local-low)', doc)
        self.assertIn('Unknown &#124; &lt;script&gt;', doc)
        self.assertIn('unknown total parameter counts', doc)
        self.assertIn('not verified launch identifiers', doc)
        with self.assertRaises(mg.RefreshError):
            mg.render(snapshot(complete=False), [])

    def test_hardware_rejects_invalid_capacity_and_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'hardware.json'
            for machines in [[{'name': 'x', 'memory_gib': 30, 'reserve_gib': 32}],
                             [{'name': 'x', 'memory_gib': True}],
                             [{'name': 'x', 'memory_gib': 30}, {'name': 'x', 'memory_gib': 64}]]:
                path.write_text(json.dumps({'schema': 1, 'machines': machines}))
                with self.assertRaises(mg.RefreshError):
                    mg.load_hardware(path)

    def test_refresh_fetches_catalog_details_then_reuses_detail_cache(self):
        calls = []
        records = catalog()
        summaries = [{**r, 'releaseDate': None, 'parameters': None} for r in records]

        def fetch(url, timeout):
            calls.append(url)
            if url == mg.LEADERBOARD_URL:
                return summaries
            if url == mg.MODELS_URL:
                return [records[0]]
            return [r for r in records if url.endswith('/' + r['slug'])]

        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / 'cache.json'
            first = mg.refresh(cache, fetch=fetch)
            self.assertEqual(len(calls), 5)
            self.assertTrue(first['complete'])
            self.assertEqual(len(mg.load_snapshot(cache)['models']), 4)
            calls.clear()
            second = mg.refresh(cache, fetch=fetch)
            self.assertEqual(calls, [mg.LEADERBOARD_URL, mg.MODELS_URL])
            for a, b in zip(first['models'], second['models']):
                self.assertEqual({k: v for k, v in a.items() if k != 'detail_checked_at'},
                                 {k: v for k, v in b.items() if k != 'detail_checked_at'})

    def test_failed_detail_refresh_cannot_be_applied_offline_and_retry_reuses_successes(self):
        records = catalog()

        def fetch(url, timeout):
            if url == mg.LEADERBOARD_URL:
                return records
            if url == mg.MODELS_URL:
                return [records[0]]
            if url.endswith('/claude'):
                raise mg.RefreshError('HTTP 429')
            return [r for r in records if url.endswith('/' + r['slug'])]

        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / 'cache.json'
            with self.assertRaisesRegex(mg.RefreshError, '1 detail page'):
                mg.refresh(cache, fetch=fetch)
            saved = mg.load_snapshot(cache)
            self.assertFalse(saved['complete'])
            self.assertTrue(next(m for m in saved['models'] if m['slug'] == 'local')['detail_checked_at'])
            with self.assertRaises(mg.RefreshError):
                mg.render(saved, [])

    def test_embedded_catalog_avoids_redundant_detail_requests(self):
        calls = []
        records = catalog() + [raw(f'local-{i}', 'Other', isOpenWeights=True, parameters=8) for i in range(10)]
        def fetch(url, timeout):
            calls.append(url)
            if url == mg.MODELS_URL:
                return [records[0]]
            return records
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / 'cache.json'
            result = mg.refresh(cache, fetch=fetch, workers=1)
            self.assertTrue(result['complete'])
            self.assertEqual(len(calls), 3)
            self.assertEqual(len(result['models']), len(records))

    def test_fresh_catalog_score_overrides_cached_detail_score(self):
        records = catalog()
        old = snapshot()
        for m in old['models']:
            m['detail_checked_at'] = '2026-10-26T12:00:00+00:00'
        records[1]['intelligenceIndex'] = 55
        def fetch(url, timeout):
            return records if url == mg.LEADERBOARD_URL else [records[0]]
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / 'cache.json'
            cache.write_text(json.dumps(old))
            result = mg.refresh(cache, fetch=fetch, detail_max_age=1_000_000)
            self.assertEqual(next(m for m in result['models'] if m['slug'] == 'claude')['intelligence'], 55)

    def test_missing_provider_fails_before_cache_write(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / 'cache.json'
            with self.assertRaises(mg.RefreshError):
                mg.refresh(cache, fetch=lambda url, timeout: [catalog()[0]])
            self.assertFalse(cache.exists())

    def test_changed_detail_schema_fails_before_guidance_can_be_rendered(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / 'cache.json'
            def fetch(url, timeout):
                records = catalog()
                if url != mg.LEADERBOARD_URL:
                    for r in records:
                        r.pop('parameters')
                return records
            with self.assertRaisesRegex(mg.RefreshError, 'schema changed'):
                mg.refresh(cache, fetch=fetch)
            self.assertFalse(cache.exists())

    def test_cli_preview_apply_check_and_offline_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference, cache, hardware = [root / p for p in ('models.md', 'cache.json', 'hardware.json')]
            reference.write_text('# Reference\n\nKeep this guidance.\n')
            cache.write_text(json.dumps(snapshot()))
            hardware.write_text(json.dumps({'schema': 1, 'machines': []}))
            args = ['--reference', str(reference), '--cache', str(cache), '--hardware', str(hardware), '--offline']
            before = reference.read_bytes(), cache.read_bytes(), hardware.read_bytes()
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), patch.object(mg, 'fetch_page', side_effect=AssertionError('offline network access')):
                self.assertEqual(mg.main(args), 0)
                self.assertEqual(before, (reference.read_bytes(), cache.read_bytes(), hardware.read_bytes()))
                self.assertEqual(mg.main(args + ['--check']), 1)
                self.assertEqual(mg.main(args + ['--apply']), 0)
                self.assertEqual(mg.main(args + ['--check']), 0)
            self.assertIn('Keep this guidance.', reference.read_text())
            self.assertIn('Catalog checked 2026-10-20', reference.read_text())
            self.assertIn('Estimates assume 8-bit weights', reference.read_text())
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(mg.main(args + ['--bits', '6', '--apply']), 0)
                self.assertEqual(mg.main(args + ['--bits', '6', '--check']), 0)
                self.assertEqual(mg.main(args + ['--check']), 1)
            self.assertIn('Estimates assume 6-bit weights', reference.read_text())

    def test_cli_rejects_path_aliases_and_bad_markers_before_fetch(self):
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / 'models.md'
            reference.write_text(mg.START)
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), patch.object(mg, 'refresh', side_effect=AssertionError('unexpected fetch')):
                self.assertEqual(mg.main(['--reference', str(reference)]), 2)
                self.assertEqual(mg.main(['--reference', str(reference), '--cache', str(reference)]), 2)


if __name__ == '__main__':
    unittest.main()
