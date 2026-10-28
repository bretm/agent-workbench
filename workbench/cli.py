"""Small declarative installer: planning is read-only, mutations require --apply."""
import argparse
import difflib
import json
import os
from pathlib import Path
import subprocess
import sys

from .planner import (Conflict, alternate_skill_roots, empty_state, harness_root,
                      installation, pack, read_json, removal, select_harnesses, validate)
from .storage import decode, digest, matches, snapshot
from .transactions import apply, locked, pending, recovery_plan, restore
from .reset import inventory, reset_installation, reset_health

SOURCE = Path(__file__).resolve().parents[1]


def parser():
    p = argparse.ArgumentParser(description='Agent Workbench: portable interactive coding workflow. Plans are read-only by default.')
    commands = p.add_subparsers(dest='command', required=True)
    commands.add_parser('context', help='Set up, inspect, update or migrate private context (context --help)')
    descriptions = {
        'install': 'Configure detected installed clients on first install, or explicitly selected targets',
        'reset-workflow': 'Preview an exact reviewed retirement of personal workflow, then install the clean baseline',
        'update': 'Update owned content and previously selected targets',
        'check': 'Check ownership, drift, discovery, prerequisites and stale content (no writes)',
        'uninstall': 'Remove all owned changes, restoring prior files/links while preserving user edits',
        'rollback': 'Undo the most recent active transaction',
        'recover': 'Reverse an interrupted apply or rollback from its durable journal',
        'discover': 'Suggest Git repositories and inspect skill links; never selects targets',
        'validate': 'Validate canonical skill metadata, references, dependencies and adapters',
    }
    for name, description in descriptions.items():
        sub = commands.add_parser(name, help=description, description=description)
        sub.add_argument('--home', type=Path, default=Path.home(), help='Target user home; use a temporary directory for fixtures')
        sub.add_argument('--context-dir', type=Path, help='Private context outside Git; default HOME/.agents/agent-workbench')
        sub.add_argument('--state-dir', type=Path, help='Local state/backups; default HOME/.local/state/agent-workbench')
        sub.add_argument('--source', type=Path, default=SOURCE, help='Canonical workbench checkout')
        sub.add_argument('--config', type=Path, help='Local JSON: harnesses, homes, repositories, migrations or reviewed workflow_reset inventory')
        sub.add_argument('--harness', action='append', help='Repeat to select clients; otherwise use recorded targets or detect installed clients on PATH')
        sub.add_argument('--repo', action='append', default=[], help='Explicit Git repository/worktree root; repeatable')
        sub.add_argument('--harness-home', action='append', default=[], metavar='NAME=PATH', help='Explicit configurable home for any adapter; repeatable')
        sub.add_argument('--codex-home', type=Path, help='Explicit Codex home; otherwise CODEX_HOME or HOME/.codex')
        sub.add_argument('--claude-home', type=Path, help='Explicit Claude home; otherwise CLAUDE_CONFIG_DIR or HOME/.claude')
        mode = sub.add_mutually_exclusive_group()
        mode.add_argument('--apply', action='store_true', help='Apply printed plan without prompting (noninteractive)')
        mode.add_argument('--interactive', action='store_true', help='Print plan, then ask one yes/no confirmation')
        mode.add_argument('--dry-run', action='store_true', help='Explicit read-only preview (default)')
        sub.add_argument('--diff', action='store_true', help='Show content diffs for planned regular-file changes (may include existing private instructions)')
        sub.add_argument('--root', type=Path, help='discover only: candidate parent; default HOME/git')
        if name == 'reset-workflow':
            sub.add_argument('--inventory', action='store_true', help='Print local review JSON (read-only); redirect stdout to a local file')
    return p


def load_state(directory):
    state = read_json(directory / 'state.json', empty_state())
    if state.get('schema') != 1:
        raise Conflict('unsupported installation state schema')
    return state


def confirmed(args):
    if args.apply:
        return True
    if args.interactive:
        if not sys.stdin.isatty():
            raise Conflict('--interactive requires a terminal; use --apply for noninteractive operation')
        return input('Apply this plan? [y/N] ').strip().lower() == 'y'
    return False


def local_config(args):
    if args.config and not args.config.expanduser().is_file():
        raise Conflict(f'{args.config}: local configuration file does not exist')
    config = read_json(args.config.expanduser().resolve(), {}) if args.config else {}
    if not isinstance(config, dict) or set(config) - {'harnesses', 'homes', 'repositories', 'migrations', 'workflow_reset'}:
        raise Conflict('local configuration must be an object with harnesses/homes/repositories/migrations/workflow_reset')
    if 'harnesses' in config and not config['harnesses']:
        raise Conflict('select at least one harness; an empty harness list does not mean all')
    seen = set()
    for m in config.get('migrations', []):
        if not isinstance(m, dict) or set(m) != {'path', 'target', 'action'} or m['action'] not in {'replace', 'retire'}:
            raise Conflict('migration requires path, literal target and action replace/retire')
        if not isinstance(m['path'], str) or not isinstance(m['target'], str):
            raise Conflict('migration paths and targets must be strings')
        if m['path'] in seen:
            raise Conflict('duplicate migration path')
        seen.add(m['path'])
    return config


def discover(args, home, source):
    root = (args.root or home / 'git').expanduser().resolve()
    print(f'Candidates under {root} (not selected):')
    if root.is_dir():
        for p in sorted(root.iterdir()):
            if p.is_dir():
                r = subprocess.run(['git', '-C', str(p), 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
                if not r.returncode and Path(r.stdout.strip()).resolve() == p.resolve():
                    print(f'  {p}')
    else:
        print('  directory unavailable; discovery outstanding')
    config = local_config(args)
    manifest = validate(source)
    overrides = {**config.get('homes', {})}
    for name, value in [('codex', args.codex_home), ('claude', args.claude_home)]:
        if value:
            overrides[name] = str(value)
    for item in args.harness_home:
        name, sep, value = item.partition('=')
        if not sep or name not in manifest['harnesses'] or not value:
            raise Conflict('--harness-home requires a supported NAME=PATH')
        overrides[name] = value
    directories = set()
    for name in manifest['harnesses']:
        a = read_json(source / 'adapters' / f'{name}.json')
        harness_home = harness_root(a, home, overrides.get(name))
        directories.add((home if a['skill_scope'] == 'user' else harness_home) / a['skill_directory'])
        directories.update(alternate_skill_roots(a, harness_home))
    for directory in sorted(directories):
        if directory.is_dir():
            for p in sorted(directory.iterdir()):
                if p.is_symlink():
                    print(f'LINK {p} -> {os.readlink(p)}' + (' [BROKEN]' if not p.exists() else ''))
    print('Select repositories explicitly with --repo or a local configuration file. No candidate has been selected.')
    return 0


def run(args):
    if sys.version_info < (3, 11) or sys.platform not in {'linux', 'darwin'}:
        raise Conflict('v1 supports Linux (including Linux under WSL) and macOS with Python 3.11+; other platforms are unsupported')
    home = args.home.expanduser().resolve()
    source = args.source.expanduser().resolve()
    directory = (args.state_dir or home / '.local/state/agent-workbench').expanduser().absolute()
    if args.command in {'discover', 'validate', 'check'} and (args.apply or args.interactive):
        raise Conflict(f'{args.command} is read-only; --apply/--interactive do not apply')
    manifest = validate(source) if args.command not in {'uninstall', 'recover', 'rollback'} else {'harnesses': []}
    if args.command == 'validate':
        print(f'Valid: {len(manifest["skills"])} portable skills, references, dependency closure and adapters')
        return 0
    if args.command == 'discover':
        return discover(args, home, source)
    state = load_state(directory)
    if args.command in {'recover', 'rollback'}:
        paths = pending(directory)
        if args.command == 'rollback':
            if paths:
                raise Conflict('incomplete transaction: use recover first')
            history = state.get('history', [])
            paths = [directory / 'transactions' / f'{history[-1]}.json'] if history else []
        if not paths:
            print('No transaction to restore.')
            return 0
        conflicts = []
        for path in paths:
            journal, operations, errors = recovery_plan(path)
            print(f'RESTORE transaction {journal["id"]}')
            for p, _, _ in operations:
                print(f'  restore {p}')
            conflicts.extend(errors)
        if conflicts:
            for error in conflicts:
                print('CONFLICT ' + error)
            return 2
        if confirmed(args):
            with locked(directory):
                # Re-evaluate under lock; restoration verifies every destination again.
                if args.command == 'rollback' and load_state(directory) != state:
                    raise Conflict('state changed since preview')
                for path in paths:
                    restore(path, directory)
            print('Restored. Backups and journals retained.')
        else:
            print('Preview only; add --apply or --interactive.')
        return 0
    if pending(directory):
        raise Conflict('incomplete transaction: run recover (preview), then recover --apply')
    config = local_config(args)
    from .context import context_root
    if args.command != 'uninstall':
        config['context_dir'] = str(context_root(args.context_dir or os.environ.get('AWB_CONTEXT_DIR') or state.get('context_dir'), home))
    homes = {name: str(value.expanduser().absolute()) for name, value in [('codex', args.codex_home), ('claude', args.claude_home)] if value}
    for item in args.harness_home:
        name, separator, value = item.partition('=')
        if not separator or name not in manifest['harnesses'] or not value:
            raise Conflict('--harness-home requires a supported NAME=PATH')
        homes[name] = str(Path(value).expanduser().absolute())
    homes = {**state.get('homes', {}), **config.get('homes', {}), **homes}
    if args.command == 'reset-workflow' and args.inventory:
        if args.apply or args.interactive:
            raise Conflict('--inventory is read-only')
        selected = select_harnesses(source, manifest, args.harness, config, state, workflow_reset=True)
        result = {'harnesses': selected, 'repositories': [],
                  'workflow_reset': inventory(source, home, state, selected, homes)}
        print(json.dumps(result, indent=2))
        return 0
    if 'workflow_reset' in config and args.command not in {'reset-workflow', 'check'}:
        raise Conflict('workflow_reset is only valid with reset-workflow/check; ordinary installation does not retire unowned content')
    if args.command == 'uninstall':
        plan = removal(state)
    else:
        if args.command == 'update':
            config = dict(config)
            if not args.repo and 'repositories' not in config:
                config['repositories'] = state['repositories']
        if args.command == 'check' and not state['entries']:
            print('Not installed. Use install to preview bootstrap.')
            return 1
        # Recorded per-harness roots are used on update/check unless explicitly overridden.
        homes = {**state.get('homes', {}), **config.get('homes', {}), **homes}
        builder = reset_installation if args.command == 'reset-workflow' else installation
        plan = builder(source, home, directory, state, config, args.harness,
                            args.repo or (state['repositories'] if args.command == 'check' else []), homes)
        plan.next['homes'] = homes
        # Derive actual roots for future runs including environment overrides.
        for name in plan.next['harnesses']:
            a = read_json(source / 'adapters' / f'{name}.json')
            plan.next['homes'][name] = str(harness_root(a, home, homes.get(name)))
        if args.command in {'check', 'update', 'install'}:
            health_harnesses = args.harness or config.get('harnesses') or plan.next['harnesses']
            plan.conflicts.extend(reset_health(source, home, state, health_harnesses, plan.next['homes']))
    for message in plan.messages:
        if not message.startswith('OK ') or args.command == 'check':
            print(message)
    if args.diff:
        for op in plan.operations:
            if op['after']['kind'] != 'file':
                continue
            before_text = decode(op['before']) if op['before']['kind'] == 'file' else ''
            after_text = decode(op['after'])
            if op['type'] == 'toml-section':
                before_text = (op['before_block'] or '') + '\n'
                after_text = (op['after_block'] or '') + '\n'
            print(''.join(difflib.unified_diff(before_text.splitlines(True), after_text.splitlines(True),
                                              fromfile=op['path'] + ' (before)', tofile=op['path'] + ' (planned)')), end='')
    for error in plan.conflicts:
        print('CONFLICT ' + error)
    print(f'{len(plan.operations)} change(s), {len(plan.conflicts)} conflict(s).')
    if plan.conflicts:
        return 2
    if args.command == 'check':
        if plan.operations:
            print('Installation stale or incomplete; preview update.')
            return 1
        print('Installation healthy; content matches this checkout.')
        return 0
    if confirmed(args):
        with locked(directory):
            txid = apply(plan, directory)
        print('Applied transaction ' + txid if txid else 'Already up to date.')
    else:
        print('Preview only; add --apply or --interactive.')
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == 'context':
        from .context import main as context_main
        return context_main(argv[1:])
    args = parser().parse_args(argv)
    try:
        return run(args)
    except (Conflict, OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        print(f'ERROR {exc}', file=sys.stderr)
        return 2 if isinstance(exc, Conflict) else 3
