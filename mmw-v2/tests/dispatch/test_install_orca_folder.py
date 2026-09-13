import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
INSTALLER = HERE.parents[1] / "install.sh"


class InstallOrcaFolderTests(unittest.TestCase):
    def run_installer(self, kind):
        with tempfile.TemporaryDirectory() as scratch:
            home = Path(scratch) / "home"
            bin_dir = Path(scratch) / "bin"
            bin_dir.mkdir()
            orca = bin_dir / "orca"
            orca.write_text(
                """#!/usr/bin/env python3
import json
import sys

args = sys.argv[1:]
if args[:2] == ["project", "setups"]:
    result = {"setups": []}
elif args[:2] == ["repo", "list"]:
    result = {"repos": [{
        "id": "folder_1",
        "path": "/Users/example",
        "displayName": "example",
        "kind": %r,
        "externalWorktreeVisibility": None,
    }]}
else:
    raise SystemExit(f"unexpected orca call: {args}")
print(json.dumps({"ok": True, "result": result}))
""" % kind,
                encoding="utf-8",
            )
            orca.chmod(0o755)

            env = dict(os.environ)
            env["MMW_V2_HOME"] = str(home)
            env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
            proc = subprocess.run(
                ["bash", str(INSTALLER)],
                cwd=HERE,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            return proc

    def test_folder_workspace_needs_no_git_worktree_visibility(self):
        proc = self.run_installer("folder")
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertNotIn("externalWorktreeVisibility", proc.stderr)

    def test_git_repository_still_needs_worktree_visibility(self):
        proc = self.run_installer("git")
        self.assertEqual(1, proc.returncode)
        self.assertIn("externalWorktreeVisibility", proc.stderr)


if __name__ == "__main__":
    unittest.main()
