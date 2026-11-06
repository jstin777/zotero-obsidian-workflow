#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
PYTHON=${WORKFLOW_PYTHON:-python3.12}
"$PYTHON" -c 'import sys; assert sys.version_info >= (3,12), "Python 3.12+ required"'
"$PYTHON" -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
printf '%s\n' 'Installed base dependencies. Next: .venv/bin/python tools/workflow.py init --list-collections'
