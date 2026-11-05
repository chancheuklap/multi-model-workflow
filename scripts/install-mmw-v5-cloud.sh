#!/usr/bin/env bash
# Install one complete MMW runtime in this machine user's ~/.agents.
set -euo pipefail

host=""
cloud=0
projects=()
usage() { echo 'usage: install-mmw-v5-cloud.sh --host cursor|codex [--cloud] [REPOSITORY ...]' >&2; exit 2; }
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --host) [[ "$#" -ge 2 && -z "$host" ]] || usage; host="$2"; shift 2 ;;
    --cloud) [[ "$cloud" == 0 ]] || usage; cloud=1; shift ;;
    --*) usage ;;
    *) projects+=("$1"); shift ;;
  esac
done
[[ "$host" == cursor || "$host" == codex ]] || usage
if [[ ${#projects[@]} == 0 ]]; then
  if project="$(git rev-parse --show-toplevel 2>/dev/null)"; then projects+=("$project"); else projects+=(""); fi
fi
for index in "${!projects[@]}"; do
  if [[ -n "${projects[$index]}" ]]; then
    projects[index]="$(git -C "${projects[$index]}" rev-parse --show-toplevel)"
  fi
done
temporary="$(mktemp -d)"
trap 'rm -rf "$temporary"' EXIT
curl -fsSL https://github.com/chancheuklap/multi-model-workflow/releases/latest/download/mmw-v5-cloud.zip -o "$temporary/cloud.zip"

python3 - "$temporary/cloud.zip" "$host" "$cloud" "${projects[@]}" <<'PY'
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import zipfile

archive, host, cloud, *roots = sys.argv[1:]
projects = list(dict.fromkeys(Path(root).resolve() for root in roots if root))
user_agents = Path.home() / '.agents'
runtime = user_agents / 'mmw'
skills = user_agents / 'skills' / 'mmw'
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

setup_text = '''#!/usr/bin/env bash
# Prepare one user-level MMW installation for all repositories in this environment.
set -euo pipefail
host="${1:-codex}"
if [[ "$#" -gt 0 ]]; then shift; fi
if [[ "$#" == 0 ]]; then set -- "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; fi
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host "$host" "$@"
'''


def remove(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


# Validate every project before replacing the shared installation.
environments = {}
for project in projects:
    environment = project / '.cursor/environment.json'
    if cloud == '1' and host == 'cursor':
        value = json.loads(environment.read_text()) if environment.exists() else {}
        for field in ('install', 'start'):
            if field in value and not isinstance(value[field], str):
                raise SystemExit(f'{environment}: {field} must be a shell command string')
        environments[project] = value
    configuration = project / '.agents/models.json'
    if not configuration.exists():
        value = json.loads(defaults)
        legacy = project / '.cursor/models.json'
        if legacy.exists():
            previous = json.loads(legacy.read_text())
            for old_host in ('cursor', 'codex'):
                if isinstance(previous.get('rows', {}).get(old_host), dict):
                    value['rows'][old_host] = previous['rows'][old_host]
        configuration.parent.mkdir(parents=True, exist_ok=True)
        configuration.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    else:
        print('Keep existing configuration: ' + str(configuration))

skill_names = {path.name for path in (staging / 'skills').iterdir()}
for target in (runtime, skills):
    remove(target)
    target.parent.mkdir(parents=True, exist_ok=True)
shutil.move(str(staging / 'skills'), str(skills))
shutil.move(str(staging), str(runtime))

for project in projects:
    # Remove MMW-owned project copies, preserving project skills and model choices.
    for directory in ('.agents', '.cursor'):
        old = project / directory
        for relative in ('mmw', 'skills/mmw'):
            remove(old / relative)
        legacy_manifest = old / 'plugin.json'
        if legacy_manifest.exists() and json.loads(legacy_manifest.read_text()).get('name') == 'mmw-v5-cloud':
            for name in skill_names:
                remove(old / 'skills' / name)
            for relative in ('board', 'tools/dispatch', 'tools/setup-mmw', 'tools/verify-ticket', 'plugin.json', '.cursor-plugin'):
                remove(old / relative)
        legacy_models = old / 'models.json'
        if directory == '.cursor' and legacy_models.exists():
            value = json.loads(legacy_models.read_text())
            if isinstance(value.get('rows'), dict) and {'cursor', 'codex'} & value['rows'].keys():
                legacy_models.unlink()
    ignore = project / '.gitignore'
    if ignore.exists():
        before = ignore.read_text()
        after = re.sub(r'(?m)^# MMW cloud BEGIN\n.*?^# MMW cloud END\n?', '', before, flags=re.S)
        if after != before:
            ignore.write_text(after.rstrip() + '\n')
    setup = project / '.agents/cloud-setup.sh'
    if cloud == '1' or setup.exists():
        setup.write_text(setup_text)
        setup.chmod(0o755)
    if project in environments:
        settings = environments[project]
        command = 'bash .agents/cloud-setup.sh cursor'
        for field in ('install', 'start'):
            before = settings.get(field, '')
            before = re.sub(r'bash \.agents/cloud-setup\.sh(?: (?:cursor|codex))?(?![\w/-])', command, before)
            if command not in before:
                before = command + (' && (\n' + before + '\n)' if before.strip() else '')
            settings[field] = before
        environment = project / '.cursor/environment.json'
        environment.parent.mkdir(parents=True, exist_ok=True)
        environment.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + '\n')
    print('Project configuration: ' + str(project / '.agents/models.json'))

print(f'Installed MMW v5 Cloud {manifest["version"]} into {user_agents}')
print('Skills: ' + str(skills))
print('Tools and board: ' + str(runtime))
if cloud == '1':
    print('Save one environment install/start entry for the repository group; preserve existing services and publish/build it.')
print('Commit project model and cloud preparation configuration only; the runtime stays outside repositories.')
PY
