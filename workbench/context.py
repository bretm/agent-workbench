"""User-owned private context, independent of repositories and installer journals."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid

TOPIC = re.compile(r'[a-z][a-z0-9-]*\Z')


def outside_git(path):
    path = Path(path).expanduser().resolve()
    ancestor = path if path.is_dir() else path.parent
    while not ancestor.exists():
        ancestor = ancestor.parent
    result = subprocess.run(['git', '-C', str(ancestor), 'rev-parse', '--is-inside-work-tree'],
                            capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip() == 'true':
        raise ValueError('Private context and generated output must be outside Git worktrees')
    return path


def context_root(value=None, home=None):
    return outside_git(value or os.environ.get('AWB_CONTEXT_DIR') or
                       (Path(home) if home else Path.home()) / '.agents/agent-workbench')


def private_path(root, path):
    root = outside_git(root)
    path = outside_git(path)
    if not path.is_relative_to(root):
        raise ValueError('Private output must stay inside the selected context directory')
    return path


def write_private(path, text):
    path = outside_git(path)
    missing = []
    parent = path.parent
    while not parent.exists():
        missing.append(parent)
        parent = parent.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
    descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def validate_topic(topic, data):
    if not TOPIC.fullmatch(topic):
        raise ValueError('Topic must use lowercase letters, digits and hyphens')
    if not isinstance(data, dict) or data.get('schema') != 1:
        raise ValueError('Topic input must be a JSON object with schema: 1')
    if topic == 'hardware':
        machines = data.get('machines')
        if not isinstance(machines, list):
            raise ValueError('Hardware needs a machines list')
        names = set()
        for m in machines:
            if not isinstance(m, dict) or not isinstance(m.get('name'), str) or not m['name'].strip() or m['name'] in names:
                raise ValueError('Each machine needs a unique nonempty name')
            names.add(m['name'])
            memory, reserve = m.get('memory_gib'), m.get('reserve_gib', 8)
            def number(v):
                return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
            if memory is not None and (not number(memory) or memory <= 0):
                raise ValueError('Memory must be positive or null')
            if not number(reserve) or reserve < 0 or (memory is not None and reserve >= memory):
                raise ValueError('Reserve must be nonnegative and below known memory')
            if not isinstance(m.get('description', ''), str):
                raise ValueError('Machine description must be text')
    if topic == 'models':
        for key in ('assistants', 'access', 'provider_order'):
            if not isinstance(data.get(key, []), list) or not all(isinstance(x, str) for x in data.get(key, [])):
                raise ValueError(f'{key} must be a list of strings')
        if not isinstance(data.get('role_preferences', {}), dict):
            raise ValueError('role_preferences must be an object')
    return data


def update_topic(root, topic, data, apply=False):
    validate_topic(topic, data)
    root = context_root(root)
    dest = private_path(root, root / 'context' / (topic + '.json'))
    content = json.dumps(data, indent=2, ensure_ascii=False) + '\n'
    index = private_path(root, root / 'context/INDEX.md')
    text = index.read_text() if index.exists() else '# Private context\n\nUser direction and project instructions take precedence. Read only relevant topics.\n'
    pointer = f'- {topic}: {topic}.json'
    indexed = text if pointer in text.splitlines() else text.rstrip() + '\n' + pointer + '\n'
    changed = not dest.exists() or dest.read_text() != content
    index_changed = not index.exists() or indexed != text
    if apply:
        if changed:
            if dest.exists():
                backup = private_path(root, root / 'backups' / (topic + '-' + uuid.uuid4().hex + '.json'))
                write_private(backup, dest.read_text())
            write_private(dest, content)
        if index_changed:
            write_private(index, indexed)
    return changed or index_changed


def ask(prompt, default=''):
    value = input(prompt + (f' [{default}]' if default else '') + ': ').strip()
    return value or default


def setup(root):
    if not sys.stdin.isatty():
        raise ValueError('Setup requires a terminal; use update --input FILE --apply for noninteractive use')
    def existing(topic, default):
        path = private_path(root, root / f'context/{topic}.json')
        return json.loads(path.read_text()) if path.exists() else default
    models = existing('models', {'schema': 1})
    for key, prompt in [('assistants', 'Available coding assistants (comma separated; blank for unknown)'),
                        ('access', 'Cloud/local access you want considered (no credentials or billing details)'),
                        ('provider_order', 'Preferred provider order (blank for no preference)')]:
        models[key] = [x.strip() for x in ask(prompt, ', '.join(models.get(key, []))).split(',') if x.strip()]
    models['rotation'] = ask('How do you choose or rotate providers?', models.get('rotation', ''))
    models['role_preferences'] = models.get('role_preferences', {})
    for role in ('light', 'implementation', 'investigation', 'reasoning', 'visual'):
        previous = models['role_preferences'].get(role, '')
        if not isinstance(previous, str):
            previous = json.dumps(previous)
        models['role_preferences'][role] = ask(f'Preferred model/client/effort for {role} (blank if unknown)', previous)
    hardware = existing('hardware', {'schema': 1, 'machines': []})
    if ask('Add a local inference machine? [y/N]', 'n').lower() == 'y':
        machine = {'name': ask('Machine label')}
        capacity = ask('Usable inference memory in GiB (blank if unknown)')
        machine['memory_gib'] = float(capacity) if capacity else None
        machine['reserve_gib'] = float(ask('Memory reserved for runtime and context, GiB', '8'))
        machine['description'] = ask('Optional hardware notes')
        if any(m['name'] == machine['name'] for m in hardware['machines']):
            raise ValueError('That machine exists; use update to review a replacement')
        hardware['machines'].append(machine)
    for topic, data in [('models', models), ('hardware', hardware)]:
        validate_topic(topic, data)
    print('Review: model preferences and hardware profiles will be saved privately. Existing topics are backed up.')
    print(json.dumps({'models': models, 'hardware': hardware}, indent=2))
    if ask('Save this private context? [y/N]', 'n').lower() == 'y':
        for topic, data in [('models', models), ('hardware', hardware)]:
            update_topic(root, topic, data, apply=True)
        print('Private context saved.')
    else:
        print('Cancelled; no context files changed.')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['setup', 'show', 'update', 'migrate'])
    parser.add_argument('--context-dir', type=Path)
    parser.add_argument('--home', type=Path)
    parser.add_argument('--topic', default='models')
    parser.add_argument('--input', type=Path, help='Whole-topic JSON replacement; - reads stdin')
    parser.add_argument('--from', dest='legacy', type=Path, help='Old local-data directory for hardware/cache/reference import')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        root = context_root(args.context_dir, args.home)
        if args.action == 'setup':
            return setup(root)
        if args.action == 'show':
            if args.apply:
                raise ValueError('show is read-only')
            if not TOPIC.fullmatch(args.topic):
                raise ValueError('Invalid topic')
            path = private_path(root, root / f'context/{args.topic}.json')
            print(path.read_text() if path.exists() else 'Unknown: run context setup or update this topic.')
            return 0
        if args.action == 'update':
            if args.input is None:
                raise ValueError('update requires --input FILE (or - for stdin)')
            data = json.loads(sys.stdin.read() if str(args.input) == '-' else args.input.read_text())
            changed = update_topic(root, args.topic, data, args.apply)
            print(('Saved privately.' if args.apply else 'Preview only; add --apply.') if changed else 'Already current.')
            return 0
        if args.legacy is None:
            raise ValueError('migrate requires --from DIRECTORY')
        legacy = args.legacy.expanduser().resolve()
        operations = []
        for source, dest in [('model-hardware.json', 'context/hardware.json'),
                             ('artificial-analysis.json', 'cache/artificial-analysis.json'),
                             ('models.md', 'context/model-preferences.md')]:
            path = legacy / source
            if path.exists():
                content = path.read_text()
                if source == 'model-hardware.json':
                    validate_topic('hardware', json.loads(content))
                target = private_path(root, root / dest)
                if target.exists() and target.read_text() != content:
                    raise ValueError('Migration would overwrite existing private context; compare and use update')
                operations.append((target, content))
        if not operations:
            raise ValueError('No recognized legacy inputs found')
        index = private_path(root, root / 'context/INDEX.md')
        if args.apply:
            for target, content in operations:
                write_private(target, content)
            hardware = root / 'context/hardware.json'
            if hardware.exists():
                update_topic(root, 'hardware', json.loads(hardware.read_text()), True)
            index = private_path(root, root / 'context/INDEX.md')
            if not index.exists():
                write_private(index, '# Private context\n\nRead relevant topics only. User and project instructions take precedence.\n')
            text = index.read_text()
            for target, _ in operations:
                if target.parent == index.parent:
                    pointer = '- ' + target.name
                    if pointer not in text.splitlines():
                        text += pointer + '\n'
            write_private(index, text)
        print(f'{len(operations)} private input(s); ' + ('migrated.' if args.apply else 'preview only; add --apply.'))
        return 0
    except (OSError, ValueError, EOFError, KeyboardInterrupt) as exc:
        print(f'Context operation stopped: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
