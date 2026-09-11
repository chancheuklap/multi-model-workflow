"""One run's share of the machine: claiming it, giving it back, and refusing to take it.

Nothing here is stubbed. A slot is busy because the test binds a real socket on it, and a
worktree is gone because the test deletes a real directory — the two facts the lease is
built on are the two a fake would get wrong.
"""

import contextlib
import importlib.util
import io
import json
import os
import re
import shlex
import signal
import socket
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "drive-target" / "scripts" / "lease.py"


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

    def test_a_judge_run_outside_a_ticket_gives_the_slot_back(self):
        tree = self.tree("main-checkout")
        with self.lease.judge_run(tree):
            self.lease.leased_environment(tree)
            self.assertEqual(len(self.lease.claimed()), 1)
        self.assertEqual(self.lease.claimed(), [])

    def test_an_outer_judge_run_owns_the_slot_until_all_nested_judges_finish(self):
        tree = self.tree("main-checkout")
        with self.lease.judge_run(tree):
            with self.lease.judge_run(tree):
                self.lease.leased_environment(tree)
            self.assertEqual(len(self.lease.claimed()), 1)
        self.assertEqual(self.lease.claimed(), [])

    def test_a_run_outside_a_ticket_keeps_the_product(self):
        tree = self.tree("main-checkout")
        pidfile = self.trees / "server.pid"
        command = (
            f"{shlex.quote(sys.executable)} -m http.server \"$MMW_PORT_BASE\" "
            f"--bind 127.0.0.1 --directory {shlex.quote(str(tree))} >/dev/null 2>&1 & "
            f"echo $! > {shlex.quote(str(pidfile))}"
        )
        code = self.lease.main(["run", str(tree), "--", "/bin/sh", "-c", command])
        self.assertEqual(code, 0)
        record = self.lease.claimed()[0]
        pid = int(pidfile.read_text(encoding="utf-8"))
        try:
            for _ in range(50):
                if self.lease.listener(record["port_base"]) is not None:
                    break
                time.sleep(0.05)
            self.assertIsNotNone(self.lease.listener(record["port_base"]))
            self.assertEqual(record["worktree"], str(tree.resolve()))
        finally:
            os.kill(pid, signal.SIGTERM)
            for _ in range(50):
                if self.lease.listener(record["port_base"]) is None:
                    break
                time.sleep(0.05)
            self.lease.release(tree.resolve())

    def test_a_ticket_judge_run_keeps_the_slot_for_its_later_runs(self):
        tree = self.trees / ".worktrees" / "issue-640"
        tree.mkdir(parents=True)
        with self.lease.judge_run(tree):
            self.lease.leased_environment(tree)
        self.assertEqual([r["worktree"] for r in self.lease.claimed()], [str(tree.resolve())])


class StoppingBeforeReleasing(Base):
    """`release --stop` takes the product down with the `stop` its repository declares,
    then gives the slot back: one act, because a slot is free only once nothing listens on
    its ports. The listener check, not the stop, is what keeps a live product's slot."""

    def declare(self, tree: Path, stop: str = "", text: str | None = None) -> None:
        (tree / ".mmw").mkdir(exist_ok=True)
        (tree / ".mmw" / "target.json").write_text(
            text if text is not None else json.dumps({"stop": stop}), encoding="utf-8")

    def run_cli(self, *argv) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.lease.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def claimed_tree(self, name: str = "issue-640") -> Path:
        tree = self.tree(name)
        self.run_cli("claim", str(tree))
        return tree

    def test_the_declared_stop_runs_in_the_worktree_before_the_slot_is_given_back(self):
        tree = self.claimed_tree()
        slot_file = self.lease.slot_file(self.lease.claimed()[0]["slot"])
        seen = self.trees / "seen"
        self.declare(tree, f"pwd -P > '{seen}'; test -f '{slot_file}' && echo held >> '{seen}'; "
                           f"echo \"$MMW_INSTANCE\" >> '{seen}'")
        code, out, err = self.run_cli("release", str(tree), "--stop")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["released"], True)
        where, held, instance = seen.read_text(encoding="utf-8").splitlines()
        self.assertEqual((where, held), (str(tree.resolve()), "held"))
        self.assertTrue(instance.startswith("issue-640-"), "the stop ran outside its claim")
        self.assertEqual(self.lease.claimed(), [])

    def test_a_stop_that_fails_is_said_and_the_slot_is_still_given_back(self):
        tree = self.claimed_tree()
        self.declare(tree, "echo compose down failed >&2; exit 7")
        code, _, err = self.run_cli("release", str(tree), "--stop")
        self.assertEqual(code, 0, err)
        self.assertIn("exited 7: compose down failed", err)
        self.assertEqual(self.lease.claimed(), [])

    def test_a_stop_that_does_not_finish_is_ended_and_the_slot_still_asked_for(self):
        import time
        tree = self.claimed_tree()
        self.declare(tree, "sleep 5")
        self.lease.STOP_TIMEOUT_S = 1
        began = time.monotonic()
        code, _, err = self.run_cli("release", str(tree), "--stop")
        self.assertLess(time.monotonic() - began, 4, "the release waited out the stop")
        self.assertEqual(code, 0, err)
        self.assertIn("did not finish in 1s", err)
        self.assertEqual(self.lease.claimed(), [])

    def test_a_failed_stop_leaves_a_live_product_its_slot(self):
        tree = self.claimed_tree()
        self.bind(self.lease.claimed()[0]["port_base"])
        self.declare(tree, "exit 1")
        with self.assertRaises(SystemExit) as caught:
            self.run_cli("release", str(tree), "--stop")
        self.assertIn("Stop that process", str(caught.exception))
        self.assertEqual(len(self.lease.claimed()), 1)

    def test_no_target_json_is_no_stop_and_a_plain_release(self):
        tree = self.claimed_tree()
        code, out, err = self.run_cli("release", str(tree), "--stop")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["released"], True)
        self.assertEqual(self.lease.claimed(), [])

    def test_a_target_json_nobody_can_read_is_exit_2_and_keeps_the_slot(self):
        """A stop nobody can read is not "no stop declared": the product may still be up,
        so nothing is stopped and nothing is given back."""
        tree = self.claimed_tree()
        self.declare(tree, text="{not json")
        code, out, err = self.run_cli("release", str(tree), "--stop")
        self.assertEqual((code, out), (2, ""))
        self.assertIn(".mmw/target.json cannot be read as JSON", err)
        self.assertEqual(len(self.lease.claimed()), 1)
        with self.assertRaises(self.lease.StopUnreadable):
            self.lease.release(self.lease.worktree_of(tree), stop=True)

    def test_a_worktree_with_no_slot_runs_no_stop(self):
        tree = self.tree("issue-640")
        stopped = self.trees / "stopped"
        self.declare(tree, f"touch '{stopped}'")
        code, _, _ = self.run_cli("release", str(tree), "--stop")
        self.assertEqual(code, 3)
        self.assertFalse(stopped.exists())

    def test_remove_instance_reports_a_failed_deletion(self):
        tree = self.tree("issue-640")
        data = self.lease.instance_data_dir(tree.resolve())
        data.mkdir(parents=True)
        tree.rmdir()
        with mock.patch.object(self.lease.shutil, "rmtree", side_effect=PermissionError("no")):
            result = self.lease.remove_instance(tree)
        self.assertEqual(result["removed"], False)
        self.assertIn("no", result["reason"])


class Sweeping(Base):
    def test_a_worktree_that_is_gone_gives_its_slot_back(self):
        """`dispatch.sh` prunes worktree registrations but removes no directory, so
        without this a machine fills up once and never empties."""
        tree = self.tree("issue-640")
        self.lease.claim(tree)
        tree.rmdir()
        self.assertEqual(self.lease.sweep(), [0])
        self.assertEqual(self.lease.claimed(), [])

    def test_claim_keeps_a_missing_worktree_slot_that_still_listens(self):
        tree = self.tree("issue-640")
        record = self.lease.claim(tree)
        self.bind(record["port_base"])
        tree.rmdir()
        claimed = self.lease.claim(self.tree("issue-new"))
        self.assertNotEqual(claimed["slot"], record["slot"])
        self.assertEqual(len(self.lease.claimed()), 2)

    def test_claim_reclaims_the_slot_of_a_missing_worktree(self):
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


class TheProductsLimit(Base):
    """`instance.max` in `.mmw/target.json` is how many copies of a product that cannot
    move its ports may run at once. The claim itself enforces it, at the first run of a
    worktree's criteria that needs the product, and counts the claims of that
    repository's ticket worktrees — the ones under `<main checkout>/.worktrees`."""

    def setUp(self):
        super().setUp()
        self.repo = self.trees / "repo"
        self.git("init", "-q", "-b", "main", str(self.repo))
        self.git("-C", str(self.repo), "-c", "user.email=t@t", "-c", "user.name=t",
                 "commit", "-q", "--allow-empty", "-m", "base")

    def git(self, *args):
        import subprocess
        subprocess.run(["git", *args], check=True, capture_output=True)

    def ticket_tree(self, n: int, limit: int | str | None = 1, repo: Path | None = None) -> Path:
        repo = repo or self.repo
        tree = repo / ".worktrees" / f"issue-{n}"
        self.git("-C", str(repo), "worktree", "add", "-q", "-b", f"issue-{n}", str(tree))
        if limit is not None:
            (tree / ".mmw").mkdir(exist_ok=True)
            text = (limit if isinstance(limit, str)
                    else json.dumps({"instance": {"max": limit, "why": "fixed ports"}}))
            (tree / ".mmw" / "target.json").write_text(text, encoding="utf-8")
        return self.lease.worktree_of(tree)

    def test_a_second_ticket_worktree_past_the_limit_is_told_the_product_is_full(self):
        first = self.ticket_tree(1)
        self.lease.try_claim(first)
        with self.assertRaises(self.lease.Full) as caught:
            self.lease.try_claim(self.ticket_tree(2))
        self.assertEqual((caught.exception.reason, caught.exception.limit),
                         ("product-full", 1))
        self.assertEqual(caught.exception.holders, [str(first)])
        self.assertEqual(len(self.lease.claimed()), 1, "a slot was taken past the limit")

    def test_a_worktree_that_holds_its_slot_is_never_refused_it(self):
        first = self.ticket_tree(1)
        record = self.lease.try_claim(first)
        self.ticket_tree(2)
        self.assertEqual(self.lease.try_claim(first), record)

    def test_a_slot_given_back_is_the_next_worktrees(self):
        first = self.ticket_tree(1)
        second = self.ticket_tree(2)
        self.lease.try_claim(first)
        self.lease.release(first)
        self.assertEqual(self.lease.try_claim(second)["worktree"], str(second))

    def test_the_main_checkout_counts_toward_the_limit_like_any_other(self):
        """The night's reverify runs the product in the main checkout; a claim there that
        the limit did not count would put a second copy on the ports the limit exists to
        protect."""
        (self.repo / ".mmw").mkdir()
        (self.repo / ".mmw" / "target.json").write_text(
            json.dumps({"instance": {"max": 1}}), encoding="utf-8")
        main = self.lease.worktree_of(self.repo)
        first = self.ticket_tree(1)
        self.lease.try_claim(first)
        with self.assertRaises(self.lease.Full) as caught:
            self.lease.try_claim(main)
        self.assertEqual(caught.exception.holders, [str(first)])
        self.lease.release(first)
        self.lease.try_claim(main)
        with self.assertRaises(self.lease.Full) as caught:
            self.lease.try_claim(self.ticket_tree(2))
        self.assertEqual(caught.exception.holders, [str(main)])

    def test_a_claim_records_its_repository_so_the_count_needs_no_directory(self):
        first = self.ticket_tree(1)
        record = self.lease.try_claim(first)
        self.assertEqual(record["repo"], str((self.repo / ".git").resolve()))

    def test_another_repositorys_worktrees_do_not_count(self):
        other = self.trees / "other"
        self.git("init", "-q", "-b", "main", str(other))
        self.git("-C", str(other), "-c", "user.email=t@t", "-c", "user.name=t",
                 "commit", "-q", "--allow-empty", "-m", "base")
        self.lease.try_claim(self.ticket_tree(1, repo=other))
        self.lease.try_claim(self.ticket_tree(1))

    def test_no_limit_declared_is_the_machines_limit(self):
        for n in range(1, 5):
            self.lease.try_claim(self.ticket_tree(n, limit=None))
        with self.assertRaises(self.lease.Full) as caught:
            self.lease.try_claim(self.ticket_tree(5, limit=None))
        self.assertEqual((caught.exception.reason, caught.exception.limit), ("machine-full", 4))

    def test_a_limit_nobody_can_read_is_not_no_limit(self):
        tree = self.ticket_tree(1, limit="{not json")
        with self.assertRaises(self.lease.CapUnreadable):
            self.lease.try_claim(tree)
        with self.assertRaises(SystemExit):
            self.lease.claim(tree)
        self.assertEqual(self.lease.claimed(), [])

    def test_a_judge_that_reaches_a_full_product_is_refused_with_a_way_out(self):
        self.lease.try_claim(self.ticket_tree(1))
        with self.assertRaises(SystemExit) as caught:
            self.lease.claim(self.ticket_tree(2))
        self.assertIn("instance.max of 1", str(caught.exception))
        self.assertIn("blocked", str(caught.exception))

    def test_the_command_line_answers_4_and_says_who_holds_the_slots(self):
        first = self.ticket_tree(1)
        self.lease.try_claim(first)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.lease.main(["claim", str(self.ticket_tree(2))])
        self.assertEqual(code, 4, "a full product is a wait, told by its own exit code")
        self.assertEqual(json.loads(out.getvalue()),
                         {"claimed": False, "reason": "product-full", "limit": 1,
                          "holders": [str(first)]})

    def test_the_count_and_the_take_are_one_act_under_a_lock(self):
        """Two runs asking for the last slot at once must not both count one free slot.
        With the registry's lock held elsewhere, a claim waits for it rather than
        counting on its own."""
        import fcntl
        import subprocess
        import time
        tree = self.ticket_tree(1)
        self.lease.REGISTRY.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, MMW_HOME=str(self.home), MMW_LEASE_SLOTS="4",
                   MMW_LEASE_PORT_BASE="21400", MMW_LEASE_PORT_STRIDE="5")
        with open(self.lease.REGISTRY / ".lock", "a+") as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            proc = subprocess.Popen([sys.executable, str(SCRIPT), "claim", str(tree)],
                                    env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(1.0)
            waiting = proc.poll() is None
            fcntl.flock(held, fcntl.LOCK_UN)
        out, err = proc.communicate(timeout=30)
        self.assertTrue(waiting, "the claim went ahead while the registry was locked")
        self.assertEqual(proc.returncode, 0, err)
        self.assertEqual(json.loads(out)["worktree"], str(tree))


class WhatTheCommandLineAnswers(Base):
    """Every verb is read by a program or an agent, so none of them answers in prose.

    The decision a caller acts on is the exit code; the facts are JSON. `dispatch.sh`
    once told "no lease" from "released" by matching the front of a sentence, which made
    the wording load-bearing and the caller silently wrong when it changed.
    """

    def run_cli(self, *argv) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.lease.main(list(argv))
        return code, out.getvalue()

    def test_release_says_which_outcome_in_the_exit_code(self):
        # Claimed through the command line too: `main` resolves the path it is given
        # before it looks a lease up, so a test that claims past it would be asking
        # about a worktree under a different name.
        tree = self.tree("issue-640")
        self.run_cli("claim", str(tree))
        code, out = self.run_cli("release", str(tree))
        self.assertEqual(code, 0, "a slot given back is exit 0")
        self.assertEqual(json.loads(out)["released"], True)

        code, out = self.run_cli("release", str(tree))
        self.assertEqual(code, 3, "nothing to give back is exit 3, not a sentence to match")
        row = json.loads(out)
        self.assertEqual(row["released"], False)
        self.assertEqual(row["reason"], "no-lease")

    def test_list_is_json_a_program_can_read_a_field_out_of(self):
        tree = self.tree("issue-640")
        record = self.lease.claim(tree)
        code, out = self.run_cli("list")
        self.assertEqual(code, 0)
        rows = json.loads(out)
        self.assertEqual([r["worktree"] for r in rows], [str(tree)])
        self.assertEqual(rows[0]["port_base"], record["port_base"])
        self.assertIsNone(rows[0]["busy"], "nothing is listening on it")

    def test_list_names_what_holds_a_slot_it_cannot_give_back(self):
        tree = self.tree("issue-640")
        record = self.lease.claim(tree)
        self.bind(record["port_base"])
        rows = json.loads(self.run_cli("list")[1])
        self.assertEqual(rows[0]["busy"]["port"], record["port_base"])
        self.assertIsInstance(rows[0]["busy"]["pid"], int)


if __name__ == "__main__":
    unittest.main()
