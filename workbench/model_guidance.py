"""Refresh benchmark evidence without changing verified launch settings.

Run with ``python3 -m workbench.model_guidance --help``. Standard library only.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
import difflib
from html import escape
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

from .context import context_root, outside_git, private_path, write_private


BASE = 'https://artificialanalysis.ai'
MODELS_URL = BASE + '/models'
LEADERBOARD_URL = BASE + '/leaderboards/models'
START = '<!-- artificial-analysis:begin -->'
END = '<!-- artificial-analysis:end -->'
PROVIDERS = ('OpenAI', 'Anthropic', 'Google')
SLUG = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*\Z')
USER_AGENT = 'agent-workbench-model-guidance/1.0'


class RefreshError(ValueError):
    """Source data cannot safely replace the current evidence."""


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.active = False
        self.current = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.active = True
            self.current = []

    def handle_data(self, data):
        if self.active:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.scripts.append(''.join(self.current))
            self.active = False


def page_records(html):
    """Read public server-rendered records; never execute page JavaScript."""
    parser = Scripts()
    parser.feed(html)
    chunks = []
    for script in parser.scripts:
        match = re.fullmatch(r'\s*self\.__next_f\.push\((.*)\);?\s*', script, re.S)
        if not match:
            continue
        try:
            frame = json.loads(match[1])
        except ValueError as exc:
            raise RefreshError('Artificial Analysis changed its page data encoding') from exc
        if isinstance(frame, list) and len(frame) > 1 and frame[0] == 1 and isinstance(frame[1], str):
            chunks.append(frame[1])
    stream = ''.join(chunks)
    records = {}
    decoder = json.JSONDecoder()
    for match in re.finditer(r'"(initialModels|models|currentModel)"\s*:\s*(?=[\[{])', stream):
        try:
            values, _ = decoder.raw_decode(stream[match.end():])
        except ValueError as exc:
            raise RefreshError('Artificial Analysis returned incomplete model data') from exc
        if match[1] == 'currentModel':
            values = [values]
        # React may reference objects serialized elsewhere on this same public page.
        # Read their concrete model objects, without evaluating JS or following paths.
        concrete = [v for v in values if isinstance(v, dict) and {'slug', 'name', 'isOpenWeights'} <= v.keys()]
        if not concrete and match[1] == 'initialModels' and not all(isinstance(v, str) and v.startswith('$') for v in values):
            raise RefreshError('Artificial Analysis returned an invalid model list')
        for model in concrete:
            records[model['slug']] = {**records.get(model['slug'], {}), **model}
    if not records:
        raise RefreshError('No public model records found; page format may have changed')
    return list(records.values())


def number(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0:
        return value
    return None


def normalize(raw):
    if not isinstance(raw, dict):
        raise RefreshError('Model record must be an object')
    slug = raw.get('slug')
    name = raw.get('name')
    creator_info = raw.get('creator') or {}
    if not isinstance(creator_info, dict):
        raise RefreshError('Model creator must be an object')
    creator = creator_info.get('name') or raw.get('modelCreatorName')
    if not isinstance(slug, str) or not SLUG.fullmatch(slug) or not isinstance(name, str) or not name.strip() or not isinstance(creator, str):
        raise RefreshError('Model record is missing a valid slug, name or creator')
    release = raw.get('release') or {}
    if not isinstance(release, dict):
        raise RefreshError(f'Invalid release metadata for {slug}')
    release_date = raw.get('releaseDate')
    if release_date is not None:
        try:
            date.fromisoformat(release_date)
        except (TypeError, ValueError) as exc:
            raise RefreshError(f'Invalid release date for {slug}') from exc
    cost_per_task = raw.get('intelligenceIndexCostPerTask')
    if isinstance(cost_per_task, dict):
        cost_per_task = (cost_per_task.get('cost') or {}).get('total')
    return {
        'id': raw.get('id'), 'slug': slug, 'name': name, 'creator': creator,
        'release': release.get('slug') or slug, 'release_date': release_date,
        'deprecated': raw.get('deprecated') is True,
        'open_weights': raw.get('isOpenWeights') is True,
        'parameters_billion': number(raw.get('parameters')),
        'active_parameters_billion': number(raw.get('inferenceParametersActiveBillions')),
        'intelligence': number(raw.get('intelligenceIndex')),
        'estimated_score': raw.get('intelligenceIndexIsEstimated') is True,
        'context_tokens': number(raw.get('contextWindowTokens')),
        'cost_per_task': number(cost_per_task),
        'input_price': number(raw.get('price1mInputTokens')),
        'output_price': number(raw.get('price1mOutputTokens')),
        'weights_url': raw.get('modelWeightsSourceUrl'),
        'license': raw.get('licenseName'),
    }


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise RefreshError(f'Cannot read JSON from {path}: {exc}') from exc


def atomic_write(path, content):
    write_private(path, content)


def fetch_page(url, timeout):
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content = response.read(16 * 1024 * 1024 + 1)
    except urllib.error.HTTPError as exc:
        raise RefreshError(f'{url}: HTTP {exc.code}') from exc
    except (OSError, urllib.error.URLError) as exc:
        raise RefreshError(f'{url}: {exc}') from exc
    if len(content) > 16 * 1024 * 1024:
        raise RefreshError(f'{url}: page exceeds 16 MiB limit')
    try:
        return page_records(content.decode('utf-8'))
    except UnicodeError as exc:
        raise RefreshError(f'{url}: page is not UTF-8') from exc


def in_scope(model):
    return not model['deprecated'] and (model['creator'] in PROVIDERS or model['open_weights'])


def validate_coverage(models):
    if not models:
        raise RefreshError('Catalog is empty')
    creators = {m['creator'] for m in models if not m['deprecated'] and not m['open_weights']}
    missing = set(PROVIDERS) - creators
    if missing or not any(m['open_weights'] and not m['deprecated'] for m in models):
        raise RefreshError('Incomplete catalog: require OpenAI, Anthropic, Google and open weights')
    if len({m['slug'] for m in models}) != len(models):
        raise RefreshError('Catalog has duplicate model slugs')


def load_snapshot(path):
    snapshot = read_json(path)
    if not isinstance(snapshot, dict) or snapshot.get('schema') != 1 or snapshot.get('source') != MODELS_URL:
        raise RefreshError('Unrecognized Artificial Analysis cache schema or source')
    try:
        fetched = datetime.fromisoformat(snapshot['fetched_at'])
        if fetched.tzinfo is None:
            raise ValueError('timestamp needs timezone')
        models = snapshot['models']
        if not isinstance(models, list):
            raise ValueError('models must be a list')
        for m in models:
            if not isinstance(m, dict) or not isinstance(m.get('slug'), str) or not SLUG.fullmatch(m['slug']):
                raise ValueError('invalid cached model')
            for field in ('name', 'creator', 'release'):
                if not isinstance(m[field], str):
                    raise ValueError(f'invalid {field}')
            for field in ('open_weights', 'deprecated', 'estimated_score'):
                if type(m[field]) is not bool:
                    raise ValueError(f'invalid {field}')
            for field in ('parameters_billion', 'intelligence', 'cost_per_task', 'context_tokens', 'input_price', 'output_price'):
                if m[field] is not None and number(m[field]) is None:
                    raise ValueError(f'invalid {field}')
            if m['release_date'] is not None:
                date.fromisoformat(m['release_date'])
        validate_coverage(models)
    except (KeyError, TypeError, ValueError) as exc:
        raise RefreshError(f'Invalid Artificial Analysis cache: {exc}') from exc
    return snapshot


def refresh(cache, timeout=30, workers=4, detail_max_age=24, fetch=fetch_page, progress=None):
    now = datetime.now(timezone.utc)
    old = load_snapshot(cache) if cache.exists() else {'models': []}
    cached = {m['slug']: m for m in old['models']}
    # Both source pages are fetched on every online run. Detail metadata is cached.
    summary = {m['slug']: m for m in map(normalize, fetch(LEADERBOARD_URL, timeout))}
    def detail_model(raw):
        if not {'parameters', 'releaseDate', 'isOpenWeights', 'intelligenceIndex'} <= raw.keys():
            raise RefreshError('Model detail schema changed; expected size, date, weights and score fields')
        return normalize(raw)

    featured = {m['slug']: m for m in map(detail_model, fetch(MODELS_URL, timeout))}
    validate_coverage(list(summary.values()))
    if len(summary) < len(cached) / 2:
        raise RefreshError('Catalog shrank by more than half; inspect source coverage before replacing the cache')
    result = dict(summary)
    pending = []
    cutoff = now - timedelta(hours=detail_max_age)
    for slug, model in summary.items():
        if not in_scope(model):
            continue
        previous = featured.get(slug) or cached.get(slug)
        checked = previous.get('detail_checked_at') if previous else None
        try:
            fresh = checked is not None and datetime.fromisoformat(checked) >= cutoff
        except (TypeError, ValueError):
            fresh = False
        if slug in featured:
            previous['detail_checked_at'] = now.isoformat()
            fresh = True
        if fresh:
            # The catalog's fresh scores/prices take precedence over cached detail metadata.
            result[slug] = {**previous, **{key: model[key] for key in (
                'intelligence', 'estimated_score', 'input_price', 'output_price',
                'context_tokens', 'deprecated', 'open_weights')}}
        else:
            pending.append(slug)
    if progress:
        progress(f'{len(summary)} catalog records; fetching {len(pending)} detail pages ({workers} workers)')
    errors = {}
    remaining = list(pending)
    fetched_pages = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        while remaining:
            batch, remaining = remaining[:workers], remaining[workers:]
            jobs = {executor.submit(fetch, MODELS_URL + '/' + slug, timeout): slug for slug in batch}
            for job in as_completed(jobs):
                slug = jobs[job]
                fetched_pages += 1
                try:
                    details = {m['slug']: m for m in map(detail_model, job.result())}
                    if slug not in details:
                        raise RefreshError(f'Detail page does not contain {slug}')
                    # Some detail pages embed the full catalog for their comparison picker.
                    # Reuse it rather than fetching a separate page for every model.
                    for key, model in details.items():
                        if key in pending:
                            model['detail_checked_at'] = now.isoformat()
                            result[key] = model
                            errors.pop(key, None)
                except (RefreshError, OSError, ValueError, TypeError, KeyError) as exc:
                    if 'detail_checked_at' not in result[slug]:
                        errors[slug] = str(exc)
            remaining = [slug for slug in remaining if 'detail_checked_at' not in result[slug]]
            if progress:
                progress(f'Fetched {fetched_pages} detail pages; {len(remaining)} models still need metadata')
    # Save successful detail fetches for a retry, but never replace guidance after a failed fetch.
    snapshot = {'schema': 1, 'source': MODELS_URL, 'fetched_at': now.isoformat(),
                'complete': not errors, 'models': sorted(result.values(), key=lambda m: m['slug'])}
    atomic_write(cache, json.dumps(snapshot, indent=2, ensure_ascii=False) + '\n')
    if errors:
        raise RefreshError(f'{len(errors)} detail page(s) failed; guidance unchanged. Retry to reuse cached successes.\n' + '\n'.join(f'{slug}: {error}' for slug, error in list(errors.items())[:10]))
    return snapshot


def load_hardware(path):
    config = read_json(path)
    if not isinstance(config, dict) or config.get('schema') != 1 or not isinstance(config.get('machines'), list):
        raise RefreshError('Hardware file needs schema: 1 and a machines list')
    machines = config['machines']
    names = set()
    for m in machines:
        if not isinstance(m, dict) or not isinstance(m.get('name'), str) or not m['name'].strip() or m['name'] in names:
            raise RefreshError('Each machine needs a unique name')
        names.add(m['name'])
        memory, reserve = m.get('memory_gib'), m.get('reserve_gib', 8)
        if memory is not None and (number(memory) is None or memory <= 0):
            raise RefreshError(f'{m["name"]}: memory_gib must be positive or null')
        if number(reserve) is None or (memory is not None and reserve >= memory):
            raise RefreshError(f'{m["name"]}: reserve_gib must be nonnegative and below memory_gib')
        m['reserve_gib'] = reserve
        if not isinstance(m.get('description', ''), str):
            raise RefreshError(f'{m["name"]}: description must be text')
    return machines


def weight_gib(parameters_billion, bits):
    """Total weights, including a 15% allowance for quantization metadata."""
    return parameters_billion * 1_000_000_000 * bits / 8 * 1.15 / (1024 ** 3)


def local_machines(model, machines, bits):
    params = model['parameters_billion']
    if not model['open_weights'] or params is None or params <= 0:
        return []
    needed = weight_gib(params, bits)
    return [m['name'] for m in machines if m.get('memory_gib') is not None and needed <= m['memory_gib'] - m['reserve_gib']]


def cell(value):
    return escape(str(value), quote=False).replace('|', '&#124;').replace('[', '&#91;').replace(']', '&#93;').replace('`', '&#96;').replace('\n', ' ').replace('\r', ' ')


def metric(value, places=1):
    return '—' if value is None else f'{value:,.{places}f}'


def model_link(model):
    return f'[{cell(model["name"])}]({MODELS_URL}/{model["slug"]})'


def rank(model):
    return (model['intelligence'] is not None, model['intelligence'] or 0, model['release_date'] or '', model['slug'])


def families(models):
    selected = {}
    for model in models:
        key = (model['creator'], model['release'])
        if key not in selected or rank(model) > rank(selected[key]):
            selected[key] = model
    return list(selected.values())


def render(snapshot, machines, bits=8):
    if snapshot.get('complete') is not True:
        raise RefreshError('Snapshot is incomplete; run an online refresh before updating guidance')
    models = [m for m in snapshot['models'] if in_scope(m)]
    validate_coverage(models)
    day = datetime.fromisoformat(snapshot['fetched_at']).date().isoformat()
    lines = [START, '## Current model evidence', '',
             f'Catalog checked {day}. Source: [Artificial Analysis]({MODELS_URL}) and its [public leaderboard]({LEADERBOARD_URL}). '
             f'This snapshot covers {len(snapshot["models"])} public leaderboard records, including {len(models)} current records from OpenAI, Anthropic, Google or open-weight creators. '
             'Models absent from that catalog are outside this snapshot.', '',
             'Use these candidates when choosing a provider or testing a local model. The Intelligence Index measures broad benchmark performance; '
             'it does not establish coding-agent reliability, client support or account access. Evaluated settings in model names are benchmark variants, '
             'not verified launch identifiers or supported effort settings. Keep the verified Codex pairs and session preferences above until launch evidence and task results justify changing them.', '',
             '### Hosted provider candidates', '',
             'Each provider lists its five most recent dated releases, plus its strongest evaluated release when older. '
             'Each release uses its highest-scoring evaluated variant; missing scores remain unknown. Dates are release dates from Artificial Analysis, '
             'so a newer release can have a lower score. Estimated scores are marked with an asterisk.', '',
             '| Provider | Evaluated model | Released | Intelligence Index | Benchmark USD/task | Input / output USD per M tokens |',
             '|---|---|---|---:|---:|---:|']
    for provider in PROVIDERS:
        candidates = families([m for m in models if m['creator'] == provider and not m['open_weights']])
        dated = sorted(candidates, key=lambda m: (m['release_date'] or '', m['slug']), reverse=True)
        chosen = dated[:5]
        strongest = max(candidates, key=rank)
        if strongest not in chosen:
            chosen.append(strongest)
        for m in chosen:
            score = metric(m['intelligence']) + ('*' if m['estimated_score'] else '')
            prices = metric(m['input_price'], 2) + ' / ' + metric(m['output_price'], 2)
            lines.append(f'| {provider} | {model_link(m)} | {m["release_date"] or "Unknown"} | {score} | {metric(m["cost_per_task"], 3)} | {prices} |')
    lines += ['', 'API benchmark prices are comparison evidence. They do not estimate subscription usage or authorize paid inference. '
              'Compare the same benchmark setting when assessing a price/quality tradeoff; similarly named effort levels across providers are not equivalent.', '',
              '### Local model candidates', '',
              f'Estimates assume {bits}-bit weights plus 15% for quantization metadata, using **total** parameters, including inactive mixture-of-experts weights. '
              'Each machine also reserves memory for its runtime and context cache. These are memory candidates: '
              'confirm an available quantization, license, runtime support, context length and acceptable measured speed before recommending a model for work. '
              'Hosted throughput and benchmark scores do not measure either machine. CPU offload and pooling memory across machines are outside this estimate.', '',
              '| Machine | Inference memory GiB | Reserved GiB | Weight budget GiB | Profile |',
              '|---|---:|---:|---:|---|']
    for m in machines:
        memory = m.get('memory_gib')
        lines.append(f'| {cell(m["name"])} | {metric(memory)} | {metric(m["reserve_gib"])} | {metric(None if memory is None else memory - m["reserve_gib"])} | {cell(m.get("description", ""))} |')
    if not machines:
        lines += ['', 'No machine profiles configured. Add a local hardware file to estimate candidates.']
    unknown = [m['name'] for m in machines if m.get('memory_gib') is None]
    if unknown:
        lines += ['', 'Memory capacity is unknown for ' + ', '.join(map(cell, unknown)) + '; no compatibility is inferred for these machines.']
    local = families([m for m in models if local_machines(m, machines, bits)])
    local.sort(key=rank, reverse=True)
    lines += ['', f'{len(local)} release(s) meet at least one configured memory budget at {bits} bits. '
              'One evaluated variant is shown per release, ordered by Intelligence Index; unscored models follow scored models.', '',
              '| Evaluated model | Creator | Total B params | Estimated weights GiB | Memory candidate on | Intelligence Index |',
              '|---|---|---:|---:|---|---:|']
    for m in local:
        score = metric(m['intelligence']) + ('*' if m['estimated_score'] else '')
        lines.append(f'| {model_link(m)} | {cell(m["creator"])} | {metric(m["parameters_billion"])} | {metric(weight_gib(m["parameters_billion"], bits))} | {", ".join(map(cell, local_machines(m, machines, bits)))} | {score} |')
    unknown_size = families([m for m in models if m['open_weights'] and not m['parameters_billion']])
    if unknown_size:
        lines += ['', 'Open-weight releases with unknown total parameter counts were not classified: ' + ', '.join(model_link(m) for m in sorted(unknown_size, key=lambda m: m['name'])) + '.']
    lines += ['', 'Refresh with `python3 -m workbench.model_guidance`; see `docs/model-guidance.md` in the source checkout. '
              'This private report contains local recommendations; do not copy it into shared repositories. Refreshing never changes client defaults.', END]
    return '\n'.join(lines)


def replace_section(before, section):
    if START not in before and END not in before:
        return before.rstrip() + '\n\n' + section + '\n'
    if before.count(START) != 1 or before.count(END) != 1 or before.index(START) >= before.index(END):
        raise RefreshError('Model reference has invalid generated-section markers')
    start, end = before.index(START), before.index(END) + len(END)
    return before[:start] + section + before[end:]


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--context-dir', type=Path)
    p.add_argument('--output', '--reference', dest='reference', type=Path, help='Private report path; --reference is a compatibility alias')
    p.add_argument('--hardware', type=Path, help='Optional hardware JSON input; otherwise use private context')
    p.add_argument('--cache', type=Path, help='Private cache path')
    p.add_argument('--diff', action='store_true', help='Display private report diff in this terminal')
    p.add_argument('--offline', action='store_true', help='Use the existing dated cache; never relabel it as fresh')
    p.add_argument('--bits', type=int, choices=(6, 8, 16), default=8, help='Weight precision for local memory estimates; default: 8 bits, minimum: 6 bits')
    p.add_argument('--workers', type=int, choices=range(1, 9), default=4)
    p.add_argument('--timeout', type=float, default=30)
    p.add_argument('--detail-max-age', type=float, default=24, help='Hours to reuse detail metadata; 0 refetches all detail pages')
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true', help='Save the private generated report')
    mode.add_argument('--check', action='store_true', help='Exit 1 when reference evidence differs, 0 when current')
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if not math.isfinite(args.timeout) or args.timeout <= 0 or not math.isfinite(args.detail_max_age) or args.detail_max_age < 0:
            raise RefreshError('Timeout must be positive; detail max age must be nonnegative')
        root = context_root(args.context_dir)
        args.reference = outside_git(args.reference) if args.reference else private_path(root, root / 'generated/model-guidance.md')
        args.cache = outside_git(args.cache) if args.cache else private_path(root, root / 'cache/artificial-analysis.json')
        explicit_hardware = args.hardware is not None
        args.hardware = args.hardware or private_path(root, root / 'context/hardware.json')
        if args.reference.resolve() in {args.cache.resolve(), args.hardware.resolve()} or args.cache.resolve() == args.hardware.resolve():
            raise RefreshError('Reference, cache and hardware paths must be different')
        # Refuse worktree output paths before any fetch or cache changes.
        before = args.reference.read_text() if args.reference.exists() else '# Private model guidance\n\n'
        replace_section(before, '')
        hardware = args.hardware
        if explicit_hardware and not hardware.exists():
            raise RefreshError('Explicit hardware input does not exist')
        machines = load_hardware(hardware) if hardware.exists() else []
        if not hardware.exists():
            print('Hardware is unknown; use context setup to add a private profile.', file=sys.stderr)
        progress = lambda message: print(message, file=sys.stderr, flush=True)
        snapshot = load_snapshot(args.cache) if args.offline else refresh(args.cache, args.timeout, args.workers, args.detail_max_age, progress=progress)
        after = replace_section(before, render(snapshot, machines, args.bits))
        if before == after:
            print('Model evidence is current.')
            return 0
        if args.check:
            print('Model evidence differs; run without --check to review, then --apply.')
            return 1
        if args.diff:
            print(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=str(args.reference), tofile=str(args.reference) + ' (refreshed)')), end='')
        if args.apply:
            if (args.reference.read_text() if args.reference.exists() else '# Private model guidance\n\n') != before:
                raise RefreshError('Reference changed during refresh; run again to review the current file')
            atomic_write(args.reference, after)
            print('Private model guidance saved.')
        else:
            print('Preview only; add --apply to save private guidance, or --diff to inspect it locally.')
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'ERROR {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
