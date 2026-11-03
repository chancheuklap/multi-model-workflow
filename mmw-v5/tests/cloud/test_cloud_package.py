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
    def test_both_editions_expose_the_complete_skill_set(self):
        def inventory(edition):
            folder = ROOT / edition / "skills"
            return {p.parent.name for p in folder.glob("*/SKILL.md") if p.is_file()}
        local = inventory("mmw-v5")
        cloud = inventory("mmw-v5-cloud")
        self.assertTrue(local)
        self.assertEqual(local, cloud)

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
            git(project,'init','-q','-b','night/test');git(project,'config','user.name','Consumer test');git(project,'config','user.email','test@example.invalid')
            binary=base/'bin'; binary.mkdir()
            curl=binary/'curl'
            curl.write_text('#!' + sys.executable + '\n' + '''import os,pathlib,shutil,sys,zipfile
output=pathlib.Path(sys.argv[sys.argv.index('-o')+1])
if any(arg.endswith('/plugin.json') for arg in sys.argv):
 with zipfile.ZipFile(os.environ['CLOUD_TEST_ARCHIVE']) as archive:
  output.write_bytes(archive.read('.cursor/plugin.json'))
else:
 shutil.copyfile(os.environ['CLOUD_TEST_ARCHIVE'],output)
''')
            curl.chmod(0o755)
            install_env={**env,'PATH':str(binary)+os.pathsep+env['PATH'],'CLOUD_TEST_ARCHIVE':str(archive)}
            def install(cwd):
                result=subprocess.run(['bash',str(ROOT/'scripts/install-mmw-v5-cloud.sh')],cwd=cwd,env=install_env,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
            install(project)
            with zipfile.ZipFile(archive) as z:
                names=z.namelist()
                self.assertFalse(any(x in name for name in names for x in ['/runners/','/relay.py','/events.py','/children.md']))
                for relative in ['skills/code-review/SKILL.md','skills/code-review/references/main-reviewer.md','skills/write-tests/SKILL.md','board/page/app.mjs','board/page/board-layout.mjs','board/page/detail-layout.mjs','board/page/topbar-layout.mjs','board/page/styles/settings-layout.css','board/gates.py']:
                    self.assertTrue((project/'.cursor'/relative).is_file(),relative)
            shutil.rmtree(source)  # Installed runtime cannot reach development sources.
            git(project,'add','.cursor');git(project,'commit','-q','-m','runtime')
            fixed=git(project,'rev-parse','HEAD')
            tool=project/'.cursor/tools/dispatch/scripts/models.py'
            run=subprocess.run([sys.executable,str(tool),'row','review-axis','codex','--at',fixed],cwd=project,env=env,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(json.loads(run.stdout),{'model':'gpt-6.1-sol','effort':'high'})
            server=project/'.cursor/board/server.py'
            run=subprocess.run([sys.executable,str(server),'--help'],cwd=project,env=env,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            label=project/'.cursor/tools/setup-mmw/scripts/labels.py'
            self.assertNotIn('events',label.read_text())
            config=project/'.cursor/models.json'
            edited=json.loads(config.read_text());edited['max_workers']=5
            config.write_text(json.dumps(edited))
            rules=project/'.cursor/rules/owner.mdc';rules.parent.mkdir();rules.write_text('Keep project rules\n')
            nested=project/'src';nested.mkdir()
            install(nested)
            self.assertEqual(json.loads(config.read_text()),edited)
            self.assertEqual(rules.read_text(),'Keep project rules\n')
            self.assertFalse((project/'.agents').exists())
            # Resolve every relative Markdown link in installed dispatch/code-review.
            import re
            for skill in ['dispatch','code-review']:
                for path in (project/'.cursor/skills'/skill).rglob('*.md'):
                    for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
                        if '://' not in target and not target.startswith('#'):
                            self.assertTrue((path.parent/target.split('#')[0]).is_file(),f'{path}: {target}')
            # Edition adapters must retain all shared module/style dependencies.
            for path in (project/'.cursor/board/page').rglob('*'):
                if path.suffix not in ('.mjs', '.css'): continue
                imports = re.findall(r'(?:from\s*|@import\s*)["\'](\.[^"\']+)["\']', path.read_text())
                for target in imports:
                    self.assertTrue((path.parent/target).is_file(), f'{path}: {target}')

if __name__ == '__main__':unittest.main()
