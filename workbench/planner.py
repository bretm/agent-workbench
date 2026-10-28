"""Manifest-driven desired state; no writes during discovery or planning."""
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import subprocess

from .storage import (Conflict, SECTION_TYPES, block, decode, digest, file_value, matches,
                      replace_block, section, snapshot)


def read_json(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def default_harnesses(manifest):
    """Return the candidate adapters for fresh-install detection."""
    return manifest.get('default_harnesses', manifest['harnesses'])


def select_harnesses(source, manifest, harnesses=None, config=None, state=None, *, workflow_reset=False):
    """Explicit and recorded targets win; otherwise detect installed candidates."""
    selected = harnesses or (config or {}).get('harnesses') or (state or {}).get('harnesses')
    if selected:
        return list(dict.fromkeys(selected))
    detected = []
    for name in default_harnesses(manifest):
        adapter = read_json(source / 'adapters' / f'{name}.json')
        if workflow_reset and 'workflow_reset' not in adapter:
            continue
        if shutil.which(adapter['executable']):
            detected.append(name)
    if not detected:
        capability = ' with verified workflow-reset support' if workflow_reset else ''
        raise Conflict(f'No supported agent clients{capability} found on PATH; install a supported client or select one explicitly with --harness.')
    return detected


def harness_root(adapter, home, override=None):
    variable = adapter.get('home_environment')
    environment = os.environ.get(variable) if variable else None
    return Path(override or environment or home / adapter['home_directory']).expanduser().absolute()


def alternate_skill_roots(adapter, root):
    paths = [adapter['alternate_skill_directory']] if adapter['alternate_skill_directory'] else []
    return [root / p for p in dict.fromkeys(paths + adapter.get('additional_skill_directories', []))]


def validate(source):
    manifest = read_json(source / 'workbench.json')
    if not manifest or manifest.get('schema') != 1:
        raise Conflict('workbench.json: unsupported or missing schema')
    defaults = default_harnesses(manifest)
    if not isinstance(defaults, list) or not defaults or any(x not in manifest['harnesses'] for x in defaults):
        raise Conflict('default_harnesses must select supported harnesses')
    skills = manifest['skills']
    for name, spec in skills.items():
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or len(name) > 64:
            raise Conflict(f'invalid skill name: {name}')
        p = source / 'skills' / name / 'SKILL.md'
        text = p.read_text()
        front = text.split('---', 2)
        if len(front) != 3 or front[0].strip():
            raise Conflict(f'{p}: missing frontmatter')
        fields = dict(line.split(':', 1) for line in front[1].strip().splitlines())
        if fields.get('name', '').strip() != name or not fields.get('description', '').strip():
            raise Conflict(f'{p}: name/description missing or incorrect')
        if set(fields) != {'name', 'description'}:
            raise Conflict(f'{p}: shared metadata must remain portable name/description')
        for dep in spec['dependencies']:
            if dep not in skills:
                raise Conflict(f'{name}: missing dependency {dep}')
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if '://' in target:
                continue
            resolved = (p.parent / target).resolve()
            if not resolved.is_relative_to(source.resolve()) or not resolved.is_file():
                raise Conflict(f'{p}: missing or escaping reference {target}')
    visiting, visited = set(), set()
    def visit(name):
        if name in visiting:
            raise Conflict(f'cyclic dependency: {name}')
        if name in visited:
            return
        visiting.add(name)
        for dep in skills[name]['dependencies']:
            visit(dep)
        visiting.remove(name)
        visited.add(name)
    for name in skills:
        visit(name)
    for harness in manifest['harnesses']:
        adapter = read_json(source / 'adapters' / f'{harness}.json')
        if not adapter or adapter.get('schema') != 1:
            raise Conflict(f'invalid adapter {harness}')
        paths = [adapter[k] for k in ['instruction_file', 'skill_directory', 'home_directory']]
        paths += adapter['shadow_files'] + adapter['project_shadow_files'] + adapter['project_skill_directories']
        paths += [adapter[k] for k in ['project_bridge', 'alternate_skill_directory'] if adapter[k]]
        paths += adapter.get('additional_skill_directories', [])
        reset = adapter.get('workflow_reset')
        if reset:
            paths += reset['harness_paths'] + reset['user_paths'] + [reset['settings_file']] + reset['additional_settings_files']
            for field in ['builtin_skill_directories', 'preserved_skill_directories']:
                directories = reset.get(field, [])
                if not isinstance(directories, list) or any(not isinstance(name, str) or not name
                        or Path(name).name != name or name in {'.', '..'} for name in directories):
                    raise Conflict(f'{harness}: {field} must contain single directory names')
        for key in paths:
            rel = Path(key)
            if rel.is_absolute() or '..' in rel.parts:
                raise Conflict(f'unsafe adapter path {key}')
    for rel in ['LICENSE', manifest['agreements'], *['reference/' + x for x in manifest['references']]]:
        if not (source / rel).is_file():
            raise Conflict(f'missing canonical content {rel}')
    for rel in ['runtime/awb-local.py', 'workbench/__init__.py', 'workbench/context.py', 'workbench/model_guidance.py']:
        path = source / rel
        if path.is_symlink() or not path.is_file():
            raise Conflict(f'missing or linked private runtime: {rel}')
    return manifest


def pack(source, manifest):
    files = {}
    for directory in ['skills', 'reference']:
        for p in sorted((source / directory).rglob('*')):
            if p.is_symlink():
                raise Conflict(f'canonical content must not have machine-specific symlinks: {p}')
            if p.is_file():
                rel = p.relative_to(source)
                if directory == 'skills' and rel.parts[1] not in manifest['skills']:
                    continue
                files[str(rel)] = p.read_text()
    files['LICENSE'] = (source / 'LICENSE').read_text()
    files['agreements/working.md'] = (source / manifest['agreements']).read_text()
    files['workbench.json'] = (source / 'workbench.json').read_text()
    for harness in manifest['harnesses']:
        files[f'adapters/{harness}.json'] = (source / 'adapters' / f'{harness}.json').read_text()
    files['runtime/awb-local.py'] = (source / 'runtime/awb-local.py').read_text()
    for name in ['__init__.py', 'context.py', 'model_guidance.py']:
        files['runtime/workbench/' + name] = (source / 'workbench' / name).read_text()
    return files



def named_collisions(directory, manifest, excluded=frozenset()):
    """Inspect only skill metadata, not arbitrary files or harness history."""
    if not directory.is_dir():
        return []
    names = set(manifest['skills']) | set(manifest['competing_skills'])
    found = []
    for p in sorted(directory.iterdir()):
        if p.name in excluded:
            continue
        skill = p / 'SKILL.md'
        if p.name in names:
            found.append(p)
        elif skill.is_file():
            match = re.search(r'^name:\s*[\'\"]?([a-z0-9-]+)', skill.read_text()[:4000], re.M)
            if match and match[1] in names:
                found.append(p)
    return found


def empty_state():
    return {'schema': 1, 'entries': {}, 'harnesses': [], 'repositories': []}


def require_repo(path):
    path = Path(path).expanduser().resolve()
    result = subprocess.run(['git', '-C', str(path), 'rev-parse', '--show-toplevel'],
                            text=True, capture_output=True, timeout=10)
    if result.returncode or Path(result.stdout.strip()).resolve() != path:
        raise Conflict(f'{path}: select a Git repository/worktree root')
    return path


class Plan:
    def __init__(self, state):
        self.previous = state
        self.next = json.loads(json.dumps(state))
        self.operations = []
        self.messages = []
        self.conflicts = []
        self.overlay = {}
        self.reset_instructions = set()

    def current(self, path):
        key = str(path)
        return self.overlay[key] if key in self.overlay else snapshot(Path(path))

    def operation(self, op):
        """Coalesce reset and installation of one path into one reversible operation."""
        prior = next((x for x in self.operations if x['path'] == op['path']), None)
        if prior:
            op['before'] = prior['before']
            self.operations.remove(prior)
        if op['before']['kind'] == 'tree' or op['after']['kind'] == 'tree':
            op['type'] = 'tree'
        self.operations.append(op)
        self.overlay[op['path']] = op['after']

    def add(self, path, value, kind='file', managed=None, migration=None):
        path = Path(path)
        key = str(path)
        current = self.current(path)
        entry = self.next['entries'].get(key)
        if entry and key not in self.overlay and not matches(path, entry):
            raise Conflict(f'{path}: locally modified managed content')
        if kind in SECTION_TYPES:
            if current['kind'] not in {'absent', 'file'}:
                raise Conflict(f'{path}: refusing to modify linked instruction file')
            text = decode(current) if current['kind'] == 'file' else ''
            old = block(text, kind)
            if old and not entry:
                raise Conflict(f'{path}: unowned managed markers; refusing adoption')
            mode = current.get('mode', entry['original'].get('mode', 0o644) if entry else 0o644)
            value = file_value(replace_block(text, old, managed), mode)
            record = {'type': 'reset-section' if key in self.reset_instructions or entry and entry['type'] == 'reset-section' else kind, 'block': managed, 'expected': value,
                      'original': entry['original'] if entry else current}
        else:
            if current['kind'] != 'absent' and not entry:
                if not migration or current != {'kind': 'link', 'target': migration}:
                    raise Conflict(f'{path}: existing unowned {current["kind"]}; explicit migration required')
            record = {'type': kind, 'expected': value,
                      'original': entry['original'] if entry else current}
        self.next['entries'][key] = record
        if current == value:
            self.messages.append(f'OK {path}')
            return
        op = {'path': key, 'type': kind, 'before': current, 'after': value}
        if kind in SECTION_TYPES:
            op.update(before_block=old, after_block=managed)
            if key in self.reset_instructions:
                op['type'] = 'reset-section'
        self.operation(op)
        action = 'merge section' if kind in SECTION_TYPES else ('link' if value['kind'] == 'link' else 'generate')
        if migration:
            action = 'replace explicitly selected link'
        self.messages.append(f'{action.upper()} {path}' + (f' -> {value["target"]}' if value['kind'] == 'link' else ''))

    def retire(self, path, target):
        path = Path(path)
        current = snapshot(path)
        key = str(path)
        entry = self.previous['entries'].get(key)
        if entry and entry['expected']['kind'] == 'absent' and current['kind'] == 'absent':
            return
        if current != {'kind': 'link', 'target': target}:
            raise Conflict(f'{path}: retirement requires the exact observed symlink target')
        after = {'kind': 'absent'}
        self.next['entries'][key] = {'type': 'file', 'expected': after, 'original': current}
        self.operations.append({'path': key, 'type': 'file', 'before': current, 'after': after})
        self.messages.append(f'RETIRE selected competing link {path} -> {target}')

    def attempt(self, callback):
        try:
            callback()
        except (Conflict, OSError, ValueError) as exc:
            self.conflicts.append(str(exc))


def installation(source, home, state_dir, state, config, harnesses, repos, homes, plan=None):
    manifest = validate(source)
    files = pack(source, manifest)
    content_hash = digest(files)
    release = state_dir / 'releases' / content_hash
    plan = plan or Plan(state)
    if state.get('workflow_reset'):
        plan.next['workflow_reset'].setdefault('harnesses', list(state['harnesses']))
    # Check all owned content, including old release snapshots, before any update.
    for key, entry in state['entries'].items():
        def verify_owned(key=key, entry=entry):
            if not matches(Path(key), entry):
                raise Conflict(f'{key}: managed content drift')
        plan.attempt(verify_owned)
    selected = select_harnesses(source, manifest, harnesses, config, state)
    if not (harnesses or config.get('harnesses') or state['harnesses']):
        plan.messages.append('DETECTED installed clients: ' + ', '.join(selected))
    for name in selected:
        if name not in manifest['harnesses']:
            raise Conflict(f'unsupported harness {name}')
    migrations = {str(Path(m['path']).expanduser().absolute()): m for m in config.get('migrations', [])}
    allowed_migrations = set()
    for name in selected:
        a = read_json(source / 'adapters' / f'{name}.json')
        harness_home = harness_root(a, home, homes.get(name) or config.get('homes', {}).get(name))
        skill_dir = (home if a['skill_scope'] == 'user' else harness_home) / a['skill_directory']
        # Changing the declarative skill selection removes only formerly owned links.
        for key, entry in list(state['entries'].items()):
            p = Path(key)
            if p.parent == skill_dir and p.name not in manifest['skills'] and entry['expected']['kind'] == 'link':
                def drop(p=p, key=key, entry=entry):
                    if not matches(p, entry):
                        raise Conflict(f'{p}: drift blocks deselection')
                    current = snapshot(p)
                    after = {'kind': 'absent'} if state.get('workflow_reset') else entry['original']
                    plan.operation({'path': key, 'type': entry['type'], 'before': current, 'after': after})
                    if state.get('workflow_reset'):
                        plan.next['entries'][key]['expected'] = after
                    else:
                        del plan.next['entries'][key]
                    plan.messages.append(f'RETIRE deselected skill {p}' if state.get('workflow_reset') else f'RESTORE / REMOVE deselected skill {p}')
                plan.attempt(drop)
        executable = shutil.which(a['executable'])
        if not executable:
            plan.conflicts.append(f'{name}: not installed; follow {a["setup_url"]}; no automatic installation/authentication')
        else:
            result = subprocess.run([executable, '--version'], text=True, capture_output=True, timeout=15)
            if result.returncode:
                plan.conflicts.append(f'{name}: version probe failed')
            else:
                version = result.stdout.strip()
                plan.next.setdefault('harness_versions', {})[name] = version
                plan.messages.append(f'HARNESS {name}: {version}')
                found_version = re.search(r'\b[0-9]+\.[0-9]+\.[0-9]+\b', version)
                if not found_version or found_version[0] != a['verified_version']:
                    plan.conflicts.append(f'{name}: adapter verified on {a["verified_version"]}, found {version}; re-verify and update adapter before applying')
        for shadow in a['shadow_files']:
            p = harness_home / shadow
            value = plan.current(p)
            if value['kind'] == 'link' or value['kind'] == 'file' and decode(value).strip():
                plan.conflicts.append(f'{p}: shadows persistent instructions; resolve explicitly')
        # Other native discovery directories may contain competing skill names.
        for alt_dir in alternate_skill_roots(a, harness_home):
            for p in named_collisions(alt_dir, manifest, excluded={Path(k).name for k, v in plan.overlay.items() if Path(k).parent == alt_dir and v['kind'] == 'absent'}):
                plan.conflicts.append(f'{p}: competing discovery location; resolve explicitly')
        for skill in manifest['competing_skills']:
            p = skill_dir / skill
            allowed_migrations.add(str(p))
            if plan.current(p)['kind'] != 'absent':
                m = migrations.get(str(p))
                if m and m.get('action') == 'retire':
                    plan.attempt(lambda p=p, m=m: plan.retire(p, m['target']))
                else:
                    plan.conflicts.append(f'{p}: competing workflow; review and explicitly retire this link')
        retired = {Path(k).name for k, v in plan.overlay.items() if Path(k).parent == skill_dir and v['kind'] == 'absent'}
        for p in named_collisions(skill_dir, manifest, excluded=set(manifest['skills']) | set(manifest['competing_skills']) | retired):
            plan.conflicts.append(f'{p}: duplicate skill metadata name or competing workflow')
        for skill in manifest['skills']:
            p = skill_dir / skill
            allowed_migrations.add(str(p))
            m = migrations.get(str(p))
            plan.attempt(lambda p=p, skill=skill, m=m: plan.add(p, {'kind': 'link', 'target': str(release / 'skills' / skill)},
                         migration=m['target'] if m and m.get('action') == 'replace' else None))
        from .context import context_root
        private_root = context_root(config.get('context_dir') or os.environ.get('AWB_CONTEXT_DIR') or state.get('context_dir'), home)
        plan.next['context_dir'] = str(private_root)
        rules = files['agreements/working.md'] + '\nShared model reference: ' + str(release / 'reference/models.md') + '\nWork-record policy: ' + str(release / 'reference/work-records.md') + '\nRead the work-record policy when starting existing tracked work, before planning adopted work, or when making a handoff.\n'
        rules += 'Private context directory: ' + str(private_root) + '\nRead its context/INDEX.md only for relevant personal facts and preferences. Missing context stays unknown.\nPrivate context tool: python3 -B ' + shlex.quote(str(release / 'runtime/awb-local.py')) + ' context\nUse --context-dir ' + shlex.quote(str(private_root)) + ' with private tools.\n'
        plan.attempt(lambda a=a, harness_home=harness_home, rules=rules: plan.add(harness_home / a['instruction_file'], None, 'section', section(rules)))
    for key in migrations:
        if key not in allowed_migrations:
            plan.conflicts.append(f'{key}: migration is outside the selected harness skill locations')
    selected_repos = repos if repos else config.get('repositories', [])
    repo_records = {r['path']: r for r in state['repositories']}
    for spec in selected_repos:
        spec = {'path': spec} if isinstance(spec, str) else spec
        path = require_repo(spec['path'])
        if spec.get('policy_conflicts'):
            plan.conflicts.append(f'{path}: unresolved policy conflicts: {spec["policy_conflicts"]}')
        facts = spec.get('facts', {})
        for key in facts:
            if key not in {'documentation', 'tracker', 'build', 'test', 'exceptions'}:
                raise Conflict(f'{path}: unsupported project fact {key}')
        data = json.dumps({'schema': 1, 'facts': facts}, indent=2) + '\n'
        plan.attempt(lambda path=path, data=data: plan.add(path / '.agent-workbench.json', file_value(data)))
        plan.attempt(lambda path=path: plan.add(path / 'AGENTS.md', None, 'section', section('Project context: read `.agent-workbench.json` for documentation locations, tracker, commands and explicit exceptions. Existing project instructions and explicit user direction take precedence over personal defaults.')))
        for name in selected:
            a = read_json(source / 'adapters' / f'{name}.json')
            for skill_location in a['project_skill_directories']:
                for p in named_collisions(path / skill_location, manifest):
                    plan.conflicts.append(f'{p}: project skill competes with personal discovery; keep a project exception or resolve names before installing')
            for shadow in a['project_shadow_files']:
                if (path / shadow).exists() or (path / shadow).is_symlink():
                    plan.conflicts.append(f'{path / shadow}: may shadow project integration')
            bridge = a['project_bridge']
            if bridge:
                p = path / bridge
                if p.is_symlink() and p.resolve() == (path / 'AGENTS.md').resolve():
                    plan.messages.append(f'USE existing compatibility symlink {p}')
                elif p.is_file() and re.search(r'^@(?:\./)?AGENTS\.md\s*$', p.read_text(), re.M) and str(p) not in state['entries']:
                    plan.messages.append(f'USE existing import {p}; unowned')
                else:
                    plan.attempt(lambda p=p: plan.add(p, None, 'section', section('@AGENTS.md')))
        repo_records[str(path)] = {'path': str(path), 'facts': facts}
        plan.messages.append(f'REVIEW {path}: policy stays local; no automatic migration of existing plans/issues')
    for rel, data in files.items():
        plan.attempt(lambda rel=rel, data=data: plan.add(release / rel, file_value(data)))
    revision = subprocess.run(['git', '-C', str(source), 'rev-parse', 'HEAD'], capture_output=True, text=True, timeout=10)
    plan.next.update(source_revision=revision.stdout.strip() if not revision.returncode else None,
                     harnesses=list(dict.fromkeys(state['harnesses'] + selected)),
                     repositories=list(repo_records.values()), source=str(source),
                     version=manifest['version'], content_hash=content_hash)
    return plan


def removal(state):
    from .storage import inverse
    plan = Plan(state)
    for key, entry in reversed(list(state['entries'].items())):
        def remove(key=key, entry=entry):
            p = Path(key)
            if not matches(p, entry):
                raise Conflict(f'{p}: drift blocks uninstall')
            current = snapshot(p, tree=True)
            op = {'path': key, 'type': entry['type'], 'before': entry['original'], 'after': entry['expected']}
            if entry['type'] in SECTION_TYPES:
                original_text = decode(entry['original']) if entry['original']['kind'] == 'file' else ''
                op.update(before_block=block(original_text, entry['type']), after_block=entry['block'])
                # Compare against the initial file plus the current owned block, not
                # an update snapshot that may already include subsequent user edits.
                baseline = '' if entry['type'] == 'reset-section' else original_text
                op['after'] = file_value(replace_block(baseline, block(baseline, entry['type']), entry['block']),
                                         entry['original'].get('mode', 0o644))
            after = inverse(op)
            if after != current:
                change = {'path': key, 'type': entry['type'], 'before': current, 'after': after}
                if current['kind'] == 'tree' or after['kind'] == 'tree':
                    change['type'] = 'tree'
                if entry['type'] in SECTION_TYPES:
                    change.update(before_block=entry['block'], after_block=block(decode(after), entry['type']) if after['kind'] == 'file' else None)
                plan.operations.append(change)
                plan.messages.append(f'RESTORE / REMOVE {p}')
        plan.attempt(remove)
    plan.next = empty_state()
    return plan
