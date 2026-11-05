#!/usr/bin/env bash
# Install the latest published cloud edition. --cloud also prepares repository cloud setup.
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
repository="chancheuklap/multi-model-workflow"

curl -fsSL "https://github.com/$repository/releases/latest/download/mmw-v5-cloud.zip" -o "$temporary/cloud.zip"

python3 - "$temporary/cloud.zip" "$project" "$host" "$cloud" <<'PY'
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import zipfile

archive, project, host, cloud = sys.argv[1:]
project = Path(project)
folder = '.agents' if host == 'codex' else '.cursor'
destination = project / folder


def git(*args):
    return subprocess.run(['git', *args], cwd=project, capture_output=True, text=True, check=True).stdout


def replace_block(text, begin, end, body):
    block = begin + '\n' + body.rstrip() + '\n' + end + '\n'
    if begin in text:
        start = text.index(begin)
        stop = text.index(end, start) + len(end)
        return text[:start] + block.rstrip('\n') + text[stop:]
    return text.rstrip() + ('\n\n' if text.strip() else '') + block


def ignore_path(path):
    return '/' + re.sub(r'([\\*?\[\]#! ])', r'\\\1', path)


# Keep ownership in the Git exclude block itself, so removed package files can be
# cleaned on an update without deleting project-owned files in the same folders.
exclude = Path(git('rev-parse', '--path-format=absolute', '--git-path', 'info/exclude').strip())
excluded = exclude.read_text() if exclude.exists() else ''
begin, end = f'# MMW cloud {host} BEGIN', f'# MMW cloud {host} END'
previous = set()
if begin in excluded:
    block = excluded.split(begin, 1)[1].split(end, 1)[0]
    for line in block.splitlines():
        path = re.sub(r'\\(.)', r'\1', line).removeprefix('/')
        relative = PurePosixPath(path)
        if path.startswith(folder + '/') and '..' not in relative.parts and '*' not in path and path != folder + '/models.json':
            previous.add(path)

# Validate existing cloud configuration before changing the installation.
environment = destination / 'environment.json'
settings = None
if cloud == '1' and host == 'cursor':
    settings = json.loads(environment.read_text()) if environment.exists() else {}
    for field in ('install', 'start'):
        if field in settings and not isinstance(settings[field], str):
            raise SystemExit(f'{environment}: {field} must be a shell command string')

with zipfile.ZipFile(archive) as package:
    prefix = 'mmw-v5-cloud/'
    manifest = json.loads(package.read(prefix + 'plugin.json'))
    if manifest['name'] != 'mmw-v5-cloud':
        raise SystemExit('The download is not the MMW v5 cloud edition')
    members = {}
    for member in package.infolist():
        if member.is_dir() or not member.filename.startswith(prefix):
            continue
        relative = PurePosixPath(member.filename[len(prefix):])
        if relative.is_absolute() or '..' in relative.parts:
            raise SystemExit('Invalid archive path: ' + str(relative))
        if relative.parts[0] not in ('skills', 'tools', 'board', 'models.json', 'plugin.json'):
            continue
        members[str(relative)] = member

    managed = {folder + '/' + path for path in members if path != 'models.json'}
    owned = sorted(previous | managed)
    tracked = git('ls-files', '-z', '--', *owned).split('\0')
    tracked = [path for path in tracked if path]
    if tracked:
        git('rm', '--cached', '--', *tracked)
        print(f'Retired tracked MMW runtime files: {len(tracked)} (kept on disk)')
    exclude.parent.mkdir(parents=True, exist_ok=True)
    patterns = [ignore_path(path) for path in sorted(managed)] + [f'/{folder}/**/__pycache__/']
    exclude.write_text(replace_block(excluded, begin, end, '\n'.join(patterns)))
    for path in previous - managed:
        target = project / path
        if target.is_file() or target.is_symlink():
            target.unlink()

    installed = 0
    for path, member in members.items():
        relative = PurePosixPath(path)
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

configuration = [folder + '/models.json']
if cloud == '1':
    setup = destination / 'cloud-setup.sh'
    setup.write_text('''#!/usr/bin/env bash
# Prepare MMW in this checkout. Use in environment installation and new-task startup.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host ''' + host + '\n')
    setup.chmod(0o755)
    configuration.append(folder + '/cloud-setup.sh')
    command = f'bash {folder}/cloud-setup.sh'
    if host == 'cursor':
        for field in ('install', 'start'):
            before = settings.get(field, '')
            if command not in before:
                settings[field] = command + (' && (\n' + before + '\n)' if before.strip() else '')
        environment.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + '\n')
        configuration.append(folder + '/environment.json')
        print('Cloud configuration: .cursor/environment.json (install and start)')
        print('Select this repository as the saved Cursor environment.json location, then build it.')
    else:
        instructions = project / 'AGENTS.md'
        before = instructions.read_text() if instructions.exists() else ''
        body = '''## MMW in Codex Cloud

During cloud environment setup, run `bash .agents/cloud-setup.sh` in this repository.
Save that command in the environment's Install script. Add it to the Start skill
to run once before work in each new cloud task, so cached environments get the
latest published MMW. Preserve existing installation and startup work. Publish
the prepared environment. Continuing an existing task keeps its installed runtime.
'''
        instructions.write_text(replace_block(before, '<!-- MMW Codex Cloud BEGIN -->', '<!-- MMW Codex Cloud END -->', body))
        configuration.append('AGENTS.md')
        print('Cloud configuration: .agents/cloud-setup.sh and AGENTS.md')
        print('Codex setup agent: save `bash .agents/cloud-setup.sh` in Install script and in the new-task Start skill, then publish.')

print(f'Installed MMW v5 Cloud {manifest["version"]} into {destination} ({installed} files)')
print('Commit and push configuration only: ' + ', '.join(configuration))
print('MMW runtime files are excluded from Git. Every install downloads the latest published cloud edition.')
PY
