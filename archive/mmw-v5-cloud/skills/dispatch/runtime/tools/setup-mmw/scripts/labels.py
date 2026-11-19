#!/usr/bin/env python3
"""Create missing labels from the shared definitions; no event-based migration."""
import importlib.util
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'dispatch/scripts'))
from status import GitHub, command


def main():
    api = GitHub()
    path = Path(__file__).resolve().parents[2] / 'verify-ticket/scripts/labels.py'
    spec = importlib.util.spec_from_file_location('mmw_cloud_labels', path)
    definitions = importlib.util.module_from_spec(spec); spec.loader.exec_module(definitions)
    existing = {item['name'] for item in api.listing('labels')}
    for name, (color, description) in definitions.LABELS.items():
        if name not in existing:
            command('gh', 'label', 'create', name, '--repo', api.repo, '--color', color, '--description', description)
            print(name)

if __name__ == '__main__':
    try: main()
    except (OSError, ValueError, RuntimeError) as exc: sys.exit(f'labels: {exc}')
