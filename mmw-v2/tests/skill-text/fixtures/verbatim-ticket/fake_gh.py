#!/usr/bin/env python3
"""Serve a ticket body and record the requested public gh command."""
import json
import os
from pathlib import Path
import sys

args = sys.argv[1:]
Path(os.environ['VERBATIM_GH_CALL']).write_text(json.dumps(args), encoding='utf-8')
if args[:3] != ['issue', 'view', '603'] or args[3:] != ['--json', 'body']:
    print('unexpected gh arguments', file=sys.stderr)
    sys.exit(2)
if os.environ.get('VERBATIM_GH_FAIL'):
    print('fixture tracker unavailable', file=sys.stderr)
    sys.exit(1)
if 'VERBATIM_GH_RESPONSE' in os.environ:
    print(os.environ['VERBATIM_GH_RESPONSE'])
    sys.exit(0)
print(json.dumps({'body': Path(os.environ['VERBATIM_GH_BODY']).read_bytes().decode('utf-8')}))
