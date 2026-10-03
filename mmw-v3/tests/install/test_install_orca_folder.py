"""Orca's external-worktree visibility applies to Git repositories, not folder workspaces."""

import tempfile
import unittest
from pathlib import Path

from install_home import INSTALLER, run_install, write_fakes


class InstallOrcaFolderTests(unittest.TestCase):
    def run_installer(self, kind):
        with tempfile.TemporaryDirectory() as scratch:
            home = Path(scratch) / "home"
            bin_dir = Path(scratch) / "bin"
            write_fakes(bin_dir, repo_kind=kind)
            return run_install(INSTALLER, home, bin_dir)

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
