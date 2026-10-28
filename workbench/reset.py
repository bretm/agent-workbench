"""Explicit, fingerprinted workflow retirement. Never discover-to-apply."""
import json
import hashlib
from pathlib import Path
import tomllib

from .planner import (Plan, alternate_skill_roots, harness_root, installation,
                      read_json, select_harnesses, validate)
from .storage import Conflict, snapshot, section, decode, block, replace_block, file_value


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def roots(source, home, harnesses, homes):
    manifest = validate(source)
    selected = select_harnesses(source, manifest, harnesses, workflow_reset=True)
    for name in selected:
        if name not in manifest['harnesses']:
            raise Conflict(f'unsupported harness {name}')
        adapter = read_json(source / 'adapters' / f'{name}.json')
        if 'workflow_reset' not in adapter:
            raise Conflict(f'{name}: adapter has no verified workflow-reset discovery contract')
        root = harness_root(adapter, home, homes.get(name))
        yield name, adapter, root


def inventory(source, home, state, harnesses, homes):
    """Return review input containing hashes, never credentials or config values."""
    entries, exceptions, blockers, plugin_skills = {}, [], [], []
    for name, adapter, root in roots(source, home, harnesses, homes):
        contract = adapter['workflow_reset']
        if contract.get('builtin_skill_note'):
            exceptions.append(f'{name}: {contract["builtin_skill_note"]}')
        paths = set()
        native = (home if adapter['skill_scope'] == 'user' else root) / adapter['skill_directory']
        skill_dirs = [native, *alternate_skill_roots(adapter, root)]
        for directory in skill_dirs:
            if directory.is_symlink():
                blockers.append(f'{directory}: linked discovery directory; choose its real location explicitly')
                continue
            if directory.is_dir():
                for p in directory.iterdir():
                    if p.name in contract['builtin_skill_directories']:
                        exceptions.append(f'{name}: built-in skill directory {p}')
                    elif p.name in contract.get('preserved_skill_directories', []):
                        exceptions.append(f'{name}: preserved client-managed skill directory {p}')
                    else:
                        paths.add(p)
        paths.update(root / p for p in contract['harness_paths'])
        paths.update(home / p for p in contract['user_paths'])
        for p in sorted(paths):
            key = str(p)
            owned = state['entries'].get(key)
            if owned:
                # An earlier additive install can still have legacy prose outside its
                # section. Review that prose for the first clean-slate reset; subsequent
                # outside user edits remain user-owned and are preserved.
                if key != str(root / adapter['instruction_file']) or owned['type'] != 'section' or state.get('workflow_reset'):
                    continue
                current = snapshot(p)
                if current['kind'] != 'file' or not replace_block(decode(current), block(decode(current)), None).strip():
                    continue
            current = snapshot(p, tree=True)
            if current['kind'] != 'absent':
                entries[key] = {'path': key, 'fingerprint': fingerprint(current),
                                'kind': current['kind'], 'action': 'retire'}
        config = root / contract['settings_file']
        if config.is_file():
            data = tomllib.loads(config.read_text()) if config.suffix == '.toml' else json.loads(config.read_text())
            for key in contract['workflow_setting_keys']:
                owned_control = state['entries'].get(str(config), {}).get('type') == 'toml-section'
                if key in data and not (key == contract.get('skill_settings_key') and owned_control):
                    blockers.append(f'{config}: workflow setting {key!r} needs a reviewed per-key migration; operational settings will not be replaced')
            plugins = data.get(contract['plugin_key'], {})
            if not isinstance(plugins, dict):
                raise Conflict(f'{config}: invalid plugin settings')
            for plugin, setting in sorted(plugins.items()):
                enabled = setting.get('enabled', True) if isinstance(setting, dict) else bool(setting)
                if enabled:
                    control = contract.get('plugin_skill_control')
                    if not control:
                        blockers.append(f'{name}: enabled plugin {plugin!r}; selective skill suppression not verified on {adapter["verified_version"]}; keep connections intact')
                        continue
                    package, sep, marketplace = plugin.partition('@')
                    if not sep or Path(package).name != package or Path(marketplace).name != marketplace:
                        blockers.append(f'{name}: invalid plugin selector {plugin!r}')
                        continue
                    cache = root / contract['plugin_cache_directory'] / marketplace / package
                    manifests = sorted(cache.glob('*/.codex-plugin/plugin.json'))
                    if not manifests:
                        blockers.append(f'{name}: {plugin!r} has no cached manifest; selective skill suppression not verified for this installation')
                    for metadata in manifests:
                        spec = json.loads(metadata.read_text())
                        skill_relative = spec.get('skills')
                        if not skill_relative:
                            exceptions.append(f'{name}: tool-only plugin {plugin}; no skill source in {metadata.parent.parent.name}')
                            continue
                        if not isinstance(skill_relative, str) or Path(skill_relative).is_absolute() or '..' in Path(skill_relative).parts:
                            blockers.append(f'{metadata}: unsupported skill source; review discovery explicitly')
                            continue
                        skill_root = metadata.parent.parent / skill_relative
                        if not skill_root.is_dir():
                            blockers.append(f'{metadata}: declared skill directory is missing')
                            continue
                        for p in sorted(skill_root.rglob('SKILL.md')):
                            resolved = p.resolve()
                            if not resolved.is_relative_to(cache.resolve()):
                                blockers.append(f'{p}: plugin skill target escapes its cache package')
                                continue
                            plugin_skills.append({'harness': name, 'plugin': plugin, 'path': str(p),
                                                  'fingerprint': fingerprint(snapshot(resolved))})
        for relative in contract['additional_settings_files']:
            p = root / relative
            if p.is_file():
                data = json.loads(p.read_text())
                if data.get('enabledPlugins'):
                    blockers.append(f'{p}: additional plugin enablement needs review')
        synced = native / 'synced'
        preserved = contract['builtin_skill_directories'] + contract.get('preserved_skill_directories', [])
        if synced.exists() and synced.name not in preserved:
            blockers.append(f'{synced}: account-synced skills can return; disable account sync before resetting')
    return {'schema': 1, 'entries': list(entries.values()), 'plugin_skills': plugin_skills, 'exceptions': sorted(set(exceptions)),
            'blockers': sorted(set(blockers))}


def reset_installation(source, home, state_dir, state, config, harnesses, repos, homes):
    selected = select_harnesses(source, validate(source), harnesses, config, state, workflow_reset=True)
    observed = inventory(source, home, state, selected, homes)
    review = config.get('workflow_reset')
    plan = Plan(state)
    plan.conflicts.extend(observed['blockers'])
    if review is None:
        plan.conflicts.append('reset requires reviewed workflow_reset inventory; run reset-workflow --inventory and save its JSON locally')
        review = {'schema': 1, 'entries': [], 'plugin_skills': [], 'exceptions': [], 'blockers': []}
    if not isinstance(review, dict) or set(review) != {'schema', 'entries', 'plugin_skills', 'exceptions', 'blockers'} or review['schema'] != 1:
        raise Conflict('workflow_reset must be the schema-1 review inventory')
    if review['plugin_skills'] != observed['plugin_skills']:
        plan.conflicts.append('plugin skill inventory changed or not reviewed; refresh and review inventory')
    requested = {}
    for entry in review['entries']:
        if not isinstance(entry, dict) or set(entry) != {'path', 'fingerprint', 'kind', 'action'} or entry['action'] != 'retire':
            raise Conflict('reset entries require exact path, fingerprint, kind and retire action')
        if entry['path'] in requested:
            raise Conflict('duplicate reset path')
        requested[entry['path']] = entry
    expected = {e['path']: e for e in observed['entries']}
    for key in requested.keys() - expected.keys():
        # Successful reruns may refer to already-retired or replaced owned paths.
        if key not in state['entries'] or not state.get('workflow_reset'):
            plan.conflicts.append(f'{key}: reset path is no longer discovered or outside permitted workflow locations')
    for key, entry in expected.items():
        if requested.get(key) != entry:
            plan.conflicts.append(f'{key}: missing or changed review fingerprint; refresh and review inventory')
            continue
        current = snapshot(Path(key), tree=True)
        after = {'kind': 'absent'}
        kind = 'tree' if current['kind'] == 'tree' else 'file'
        original = current
        if state['entries'].get(key, {}).get('type') == 'section' and current['kind'] == 'file':
            original = file_value(replace_block(decode(current), block(decode(current)), None), current['mode'])
        plan.next['entries'][key] = {'type': kind, 'expected': after, 'original': original}
        plan.operation({'path': key, 'type': kind, 'before': current, 'after': after})
        plan.messages.append(f'ARCHIVE / RETIRE {key} [{entry["kind"]}, {entry["fingerprint"][:12]}] into durable local journal')
    for _, adapter, root in roots(source, home, selected, homes):
        key = str(root / adapter['instruction_file'])
        if key in plan.overlay:
            plan.reset_instructions.add(key)
    for name, adapter, root in roots(source, home, selected, homes):
        contract = adapter['workflow_reset']
        control = contract.get('plugin_skill_control')
        selected_paths = sorted({s['path'] for s in observed['plugin_skills'] if s['harness'] == name})
        if control and (selected_paths or state['entries'].get(str(root / contract['settings_file']), {}).get('type') == 'toml-section'):
            body = '\n\n'.join(control['entry_template'].replace('{path}', json.dumps(p)) for p in selected_paths)
            p = root / contract['settings_file']
            plan.attempt(lambda p=p, body=body: plan.add(p, None, 'toml-section', section(body, 'toml-section')))
            # Verify semantic preservation: the generated TOML must parse, and only
            # additional native skill disabling entries may appear.
            generated = plan.overlay.get(str(p))
            if generated:
                before = tomllib.loads(p.read_text()) if p.exists() else {}
                after = tomllib.loads(decode(generated))
                for key in before.keys() | after.keys():
                    if key != contract['skill_settings_key'] and before.get(key) != after.get(key):
                        plan.conflicts.append(f'{p}: suppression would change operational setting {key}')
    plan.next['workflow_reset'] = {'schema': 1, 'harnesses': selected, 'exceptions': observed['exceptions'],
                                   'plugin_skills': observed['plugin_skills']}
    plan.messages.extend('RETAIN ' + e for e in observed['exceptions'])
    return installation(source, home, state_dir, state, config, selected, repos, homes, plan=plan)


def reset_health(source, home, state, harnesses, homes):
    if not state.get('workflow_reset'):
        return []
    # An additive adapter install does not expand a previous reset's authority.
    covered = state['workflow_reset'].get('harnesses', state['harnesses'])
    harnesses = [name for name in harnesses if name in covered]
    if not harnesses:
        return []
    observed = inventory(source, home, state, harnesses, homes)
    errors = observed['blockers'] + [f'{e["path"]}: unmanaged workflow appeared after reset' for e in observed['entries']]
    if observed['plugin_skills'] != state['workflow_reset'].get('plugin_skills', []):
        errors.append('plugin skill paths/content changed since reset; review reset-workflow again')
    for name, adapter, root in roots(source, home, harnesses, homes):
        contract = adapter['workflow_reset']
        if contract.get('plugin_skill_control'):
            expected = {s['path'] for s in observed['plugin_skills'] if s['harness'] == name}
            p = root / contract['settings_file']
            data = tomllib.loads(p.read_text()) if p.is_file() else {}
            configs = data.get(contract['skill_settings_key'], {}).get('config', [])
            if not isinstance(configs, list) or len(configs) != len(expected) or {e.get('path') for e in configs if isinstance(e, dict)} != expected or any(not isinstance(e, dict) or e.get('enabled') is not False for e in configs):
                errors.append(f'{p}: skill controls differ from the approved disabled plugin paths')
    return errors
