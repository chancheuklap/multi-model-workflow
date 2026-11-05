#!/usr/bin/env bash
# Install MMW for this machine's user; --cloud installs in the isolated project.
set -euo pipefail

host=""
cloud=0
usage() { echo 'usage: install-mmw-v5-cloud.sh --host cursor|codex [--cloud]' >&2; exit 2; }
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --host) [[ "$#" -ge 2 && -z "$host" ]] || usage; host="$2"; shift 2 ;;
    --cloud) [[ "$cloud" == 0 ]] || usage; cloud=1; shift ;;
    *) usage ;;
  esac
done
[[ "$host" == cursor || "$host" == codex ]] || usage

project="$(git rev-parse --show-toplevel)"
temporary="$(mktemp -d)"
trap 'rm -rf "$temporary"' EXIT
curl -fsSL https://github.com/chancheuklap/multi-model-workflow/releases/latest/download/mmw-v5-cloud.zip -o "$temporary/cloud.zip"

python3 - "$temporary/cloud.zip" "$project" "$host" "$cloud" <<'PY'
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
import zipfile

archive, project, host, cloud = sys.argv[1:]
project = Path(project)
user_agents = project / '.agents' if cloud == '1' else Path.home() / '.agents'
runtime = user_agents / 'mmw'
skills = user_agents / 'skills' / 'mmw'
configuration = project / '.agents' / 'models.json'
environment = project / '.cursor' / 'environment.json'
settings = None
if cloud == '1' and host == 'cursor':
    settings = json.loads(environment.read_text()) if environment.exists() else {}
    for field in ('install', 'start'):
        if field in settings and not isinstance(settings[field], str):
            raise SystemExit(f'{environment}: {field} must be a shell command string')

staging = Path(archive).parent / 'payload'
with zipfile.ZipFile(archive) as package:
    prefix = 'mmw-v5-cloud/'
    manifest = json.loads(package.read(prefix + 'plugin.json'))
    if manifest['name'] != 'mmw-v5-cloud':
        raise SystemExit('The download is not the MMW v5 cloud edition')
    defaults = package.read(prefix + 'models.json')
    for member in package.infolist():
        if member.is_dir() or not member.filename.startswith(prefix):
            continue
        relative = PurePosixPath(member.filename[len(prefix):])
        if relative.is_absolute() or '..' in relative.parts:
            raise SystemExit('Invalid archive path: ' + str(relative))
        if str(relative) == 'models.json':
            continue
        target = staging / str(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(package.read(member))
        mode = (member.external_attr >> 16) & 0o777
        if mode:
            target.chmod(mode)

if configuration.exists():
    print('Keep existing configuration: ' + str(configuration))
else:
    legacy = project / '.cursor' / 'models.json'
    if legacy.exists():
        previous = json.loads(legacy.read_text())
        value = json.loads(defaults)
        for old_host in ('cursor', 'codex'):
            if isinstance(previous.get('rows', {}).get(old_host), dict):
                value['rows'][old_host] = previous['rows'][old_host]
        defaults = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    configuration.parent.mkdir(parents=True, exist_ok=True)
    configuration.write_bytes(defaults)

# These two directories belong to MMW. Project and other personal skills live outside them.
for target in (runtime, skills):
    if target.is_symlink():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
shutil.move(str(staging / 'skills'), str(skills))
shutil.move(str(staging), str(runtime))

tracked = ['.agents/models.json']
if cloud == '1':
    ignore = project / '.gitignore'
    before = ignore.read_text() if ignore.exists() else ''
    begin, end = '# MMW cloud BEGIN', '# MMW cloud END'
    block = begin + '\n/.agents/mmw/\n/.agents/skills/mmw/\n' + end + '\n'
    if begin in before:
        start = before.index(begin)
        stop = before.index(end, start) + len(end)
        after = before[:start] + block.rstrip('\n') + before[stop:]
    else:
        after = before.rstrip() + ('\n\n' if before.strip() else '') + block
    ignore.write_text(after)
    tracked.append('.gitignore')
    setup = project / '.agents' / 'cloud-setup.sh'
    setup.write_text('''#!/usr/bin/env bash
# Prepare MMW in this isolated cloud checkout before a new task starts.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host ''' + host + ' --cloud\n')
    setup.chmod(0o755)
    tracked.append('.agents/cloud-setup.sh')
    command = 'bash .agents/cloud-setup.sh'
    if host == 'cursor':
        for field in ('install', 'start'):
            before = settings.get(field, '')
            if command not in before:
                settings[field] = command + (' && (\n' + before + '\n)' if before.strip() else '')
        environment.parent.mkdir(parents=True, exist_ok=True)
        environment.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + '\n')
        tracked.append('.cursor/environment.json')
        print('Bind .cursor/environment.json to the saved Cursor environment and complete its Build.')
    else:
        print('Codex setup agent: save `bash .agents/cloud-setup.sh` in Install script and in the new-task Start skill, then publish.')

print(f'Installed MMW v5 Cloud {manifest["version"]} into {user_agents}')
print('Skills: ' + str(skills))
print('Tools and board: ' + str(runtime))
print('Commit and push project configuration only: ' + ', '.join(tracked))
PY
