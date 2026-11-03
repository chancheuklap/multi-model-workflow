#!/usr/bin/env bash
# Install the cloud edition into the current Git repository's .cursor directory.
set -euo pipefail

ref=""
case "$#" in
  0) ;;
  2) if [[ "$1" == --ref && -n "$2" ]]; then ref="$2"; else echo 'usage: install-mmw-v5-cloud.sh [--ref BRANCH_OR_TAG_OR_SHA]' >&2; exit 2; fi ;;
  *) echo 'usage: install-mmw-v5-cloud.sh [--ref BRANCH_OR_TAG_OR_SHA]' >&2; exit 2 ;;
esac

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

python3 - "$temporary/cloud.zip" "$project" "$ref" <<'PY'
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

archive, project, ref = sys.argv[1:]
destination = Path(project) / '.cursor'
with zipfile.ZipFile(archive) as package:
    if ref:
        prefix = package.namelist()[0].split('/')[0] + '/mmw-v5-cloud/'
    else:
        prefix = '.cursor/'
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
        target.write_bytes(package.read(member))
        mode = (member.external_attr >> 16) & 0o777
        if mode:
            target.chmod(mode)
        installed += 1
print(f'Installed MMW v5 Cloud {manifest["version"]} into {destination} ({installed} files)')
print('Commit and push .cursor/ so Cloud Workers receive the same runtime.')
PY
