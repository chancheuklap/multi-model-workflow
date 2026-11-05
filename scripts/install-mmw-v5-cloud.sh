#!/usr/bin/env bash
# Install the complete cloud edition into the project's native host directory.
set -euo pipefail

ref=""
host=""
usage() { echo 'usage: install-mmw-v5-cloud.sh --host cursor|codex [--ref BRANCH_OR_TAG_OR_SHA]' >&2; exit 2; }
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --host) [[ "$#" -ge 2 && -z "$host" ]] || usage; host="$2"; shift 2 ;;
    --ref) [[ "$#" -ge 2 && -n "$2" && -z "$ref" ]] || usage; ref="$2"; shift 2 ;;
    *) usage ;;
  esac
done
[[ "$host" == cursor || "$host" == codex ]] || usage

project="$(git rev-parse --show-toplevel)"
temporary="$(mktemp -d)"
trap 'rm -rf "$temporary"' EXIT
repository="chancheuklap/multi-model-workflow"

if [[ -n "$ref" ]]; then
  # Development installs use a GitHub snapshot, never a local source checkout.
  curl -fsSL "https://api.github.com/repos/$repository/zipball/$ref" -o "$temporary/cloud.zip"
else
  curl -fsSL "https://raw.githubusercontent.com/$repository/main/mmw-v5-cloud/plugin.json" -o "$temporary/plugin.json"
  version="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$temporary/plugin.json")"
  curl -fsSL "https://github.com/$repository/releases/download/v$version/mmw-v5-cloud-$version.zip" -o "$temporary/cloud.zip"
fi

python3 - "$temporary/cloud.zip" "$project" "$ref" "$host" <<'PY'
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

archive, project, ref, host = sys.argv[1:]
destination = Path(project) / ('.agents' if host == 'codex' else '.cursor')
with zipfile.ZipFile(archive) as package:
    if ref:
        prefix = package.namelist()[0].split('/')[0] + '/mmw-v5-cloud/'
    else:
        prefix = 'mmw-v5-cloud/'
    manifest = json.loads(package.read(prefix + 'plugin.json'))
    if manifest['name'] != 'mmw-v5-cloud':
        raise SystemExit('The download is not the MMW v5 cloud edition')
    installed = 0
    for member in package.infolist():
        if member.is_dir() or not member.filename.startswith(prefix):
            continue
        relative = PurePosixPath(member.filename[len(prefix):])
        if relative.is_absolute() or '..' in relative.parts:
            raise SystemExit('Invalid archive path: ' + str(relative))
        if relative.parts[0] not in ('skills', 'tools', 'board', 'models.json', 'plugin.json'):
            continue
        target = destination / str(relative)
        if str(relative) == 'models.json' and target.exists():
            print('Keep existing configuration: ' + str(target))
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        content = package.read(member)
        if str(relative) == 'models.json' and host == 'codex':
            legacy = Path(project) / '.cursor' / 'models.json'
            if legacy.exists():
                previous = json.loads(legacy.read_text(encoding='utf-8'))
                settings = json.loads(content)
                if isinstance(previous.get('rows', {}).get('codex'), dict):
                    settings['rows']['codex'] = previous['rows']['codex']
                    content = (json.dumps(settings, ensure_ascii=False, indent=2) + '\n').encode()
        target.write_bytes(content)
        mode = (member.external_attr >> 16) & 0o777
        if mode:
            target.chmod(mode)
        installed += 1
print(f'Installed MMW v5 Cloud {manifest["version"]} into {destination} ({installed} files)')
print(f'Commit and push {destination.name}/ so Cloud Workers receive the same runtime.')
PY
