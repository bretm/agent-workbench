#!/usr/bin/env python3
"""Installed private-context and guidance tools; Python standard library only."""
import sys
from workbench import context, model_guidance

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in {'context', 'models'}:
        raise SystemExit('Usage: awb-local.py context ACTION ... | models ...')
    command = sys.argv[1]
    raise SystemExit((context.main if command == 'context' else model_guidance.main)(sys.argv[2:]))
