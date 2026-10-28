#!/usr/bin/env python3
"""Agent Workbench CLI, Python 3.11+, no third-party dependencies."""
import sys

if sys.platform not in {'linux', 'darwin'} or sys.version_info < (3, 11):
    print('agent-workbench v1 requires Linux or macOS and Python 3.11+', file=sys.stderr)
    raise SystemExit(2)

from workbench.cli import main

if __name__ == '__main__':
    raise SystemExit(main())
