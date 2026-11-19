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

            nmem = bin_dir / "nmem"
            nmem.write_text(
                """#!/usr/bin/env python3
import json
import sys

args = [arg for arg in sys.argv[1:] if arg != "--json"]
if args == ["spaces", "show", "mmw-toolbox"]:
    result = {"id": "mmw-toolbox", "name": "MMW Toolbox",
              "defaultRetrievalMode": "strict", "sharedSpaceIds": []}
elif args[:2] == ["agents", "show"] and args[2] in ("mmw-worker", "mmw-reviewer"):
    role = args[2].removeprefix("mmw-")
    result = {"id": args[2], "displayName": "MMW " + role.title(),
              "role": role, "defaultSpaceId": "mmw-toolbox"}
else:
    raise SystemExit(f"unexpected nmem call: {args}")
print(json.dumps(result))
""",
                encoding="utf-8",
            )
            nmem.chmod(0o755)

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
