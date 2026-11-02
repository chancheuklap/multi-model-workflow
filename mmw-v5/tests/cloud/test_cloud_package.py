from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[3]

class InstalledCloudPackage(unittest.TestCase):
    def test_both_editions_contain_identical_non_dispatch_skills(self):
        def inventory(edition):
            folder = ROOT / edition / "skills"
            return {p.relative_to(folder): p.read_bytes() for p in folder.rglob("*")
                    if p.is_file() and p.relative_to(folder).parts[0] != "dispatch"
                    and "__pycache__" not in p.parts}
        local = inventory("mmw-v5")
        cloud = inventory("mmw-v5-cloud")
        self.assertEqual(local.keys(), cloud.keys())
        for path, content in local.items():
            self.assertEqual(content, cloud[path], str(path))
            self.assertFalse((ROOT / "mmw-v5-cloud/skills" / path).is_symlink())

    def test_complete_project_runtime_works_without_development_checkout(self):
        with tempfile.TemporaryDirectory(prefix='mmw-cloud-package-') as tmp:
            base=Path(tmp); source=base/'source'; source.mkdir()
            def git(folder,*args):
                return subprocess.run(['git',*args],cwd=folder,env=env,capture_output=True,text=True,check=True).stdout.strip()
            env=dict(os.environ,GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_NOSYSTEM='1')
            for name in ['mmw-v5-cloud']:
                shutil.copytree(ROOT/name,source/name,ignore=shutil.ignore_patterns('__pycache__'))
            for name in ['scripts/release-mmw-v5.py']:
                dest=source/name; dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
            git(source,'init','-q','-b','dev');git(source,'config','user.name','Package test');git(source,'config','user.email','test@example.invalid')
            git(source,'add','.');git(source,'commit','-q','-m','candidate')
            archive=base/'cloud.zip'
            run=subprocess.run([sys.executable,str(source/'scripts/release-mmw-v5.py'),'package','--edition','cloud','--output',str(archive)],env=env,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            project=base/'consumer';project.mkdir()
            with zipfile.ZipFile(archive) as z:
                z.extractall(project)
                names=z.namelist()
                self.assertFalse(any(x in name for name in names for x in ['/runners/','/relay.py','/events.py','/children.md']))
                for relative in ['skills/code-review/SKILL.md','skills/code-review/references/main-reviewer.md','skills/write-tests/SKILL.md','board/page/app.mjs','board/page/board-layout.mjs','board/page/detail-layout.mjs','board/page/topbar-layout.mjs','board/page/styles/settings-layout.css','board/gates.py']:
                    self.assertTrue((project/'.agents'/relative).is_file(),relative)
            shutil.rmtree(source)  # Installed runtime cannot reach development sources.
            git(project,'init','-q','-b','night/test');git(project,'config','user.name','Consumer test');git(project,'config','user.email','test@example.invalid')
            git(project,'add','.agents');git(project,'commit','-q','-m','runtime')
            fixed=git(project,'rev-parse','HEAD')
            tool=project/'.agents/tools/dispatch/scripts/models.py'
            run=subprocess.run([sys.executable,str(tool),'row','review-axis','codex','--at',fixed],cwd=project,env=env,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(json.loads(run.stdout),{})
            server=project/'.agents/board/server.py'
            run=subprocess.run([sys.executable,str(server),'--help'],cwd=project,env=env,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            label=project/'.agents/tools/setup-mmw/scripts/labels.py'
            self.assertNotIn('events',label.read_text())
            # Resolve every relative Markdown link in installed dispatch/code-review.
            import re
            for skill in ['dispatch','code-review']:
                for path in (project/'.agents/skills'/skill).rglob('*.md'):
                    for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
                        if '://' not in target and not target.startswith('#'):
                            self.assertTrue((path.parent/target.split('#')[0]).is_file(),f'{path}: {target}')
            # Edition adapters must retain all shared module/style dependencies.
            for path in (project/'.agents/board/page').rglob('*'):
                if path.suffix not in ('.mjs', '.css'): continue
                imports = re.findall(r'(?:from\s*|@import\s*)["\'](\.[^"\']+)["\']', path.read_text())
                for target in imports:
                    self.assertTrue((path.parent/target).is_file(), f'{path}: {target}')

if __name__ == '__main__':unittest.main()
