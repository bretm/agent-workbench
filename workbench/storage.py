"""Atomic storage and reversible path/section operations."""
import base64
import hashlib
import json
import os
import shutil
from pathlib import Path
import stat
import tempfile

BEGIN = '<!-- agent-workbench:begin -->'
END = '<!-- agent-workbench:end -->'
SECTION_TYPES = {'section', 'reset-section', 'toml-section'}


class Conflict(Exception):
    pass


def safe_parent(path):
    for parent in path.parents:
        if parent.is_symlink():
            raise Conflict(f'{path}: symlinked parent {parent}; use an explicit real path')
        if parent.exists() and not parent.is_dir():
            raise Conflict(f'{path}: parent is not a directory: {parent}')


def snapshot(path, tree=False):
    safe_parent(path)
    if path.is_symlink():
        return {'kind': 'link', 'target': os.readlink(path)}
    if not path.exists():
        return {'kind': 'absent'}
    if not path.is_file():
        if tree and path.is_dir():
            return {'kind': 'tree', 'mode': stat.S_IMODE(path.stat().st_mode),
                    'children': {p.name: snapshot(p, tree=True) for p in sorted(path.iterdir())}}
        raise Conflict(f'{path}: expected a regular file or symlink')
    return {'kind': 'file', 'data': base64.b64encode(path.read_bytes()).decode(),
            'mode': stat.S_IMODE(path.stat().st_mode)}


def file_value(text, mode=0o644):
    return {'kind': 'file', 'data': base64.b64encode(text.encode()).decode(), 'mode': mode}


def decode(value):
    if value['kind'] != 'file':
        raise Conflict('instruction file must be a regular file; refusing to follow a link')
    return base64.b64decode(value['data']).decode('utf-8')


def permission_data(value):
    """Read settings without adopting unrelated keys or accepting malformed rules."""
    data = json.loads(decode(value)) if value['kind'] != 'absent' else {}
    if not isinstance(data, dict):
        raise Conflict('settings must be a JSON object')
    permissions = data.get('permissions', {})
    if not isinstance(permissions, dict):
        raise Conflict('settings permissions must be a JSON object')
    for key in ('allow', 'ask', 'deny'):
        rules = permissions.get(key, [])
        if not isinstance(rules, list) or any(not isinstance(rule, str) for rule in rules):
            raise Conflict(f'settings permissions.{key} must be a list of strings')
    return data


def permission_value(data, mode=0o600):
    return file_value(json.dumps(data, indent=2) + '\n', mode)


def permission_matches(data, present, absent=()):
    rules = data.get('permissions', {}).get('allow', [])
    return all(rules.count(rule) == 1 for rule in present) and all(rule not in rules for rule in absent)


def restore_permissions(op, current):
    """Reverse only owned allow-list entries, retaining later user settings."""
    data = permission_data(current)
    before, after = set(op['before_rules']), set(op['after_rules'])
    if permission_matches(data, before, after - before):
        return current  # Already recovered, including a partial transaction.
    if not permission_matches(data, after, before - after):
        raise Conflict(f'{op["path"]}: managed permission changed since transaction')
    if current == op['after']:
        restored = dict(op['before'])
        if restored['kind'] == 'file':
            restored['mode'] = current.get('mode', restored['mode'])
        return restored
    permissions = data.setdefault('permissions', {})
    rules = permissions.setdefault('allow', [])
    rules[:] = [rule for rule in rules if rule not in after - before]
    rules.extend(rule for rule in op['before_rules'] if rule not in rules)
    original = permission_data(op['before'])
    if not rules and 'allow' not in original.get('permissions', {}):
        del permissions['allow']
    if not permissions and 'permissions' not in original:
        del data['permissions']
    if not data and op['before']['kind'] == 'absent':
        return {'kind': 'absent'}
    return permission_value(data, current.get('mode', 0o600))


def block(text, kind='section'):
    begin, end = ('# agent-workbench:begin', '# agent-workbench:end') if kind == 'toml-section' else (BEGIN, END)
    if text.count(begin) != text.count(end) or text.count(begin) > 1:
        raise Conflict('ambiguous managed section markers')
    if begin not in text:
        return None
    a, b = text.index(begin), text.index(end)
    if b < a:
        raise Conflict('reversed managed section markers')
    return text[a:b + len(end)]


def section(text, kind='section'):
    begin, end = ('# agent-workbench:begin', '# agent-workbench:end') if kind == 'toml-section' else (BEGIN, END)
    return begin + '\n' + text.rstrip() + '\n' + end


def replace_block(text, old, new):
    if old:
        return text.replace(old, new or '', 1)
    return text + ('\n\n' if text and not text.endswith('\n\n') else '') + (new or '') + '\n'


def write_value(path, value, archive=None):
    safe_parent(path)
    if path.is_dir() and not path.is_symlink():
        if archive is None:
            raise Conflict(f'{path}: directory replacement requires a journaled archive destination')
        safe_parent(archive)
        if archive.exists() or archive.is_symlink():
            raise Conflict(f'{archive}: archive destination already exists')
        archive.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Atomic retirement, no recursive deletion and no following linked descendants.
        # Cross-filesystem rename fails before changing the source directory.
        os.replace(path, archive)
        for parent in [path.parent, archive.parent]:
            fd = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
    if value['kind'] == 'absent':
        if path.exists() or path.is_symlink():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if value['kind'] == 'tree':
        temp = Path(tempfile.mkdtemp(prefix='.awb-', dir=path.parent))
        try:
            for name, child in value['children'].items():
                if Path(name).name != name or name in {'.', '..'}:
                    raise Conflict('unsafe archived tree entry')
                write_value(temp / name, child)
            temp.chmod(value['mode'])
            if path.exists() or path.is_symlink():
                path.unlink()
            os.replace(temp, path)
        finally:
            if temp.exists():
                shutil.rmtree(temp)
        return
    fd, name = tempfile.mkstemp(prefix='.awb-', dir=path.parent)
    temp = Path(name)
    try:
        if value['kind'] == 'link':
            os.close(fd)
            temp.unlink()
            temp.symlink_to(value['target'])
        else:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(base64.b64decode(value['data']))
                stream.flush()
                os.fsync(stream.fileno())
            temp.chmod(value['mode'])
        os.replace(temp, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temp.exists() or temp.is_symlink():
            temp.unlink()


def digest(files):
    h = hashlib.sha256()
    for name, data in sorted(files.items()):
        h.update(name.encode() + b'\0' + data.encode() + b'\0')
    return h.hexdigest()


def matches(path, entry):
    current = snapshot(path, tree=entry['type'] == 'tree')
    if entry['type'] == 'json-permissions':
        return current['kind'] == 'file' and permission_matches(permission_data(current), entry['rules'])
    if entry['type'] in SECTION_TYPES:
        return current['kind'] == 'file' and block(decode(current), entry['type']) == entry['block']
    return current == entry['expected']


def inverse(op):
    """Restore changed bytes only; preserve edits outside a managed section."""
    path = Path(op['path'])
    current = snapshot(path, tree=True)
    if current == op['before']:
        return current  # Mutation was not reached, or already recovered.
    if op['type'] == 'json-permissions':
        return restore_permissions(op, current)
    if op['type'] == 'tree' and current['kind'] == 'absent':
        # A directory was atomically archived before its replacement was written.
        return op['before']
    if op['type'] in SECTION_TYPES and current['kind'] == 'file':
        text = decode(current)
        found = block(text, op['type'])
        after_block = op['after_block']
        if found == op['before_block']:
            return current
        if found != after_block:
            raise Conflict(f'{path}: managed section changed since transaction')
        if current == op['after']:
            restored = dict(op['before'])
            if restored['kind'] == 'file':
                restored['mode'] = current['mode']
            return restored
        if op['type'] == 'reset-section' and op['before']['kind'] == 'link':
            raise Conflict(f'{path}: restoring an instruction symlink would lose later outside edits; preserve them and resolve manually')
        result = replace_block(text, after_block, op['before_block'])
        if op['type'] == 'reset-section' and op['before']['kind'] == 'file':
            # The initial reset removed old prose; restore it alongside later outside edits.
            result = decode(op['before']) + '\n' + result
        return file_value(result, current['mode'])
    if current != op['after']:
        raise Conflict(f'{path}: changed since transaction; preserve it and resolve manually')
    return op['before']
