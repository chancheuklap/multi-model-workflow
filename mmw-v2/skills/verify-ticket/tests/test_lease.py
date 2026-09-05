"""One run's share of the machine: claiming it, giving it back, and refusing to take it.

Nothing here is stubbed. A slot is busy because the test binds a real socket on it, and a
worktree is gone because the test deletes a real directory — the two facts the lease is
built on are the two a fake would get wrong.
"""

import importlib.util
import os
import re
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "lease.py"


def load(home: Path, slots: int = 4, port_base: int = 21400, stride: int = 5):
    """A fresh module bound to a registry of its own.

    `lease.py` reads its limits once, at import, so a test that wants different ones
    imports it again rather than reaching into it afterwards.
    """
    env = {
        "MMW_HOME": str(home),
        "MMW_LEASE_SLOTS": str(slots),
        "MMW_LEASE_PORT_BASE": str(port_base),
        "MMW_LEASE_PORT_STRIDE": str(stride),
    }
    with mock.patch.dict(os.environ, env, clear=False):
        spec = importlib.util.spec_from_file_location("mmw_lease_under_test", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "mmw"
        self.trees = Path(self.tmp.name) / "trees"
        self.trees.mkdir(parents=True)
        self.addCleanup(self.tmp.cleanup)
        self.lease = load(self.home)

    def tree(self, name: str) -> Path:
        path = self.trees / name
        path.mkdir(exist_ok=True)
        return path

    def bind(self, port: int) -> socket.socket:
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", port))
        sock.listen(1)
        self.addCleanup(sock.close)
        return sock


class Claiming(Base):
    def test_a_worktree_keeps_the_slot_it_was_given(self):
        """Re-claiming is a lookup. Every command of a run has to agree on the ports
        without a file they all have to keep in step."""
        first = self.lease.claim(self.tree("issue-640"))
        again = self.lease.claim(self.tree("issue-640"))
        self.assertEqual(first, again)

    def test_two_worktrees_never_share_a_port(self):
        a = self.lease.claim(self.tree("issue-640"))
        b = self.lease.claim(self.tree("issue-641"))
        self.assertNotEqual(a["slot"], b["slot"])
        span_a = range(a["port_base"], a["port_base"] + a["port_count"])
        span_b = range(b["port_base"], b["port_base"] + b["port_count"])
        self.assertFalse(set(span_a) & set(span_b))

    def test_a_relative_path_is_resolved_before_it_is_registered(self):
        """A lease registered under a name like "." matches nothing later and can never
        be reclaimed. The driver runs declared commands with whatever `cwd` it was
        handed, so the normalising has to happen here rather than at every call site."""
        tree = self.tree("issue-642")
        here = Path.cwd()
        os.chdir(tree)
        try:
            env = self.lease.leased_environment(Path("."))
        finally:
            os.chdir(here)
        self.assertTrue(env["MMW_INSTANCE"].startswith("issue-642-"))
        registered = [r["worktree"] for r in self.lease.claimed()]
        self.assertIn(str(tree.resolve()), registered)
        self.assertNotIn(".", registered)

    def test_the_environment_says_this_is_an_automated_run(self):
        """Question 9's signal. Without it every repository invents a name of its own and
        no criterion can rely on one."""
        env = self.lease.leased_environment(self.tree("issue-643"))
        self.assertEqual(env["MMW_AUTOMATION"], "1")
        self.assertTrue(Path(env["MMW_DATA_DIR"]).is_dir())
        self.assertIn("MMW_PORT_BASE", env)
        self.assertIn("MMW_PORT_COUNT", env)

    def test_a_machine_with_no_slot_left_refuses_and_says_what_to_do(self):
        for n in range(4):
            self.lease.claim(self.tree(f"issue-{n}"))
        with self.assertRaises(SystemExit) as caught:
            self.lease.claim(self.tree("issue-one-too-many"))
        reason = str(caught.exception)
        self.assertLessEqual(len(reason), self.lease.refusal.__globals__["REASON_LIMIT"])
        self.assertIn("blocked", reason, "a refusal without a way out is not a refusal")


class Releasing(Base):
    def test_a_slot_comes_back_when_the_ticket_is_done(self):
        tree = self.tree("issue-640")
        self.lease.claim(tree)
        self.lease.release(tree)
        self.assertEqual(self.lease.claimed(), [])

    def test_release_refuses_while_something_still_listens(self):
        """Taking the ports back from a live process is the same act as ending it."""
        tree = self.tree("issue-640")
        record = self.lease.claim(tree)
        self.bind(record["port_base"])
        with self.assertRaises(SystemExit) as caught:
            self.lease.release(tree)
        reason = str(caught.exception)
        self.assertIn(str(record["port_base"]), reason, "the refusal names no fact")
        self.assertIn("Stop that process", reason, "the refusal names no next step")
        self.assertLessEqual(len(reason), self.lease.refusal.__globals__["REASON_LIMIT"])
        self.assertEqual(len(self.lease.claimed()), 1, "the slot was taken anyway")


class Sweeping(Base):
    def test_a_worktree_that_is_gone_gives_its_slot_back(self):
        """`dispatch.sh` prunes worktree registrations but removes no directory, so
        without this a machine fills up once and never empties."""
        tree = self.tree("issue-640")
        self.lease.claim(tree)
        tree.rmdir()
        self.assertEqual(self.lease.sweep(), [0])
        self.assertEqual(self.lease.claimed(), [])

    def test_a_live_process_keeps_its_slot_even_with_no_worktree(self):
        tree = self.tree("issue-640")
        record = self.lease.claim(tree)
        self.bind(record["port_base"])
        tree.rmdir()
        self.assertEqual(self.lease.sweep(), [])
        self.assertEqual(len(self.lease.claimed()), 1)

    def test_claiming_sweeps_before_it_gives_up(self):
        trees = [self.tree(f"issue-{n}") for n in range(4)]
        for tree in trees:
            self.lease.claim(tree)
        for tree in trees[:2]:
            tree.rmdir()
        record = self.lease.claim(self.tree("issue-new"))
        self.assertIn(record["slot"], (0, 1))


class Counting(Base):
    """How many runs of one repository are up. The gate reads this number, so a wrong
    answer here does not fail loudly — it opens the gate and says nothing."""

    def test_only_the_claims_under_that_directory_are_counted(self):
        base = self.trees / "repo"
        (base / "issue-640").mkdir(parents=True)
        (base / "issue-641").mkdir(parents=True)
        (self.trees / "elsewhere").mkdir()
        for path in (base / "issue-640", base / "issue-641", self.trees / "elsewhere"):
            self.lease.claim(path)
        self.assertEqual(self.lease.count_under(base), 2)

    def test_a_symlinked_prefix_counts_the_same(self):
        """A registry stores resolved paths and a caller usually holds the unresolved
        one; on macOS `/var` is a symlink to `/private/var`. Compared as text the answer
        was zero, and a gate reading zero lets everything through (found 2026-09-05 while
        testing this gate, before it ever ran a night)."""
        real = self.trees / "real"
        (real / "issue-640").mkdir(parents=True)
        self.lease.claim(real / "issue-640")
        link = self.trees / "via-link"
        link.symlink_to(real, target_is_directory=True)
        self.assertEqual(self.lease.count_under(link), 1)

    def test_a_directory_with_nothing_under_it_counts_zero(self):
        self.assertEqual(self.lease.count_under(self.trees / "nothing-here"), 0)


class RegistryIsolation(unittest.TestCase):
    """No test of this suite may write to the machine's own lease registry.

    A slot claim is the only thing keeping two runs off one range of ports. A claim made
    by a test overwrites the record of whatever run holds that slot, and the overwritten
    record names the wrong worktree: `release` then refuses, because the ports are still
    listened on, and the slot is lost until someone edits the registry by hand. Two of
    four slots were lost that way on 2026-09-05, to a suite that had no registry of its
    own.

    `lease.py` reads `MMW_HOME` once, at import, so whichever module pulls it in decides
    then and there which registry it writes to. The two checks below are the two ways a
    module can get that wrong: importing it with the ambient environment, and running a
    script that imports it in a subprocess.
    """

    TESTS = Path(__file__).resolve().parent
    SCRIPTS = SCRIPT.parent
    REAL = Path.home() / ".mmw" / "leases"

    def test_no_lease_module_this_suite_loaded_points_at_the_real_registry(self):
        """`unittest discover` imports every module before it runs anything, so under a
        full run this sees every copy of `lease.py` the suite pulled in."""
        for name, module in list(sys.modules.items()):
            if not str(getattr(module, "__file__", "")).endswith("lease.py"):
                continue
            registry = getattr(module, "REGISTRY", None)
            if registry is None:
                continue
            with self.subTest(module=name):
                self.assertNotEqual(
                    Path(registry).expanduser(), self.REAL,
                    f"`{name}` writes leases to the machine's own registry; set "
                    f"MMW_HOME to a directory of the test's own before importing it")

    def lease_bound_scripts(self) -> set[str]:
        """Every script under `scripts/` that reaches `lease.py`, directly or through
        another script."""
        texts = {p.name: p.read_text(encoding="utf-8") for p in self.SCRIPTS.glob("*.py")}
        bound = {"lease.py"}
        while True:
            more = {
                name for name, text in texts.items() if name not in bound
                and any(re.search(rf"(?m)^\s*(?:from|import)\s+{re.escape(m[:-3])}\b", text)
                        for m in bound)
            }
            if not more:
                return bound
            bound |= more

    def test_every_test_that_names_a_lease_bound_script_sets_its_own_home(self):
        """The static half of the same rule. It also covers a claim made in a subprocess,
        which leaves no module in this process for the check above to find."""
        bound = self.lease_bound_scripts()
        named = []
        for path in sorted(self.TESTS.glob("test_*.py")):
            text = path.read_text(encoding="utf-8")
            if not any(script in text for script in bound):
                continue
            named.append(path.name)
            with self.subTest(test_file=path.name):
                self.assertIn(
                    "MMW_HOME", text,
                    f"{path.name} loads a script that claims a lease and never says "
                    f"which registry it writes to")
        self.assertTrue(named, "no test file names a lease-bound script; this check "
                               "found nothing to check")


if __name__ == "__main__":
    unittest.main()
