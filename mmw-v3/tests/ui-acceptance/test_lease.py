"""One run's share of the machine: acquiring it, giving it back, and refusing to take it.

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
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "ui-acceptance" / "scripts" / "lease.py"


def load(home: Path, slots: int = 4, port_base: int = 21400, stride: int = 5):
    """A fresh module bound to a registry of its own, and the patch that binds it.

    `lease.py` reads its port and slot limits once, at import, so a test that wants
    different ones imports it again rather than reaching into it afterwards. `MMW_HOME`
    it reads at every call, so the environment this test's registry is named in has to
    stay in force while the test runs: the caller stops the patcher it gets back.
    """
    env = {
        "MMW_HOME": str(home),
        "MMW_LEASE_SLOTS": str(slots),
        "MMW_LEASE_PORT_BASE": str(port_base),
        "MMW_LEASE_PORT_STRIDE": str(stride),
    }
    patcher = mock.patch.dict(os.environ, env, clear=False)
    patcher.start()
    try:
        spec = importlib.util.spec_from_file_location("mmw_lease_under_test", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except BaseException:
        patcher.stop()
        raise
    return module, patcher


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "mmw"
        self.trees = Path(self.tmp.name) / "trees"
        self.trees.mkdir(parents=True)
        self.addCleanup(self.tmp.cleanup)
        self.lease, patcher = load(self.home)
        self.addCleanup(patcher.stop)

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

    def bind_at(self, port: int, address: str) -> socket.socket:
        """Listen on `port` at one address, in the family that address belongs to.

        Every listener a test bound used to be `127.0.0.1`, which is the one address the
        old check could see; a product bound to every address, which is where a
        container engine publishes a port, went unseen.
        """
        family = socket.AF_INET6 if ":" in address else socket.AF_INET
        sock = socket.socket(family, socket.SOCK_STREAM)
        if family == socket.AF_INET6:
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        sock.bind((address, port))
        sock.listen(1)
        self.addCleanup(sock.close)
        return sock


class Products(Base):
    def setUp(self):
        super().setUp()
        self.lease, patcher = load(self.home, port_base=22400)
        self.addCleanup(patcher.stop)
        self.root = self.tree("products")
        mmw = self.root / ".mmw"
        mmw.mkdir()
        (mmw / "target.json").write_text(json.dumps({
            "checks": [], "products": ["gateway", "parrot"],
            "needs": {"parrot": ["gateway"]},
        }))
        for name, ports in (("gateway", 2), ("parrot", 3)):
            base = mmw / name
            base.mkdir()
            (base / "target.json").write_text(json.dumps({
                "ports": ports, "start": "true", "stop": "true",
                "discover": "echo '{}'",
            }))

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.root,
                              env=dict(os.environ), capture_output=True, text=True)

    def stack(self):
        fixture = Path(__file__).resolve().parent / "fixtures" / "products" / "repo"
        shutil.copytree(fixture, self.root, dirs_exist_ok=True)
        self.addCleanup(self.cli, "release", "--stop")

    def events(self):
        return [json.loads(line) for line in
                (self.root / ".mmw" / "events.jsonl").read_text().splitlines()]

    def test_lease_run_with_product_starts_its_needs(self):
        self.stack()
        proc = self.cli("run", "--product", "parrot", "--", sys.executable,
                        ".mmw/product.py", "command")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["started"], ["gateway", "parrot"])
        events = self.events()
        self.assertEqual([(e["product"], e["verb"]) for e in events],
                         [("gateway", "start"), ("gateway", "discover"), ("parrot", "command")])
        self.assertEqual(events[-1]["env"]["GATEWAY_ORIGIN"],
                         "http://127.0.0.1:22400/discovered")

    def test_release_stops_products_in_reverse_order(self):
        self.stack()
        proc = self.cli("run", "--product", "parrot", "--", sys.executable,
                        ".mmw/product.py", "start")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        record = json.loads(self.cli("list").stdout)[0]
        self.assertEqual(record["started"], ["gateway", "parrot"])
        proc = self.cli("release", "--stop")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(json.loads(proc.stdout)["released"])
        self.assertEqual([e["product"] for e in self.events() if e["verb"] == "stop"],
                         ["parrot", "gateway"])
        self.assertEqual(json.loads(self.cli("list").stdout), [])
        for port in range(22400, 22405):
            self.assertIsNone(self.lease.listener(port))

    def test_a_product_still_listening_is_named_on_release(self):
        self.stack()
        marker = self.root / ".mmw/leave-gateway"
        marker.touch()
        self.addCleanup(marker.unlink, missing_ok=True)
        proc = self.cli("run", "--product", "parrot", "--", sys.executable,
                        ".mmw/product.py", "start")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        gateway = next(e for e in self.events() if e["product"] == "gateway")
        pid = Path(gateway["env"]["MMW_DATA_DIR"], "pid").read_text()
        proc = self.cli("release", "--stop")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        for fact in ("gateway", "22400", pid):
            self.assertIn(fact, proc.stderr)
        record = json.loads(self.cli("list").stdout)[0]
        self.assertEqual(record["started"], ["gateway"])
        self.assertEqual(record["busy"]["port"], 22400)

    def test_recursive_shared_needs_start_once_and_hyphens_are_prefixed(self):
        self.stack()
        mmw = self.root / ".mmw"
        (mmw / "gateway").rename(mmw / "api-gateway")
        for name in ("cache", "aux"):
            shutil.copytree(mmw / "api-gateway", mmw / name)
        (mmw / "target.json").write_text(json.dumps({
            "checks": [], "products": ["parrot", "api-gateway", "cache", "aux"],
            "needs": {"cache": ["api-gateway"], "aux": ["api-gateway"],
                      "parrot": ["cache", "aux"]},
        }))
        for name in ("parrot", "api-gateway", "cache", "aux"):
            path = mmw / name / "target.json"
            cfg = json.loads(path.read_text())
            cfg["ports"] = 1
            path.write_text(json.dumps(cfg))
        proc = self.cli("run", "--product", "parrot", "--", sys.executable,
                        ".mmw/product.py", "command")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["started"],
                         ["api-gateway", "cache", "aux", "parrot"])
        starts = [e for e in self.events() if e["verb"] == "start"]
        self.assertEqual([e["product"] for e in starts], ["api-gateway", "cache", "aux"])
        command = self.events()[-1]["env"]
        self.assertEqual(command["MMW_PORT_BASE"], "22400")
        self.assertEqual(command["API_GATEWAY_ORIGIN"], "http://127.0.0.1:22401/discovered")
        self.assertEqual(json.loads(command["API_GATEWAY_METADATA"]), {"product": "api-gateway"})
        self.assertEqual(command["CACHE_ORIGIN"], "http://127.0.0.1:22402/discovered")
        self.assertEqual(command["AUX_ORIGIN"], "http://127.0.0.1:22403/discovered")

    def test_ports_that_exceed_the_slot_are_refused_without_a_registration(self):
        path = self.root / ".mmw/parrot/target.json"
        cfg = json.loads(path.read_text())
        cfg["ports"] = 4
        path.write_text(json.dumps(cfg))
        proc = self.cli("run", "--product", "parrot", "--", "true")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("6", proc.stderr)
        self.assertEqual(json.loads(self.cli("list").stdout), [])

    def test_a_failed_product_command_stops_the_dependencies_it_started(self):
        self.stack()
        proc = self.cli("run", "--product", "parrot", "--", sys.executable,
                        "-c", "raise SystemExit(7)")
        self.assertEqual(proc.returncode, 7, proc.stdout + proc.stderr)
        self.assertEqual([e["product"] for e in self.events() if e["verb"] == "stop"],
                         ["parrot", "gateway"])
        record = json.loads(self.cli("list").stdout)[0]
        self.assertEqual(record["started"], [])
        self.assertIsNone(record["busy"])

    def test_a_new_layout_without_ports_is_refused_before_claiming(self):
        path = self.root / ".mmw/parrot/target.json"
        cfg = json.loads(path.read_text())
        del cfg["ports"]
        path.write_text(json.dumps(cfg))
        proc = self.cli("run", "--product", "parrot", "--", "true")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn(".mmw/parrot/target.json", proc.stderr)
        self.assertEqual(json.loads(self.cli("list").stdout), [])

    def test_an_old_layout_run_refuses_before_commands_or_claiming(self):
        (self.root / ".mmw/target.json").write_text(json.dumps({"stop": "true"}))
        marker = self.root / "command-ran"
        proc = self.cli("run", "--", "touch", str(marker))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("migrate_products.py", proc.stderr)
        self.assertFalse(marker.exists())
        self.assertEqual(json.loads(self.cli("list").stdout), [])

    def test_each_product_gets_its_own_segment(self):
        (self.root / ".mmw/target.json").write_text(json.dumps({
            "products": ["parrot", "gateway"], "needs": {"parrot": ["gateway"]},
        }))
        seen = []
        for name in ("gateway", "parrot"):
            proc = self.cli("run", "--product", name, "--", sys.executable, "-c",
                            "import os,json; print(json.dumps(dict(os.environ)))")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            seen.append(json.loads(proc.stdout))
        gateway, parrot = seen
        self.assertEqual((gateway["MMW_PORT_BASE"], gateway["MMW_PORT_COUNT"]),
                         ("22403", "2"))
        self.assertEqual((parrot["MMW_PORT_BASE"], parrot["MMW_PORT_COUNT"]),
                         ("22400", "3"))
        for name, env in zip(("gateway", "parrot"), seen):
            self.assertEqual(Path(env["MMW_DATA_DIR"]).name, name)
            self.assertEqual(env["MMW_PRODUCT"], name)
            self.assertTrue(Path(env["MMW_DATA_DIR"]).is_dir())
            self.assertEqual(env["MMW_AUTOMATION"], "1")
        self.assertEqual(gateway["MMW_SLOT"], parrot["MMW_SLOT"])
        self.assertEqual(gateway["MMW_INSTANCE"], parrot["MMW_INSTANCE"])

    def test_a_single_product_run_keeps_the_callers_working_directory(self):
        (self.root / ".mmw/target.json").write_text('{"products": ["parrot"]}')
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subdir = self.root / "subdir"
        subdir.mkdir()
        self.addCleanup(self.cli, "release", "--stop")
        proc = subprocess.run([sys.executable, str(SCRIPT), "run", "--", sys.executable,
                               "-c", "import os; print(os.getcwd())"], cwd=subdir,
                              env=dict(os.environ), capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(Path(proc.stdout.strip()).resolve(), subdir.resolve())


class SeeingWhatListens(Base):
    """Whether a port is held is asked of the port, not of one address on it.

    A product publishes its ports where it likes: a container engine on macOS publishes
    on every address, and a server told to listen on `localhost` under Node listens on
    `::1` alone. A slot read as quiet under a live stack is given to the next run, which
    then starts onto occupied ports and can report only blocked.
    """

    def free_port(self) -> int:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            return int(probe.getsockname()[1])

    def test_a_listener_on_every_address_is_seen(self):
        port = self.free_port()
        self.bind_at(port, "0.0.0.0")
        self.assertIsNotNone(self.lease.listener(port))

    def test_a_listener_on_the_ipv6_loopback_alone_is_seen(self):
        port = self.free_port()
        self.bind_at(port, "::1")
        self.assertIsNotNone(self.lease.listener(port))

    def test_a_port_nothing_listens_on_is_free(self):
        self.assertIsNone(self.lease.listener(self.free_port()))

    def test_a_slot_held_by_a_listener_on_every_address_is_not_given_back(self):
        tree = self.tree("issue-640")
        record = self.lease.claim(tree)
        self.bind_at(record["port_base"] + 1, "0.0.0.0")
        with self.assertRaises(SystemExit) as caught:
            self.lease.release(tree)
        self.assertIn(str(record["port_base"] + 1), str(caught.exception))
        self.assertEqual(len(self.lease.claimed()), 1, "a live stack lost its slot")

    def test_a_gone_worktree_with_a_listener_on_every_address_is_not_swept(self):
        tree = self.tree("issue-640")
        record = self.lease.claim(tree)
        self.bind_at(record["port_base"], "0.0.0.0")
        tree.rmdir()
        self.assertEqual(self.lease.sweep(), [])
        self.assertEqual(len(self.lease.claimed()), 1)


class Claiming(Base):
    def test_a_slot_with_a_foreign_listener_is_skipped(self):
        """One port of the first slot is listened on by this process, which the
        registry does not name. The port is not the first of the block. The lease
        issues the next slot."""
        occupied = self.lease.PORT_BASE + 2
        self.bind(occupied)
        record = self.lease.claim(self.tree("issue-640"))
        issued = range(record["port_base"], record["port_base"] + record["port_count"])
        self.assertEqual(record["slot"], 1)
        self.assertNotIn(occupied, issued)
        self.assertFalse(self.lease.slot_file(0).exists())

    def test_a_worktree_keeps_the_slot_it_was_given(self):
        """Re-acquiring is a lookup. Every command of a run has to agree on the ports
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
        be re-acquired. The driver runs declared commands with whatever `cwd` it was
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

    def test_a_judge_leaves_a_slot_it_found_already_held(self):
        """The slot was somebody's before this oracle started — a product left running
        under `lease.py run`, a journey going in the same checkout. Ending it is ending a
        process this run never started."""
        tree = self.tree("main-checkout")
        (tree / ".mmw").mkdir(exist_ok=True)
        stopped = self.trees / "stopped"
        (tree / ".mmw" / "target.json").write_text(
            json.dumps({"products": ["notes"]}), encoding="utf-8")
        (tree / ".mmw/notes").mkdir()
        (tree / ".mmw/notes/target.json").write_text(
            json.dumps({"ports": 1, "stop": f"touch '{stopped}'"}))
        self.lease.claim(self.lease.worktree_of(tree))
        with self.lease.judge_run(tree, stop=True):
            self.lease.leased_environment(tree)
        self.assertEqual([r["worktree"] for r in self.lease.claimed()],
                         [str(tree.resolve())], "a slot this run never acquired was taken")
        self.assertFalse(stopped.exists(), "a product this run never started was stopped")

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
        if text is not None:
            (tree / ".mmw/target.json").write_text(text)
            return
        (tree / ".mmw/target.json").write_text('{"products": ["notes"]}')
        (tree / ".mmw/notes").mkdir(exist_ok=True)
        (tree / ".mmw/notes/target.json").write_text(json.dumps({"ports": 5, "stop": stop}))
        if self.lease.registered(tree.resolve()) is not None:
            code, _, err = self.run_cli("run", str(tree), "--product", "notes", "--", "true")
            self.assertEqual(code, 0, err)

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
        self.assertTrue(instance.startswith("issue-640-"), "the stop ran outside its lease")
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


class WhichRootThePathsAreUnder(unittest.TestCase):
    """`MMW_HOME` names the root, and it is read at the moment a path is needed.

    Bound once at import instead, two things go wrong and neither says so: an empty
    value becomes `Path("")`, the process's working directory, so a lease is written
    into whatever repository the run happens to be in; and a caller that sets the
    variable after this module is in memory is ignored. The reading is `home()` in the
    `dispatch` skill's `statedir.py`, the canonical reader: empty is no value.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.lease, patcher = load(Path(self.tmp.name) / "at-import")
        self.addCleanup(patcher.stop)

    def test_an_empty_value_is_no_value(self):
        default = Path.home() / ".mmw"
        with mock.patch.dict(os.environ, {"MMW_HOME": ""}, clear=False):
            self.assertEqual(self.lease.home(), default)
            self.assertEqual(self.lease.registry(), default / "leases")
            self.assertNotEqual(self.lease.registry(), Path("") / "leases")

    def test_a_changed_value_is_seen_without_importing_again(self):
        moved = Path(self.tmp.name) / "moved"
        with mock.patch.dict(os.environ, {"MMW_HOME": str(moved)}, clear=False):
            self.assertEqual(self.lease.home(), moved)
            # The paths every verb is built out of, not just the reader beside them.
            self.assertEqual(self.lease.slot_file(1), moved / "leases" / "slot-1.json")
            self.assertEqual(
                self.lease.instance_data_dir(Path(self.tmp.name) / "issue-640").parent,
                moved / "instances")


class RegistryIsolation(unittest.TestCase):
    """No test of this suite may write to the machine's own lease registry.

    A slot lease is the only thing keeping two runs off one range of ports. A lease acquired
    by a test overwrites the record of whatever run holds that slot, and the overwritten
    record names the wrong worktree: `release` then refuses, because the ports are still
    listened on, and the slot is lost until someone edits the registry by hand. Two of
    four slots were lost that way on 2026-09-05, to a suite that had no registry of its
    own.

    `lease.py` reads `MMW_HOME` at the moment it needs a path, so the environment a
    module runs under decides which registry it writes to. The two checks below are the
    two ways a module can get that wrong: running it with the ambient environment, and
    running a script that acquires a lease in a subprocess.
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
            registry = getattr(module, "registry", None)
            if not callable(registry):
                continue
            with self.subTest(module=name):
                self.assertNotEqual(
                    Path(registry()).expanduser(), self.REAL,
                    f"`{name}` writes leases to the machine's own registry; set "
                    f"MMW_HOME to a directory of the test's own while it runs")

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
        """The static half of the same rule. It also covers a lease acquired in a subprocess,
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
                    f"{path.name} loads a script that acquires a lease and never says "
                    f"which registry it writes to")
        self.assertTrue(named, "no test file names a lease-bound script; this check "
                               "found nothing to check")


class AFullMachine(Base):
    """With every slot of the machine taken, no lease is made, and whoever asked is told
    who holds the slots."""

    def full(self) -> list[str]:
        trees = [self.lease.worktree_of(self.tree(f"issue-{n}")) for n in range(1, 5)]
        for tree in trees:
            self.lease.try_claim(tree)
        return [str(tree) for tree in trees]

    def test_a_full_machine_names_every_holder(self):
        """Every slot's first port is listened on by this process, which the registry
        does not name. Nothing is issued, and the refusal names each listener."""
        pid = os.getpid()
        for slot in range(self.lease.SLOTS):
            self.bind(self.lease.ports_of(slot).start)
        with self.assertRaises(SystemExit) as caught:
            self.lease.claim(self.tree("issue-one-too-many"))
        reason = str(caught.exception)
        for slot in range(self.lease.SLOTS):
            self.assertIn(f"slot {slot} pid {pid}", reason)
        self.assertIn(self.lease.REPORT_BLOCKED, reason)
        self.assertNotIn("…", reason)
        self.assertEqual(self.lease.claimed(), [])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.lease.main(["claim", str(self.tree("issue-cli"))])
        self.assertEqual(code, 4)
        holders = json.loads(out.getvalue())["holders"]
        for slot in range(self.lease.SLOTS):
            self.assertIn(f"slot {slot} pid {pid}", holders)

    def test_eight_listeners_are_all_named(self):
        """The default machine has eight slots. Short `slot N pid P` lines still
        overflow the refusal once the blocked-ticket sentence is kept, and a cut
        list drops the last slots."""
        self.lease, extra = load(self.home, slots=8, port_base=22100)
        self.addCleanup(extra.stop)
        pid = os.getpid()
        for slot in range(self.lease.SLOTS):
            self.bind(self.lease.ports_of(slot).start)
        with self.assertRaises(SystemExit) as caught:
            self.lease.claim(self.tree("issue-one-too-many"))
        reason = str(caught.exception)
        self.assertIn(self.lease.REPORT_BLOCKED, reason)
        self.assertNotIn("…", reason)
        for slot in range(self.lease.SLOTS):
            self.assertIn(f"{slot}:p{pid}", reason)

    def test_a_full_registry_names_every_worktree(self):
        """Registered holders are worktree paths. Four of them do not fit in the
        refusal whole, and the last paths are the ones a cut list drops."""
        holders = self.full()
        with self.assertRaises(SystemExit) as caught:
            self.lease.claim(self.tree("issue-5"))
        reason = str(caught.exception)
        self.assertIn(self.lease.REPORT_BLOCKED, reason)
        self.assertNotIn("…", reason)
        for path in holders:
            self.assertIn(Path(path).name, reason)

    def test_an_unreadable_slot_record_names_the_slot(self):
        """A slot file left empty between create and write has no worktree to name.
        The holder is still a fact a reader can check."""
        self.lease.registry().mkdir(parents=True, exist_ok=True)
        for slot in range(self.lease.SLOTS):
            self.lease.slot_file(slot).write_text("", encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.lease.main(["claim", str(self.tree("issue-cli"))])
        self.assertEqual(code, 4)
        holders = json.loads(out.getvalue())["holders"]
        for slot in range(self.lease.SLOTS):
            self.assertEqual(holders[slot], f"slot {slot} record unreadable")

    def test_a_fifth_worktree_is_told_the_machine_is_full(self):
        holders = self.full()
        with self.assertRaises(self.lease.Full) as caught:
            self.lease.try_claim(self.lease.worktree_of(self.tree("issue-5")))
        self.assertEqual(sorted(caught.exception.holders), sorted(holders))
        self.assertEqual(len(self.lease.claimed()), 4, "a slot was taken past the limit")

    def test_a_worktree_that_holds_its_slot_is_never_refused_it(self):
        self.full()
        first = self.lease.worktree_of(self.tree("issue-1"))
        self.assertEqual(self.lease.try_claim(first)["worktree"], str(first))

    def test_a_judge_that_reaches_a_full_machine_is_refused_with_a_way_out(self):
        self.full()
        with self.assertRaises(SystemExit) as caught:
            self.lease.claim(self.tree("issue-5"))
        self.assertIn("blocked", str(caught.exception))

    def test_the_command_line_answers_4_and_says_who_holds_the_slots(self):
        holders = self.full()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.lease.main(["claim", str(self.tree("issue-5"))])
        self.assertEqual(code, 4, "a full machine is told by its own exit code")
        answer = json.loads(out.getvalue())
        self.assertEqual((answer["claimed"], answer["limit"]), (False, 4))
        self.assertEqual(sorted(answer["holders"]), sorted(holders))

    def test_the_count_and_the_take_are_one_act_under_a_lock(self):
        """Two runs asking for the last slot at once must not both count one free slot.
        With the registry's lock held elsewhere, acquiring waits for it rather than
        counting on its own."""
        import fcntl
        import subprocess
        import time
        tree = self.lease.worktree_of(self.tree("issue-1"))
        self.lease.registry().mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, MMW_HOME=str(self.home), MMW_LEASE_SLOTS="4",
                   MMW_LEASE_PORT_BASE="21400", MMW_LEASE_PORT_STRIDE="5")
        with open(self.lease.registry() / ".lock", "a+") as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            proc = subprocess.Popen([sys.executable, str(SCRIPT), "claim", str(tree)],
                                    env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(1.0)
            waiting = proc.poll() is None
            fcntl.flock(held, fcntl.LOCK_UN)
        out, err = proc.communicate(timeout=30)
        self.assertTrue(waiting, "the acquire went ahead while the registry was locked")
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
        # Acquired through the command line too: `main` resolves the path it is given
        # before it looks a lease up, so a test that acquires past it would be asking
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
