"""Durable write-ahead journal; backups contain exact prior bytes and permissions."""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import uuid

from .storage import Conflict, file_value, inverse, safe_parent, snapshot, write_value
from .planner import read_json


def save(path, data):
    write_value(path, file_value(json.dumps(data, indent=2) + '\n', 0o600))


@contextmanager
def locked(directory):
    safe_parent(directory / 'lock')
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (directory / 'lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Conflict('another workbench mutation is running') from None
        yield


def pending(directory):
    return [p for p in sorted((directory / 'transactions').glob('*.json'))
            if read_json(p)['status'] == 'pending']


def apply(plan, directory, fail_after=None):
    if plan.conflicts:
        raise Conflict('resolve all plan conflicts before applying')
    if pending(directory):
        raise Conflict('incomplete transaction: run recover --apply first')
    on_disk = read_json(directory / 'state.json', None)
    # A preview is never permission to apply a now-stale plan.
    if on_disk is not None and on_disk != plan.previous:
        raise Conflict('installation state changed while planning; re-plan')
    for op in plan.operations:
        if snapshot(Path(op['path']), tree=True) != op['before']:
            raise Conflict(f'{op["path"]}: changed while planning')
        if op['before']['kind'] == 'tree':
            ancestor = directory
            while not ancestor.exists():
                ancestor = ancestor.parent
            if os.stat(op['path']).st_dev != ancestor.stat().st_dev:
                raise Conflict(f'{op["path"]}: atomic directory archive requires state on the same filesystem; choose --state-dir accordingly')
    if not plan.operations and plan.next == plan.previous:
        return None
    txid = uuid.uuid4().hex
    path = directory / 'transactions' / f'{txid}.json'
    next_state = dict(plan.next)
    next_state['history'] = plan.previous.get('history', []) + [txid]
    journal = {'schema': 1, 'id': txid, 'status': 'pending', 'previous': plan.previous,
               'next': next_state, 'operations': plan.operations}
    save(path, journal)  # All preimages durable before the first destination changes.
    try:
        for i, op in enumerate(plan.operations, 1):
            if snapshot(Path(op['path']), tree=True) != op['before']:
                raise Conflict(f'{op["path"]}: changed during transaction')
            write_value(Path(op['path']), op['after'], archive=directory / 'archives' / txid / f'{i}-apply')
            if fail_after == i:
                raise OSError('injected transaction failure')
        save(directory / 'state.json', next_state)
        journal['status'] = 'complete'
        save(path, journal)
    except BaseException:
        # Leave the journal pending even if an interrupt happened between write and bookkeeping.
        # Recovery recognizes preimages/postimages rather than trusting a progress counter.
        raise
    return txid


def recovery_plan(path):
    journal = read_json(path)
    operations = []
    conflicts = []
    for op in reversed(journal['operations']):
        try:
            current = snapshot(Path(op['path']), tree=True)
            restored = inverse(op)
            if current != restored:
                operations.append((Path(op['path']), current, restored))
        except (Conflict, OSError, ValueError) as exc:
            conflicts.append(str(exc))
    return journal, operations, conflicts


def restore(path, directory):
    journal, operations, conflicts = recovery_plan(path)
    if conflicts:
        raise Conflict('\n'.join(conflicts))
    # Mark pending before rollback too: interrupted rollback uses the same inverse journal.
    journal['status'] = 'pending'
    save(path, journal)
    for i, (p, current, restored) in enumerate(operations):
        if snapshot(p, tree=current['kind'] == 'tree' or restored['kind'] == 'tree') != current:
            raise Conflict(f'{p}: changed during recovery; re-run recover')
        write_value(p, restored, archive=directory / 'archives' / journal['id'] / f'{i}-restore')
    save(directory / 'state.json', journal['previous'])
    journal['status'] = 'reverted'
    save(path, journal)
