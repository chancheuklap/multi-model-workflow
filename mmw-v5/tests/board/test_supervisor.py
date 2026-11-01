from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SUPERVISOR = ROOT / "mmw-v5" / "board" / "supervisor.py"
FIXTURE_GH = ROOT / "mmw-v5" / "tests" / "board" / "github" / "gh"


def free_port(excluding: set[int] | None = None) -> int:
    import socket
    excluding = excluding or set()
    while True:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        if port not in excluding:
            return port


class SupervisorFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.home = self.base / "mmw"
        self.home.mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.processes = []
        wrapper = self.bin / "gh"
        wrapper.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os\n"
            "from pathlib import Path\n"
            "mapping=json.loads(os.environ['MMW_TEST_REPO_FIXTURES'])\n"
            "os.environ['MMW_BOARD_FAKE_DIR']=mapping[str(Path.cwd())]\n"
            f"os.execv({str(FIXTURE_GH)!r}, [{str(FIXTURE_GH)!r}, *os.sys.argv[1:]])\n",
            encoding="utf-8",
        )
        wrapper.chmod(0o755)

    def tearDown(self):
        for process, log in reversed(self.processes):
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
            log.close()
        self.temp.cleanup()

    def repository(self, name: str, slug: str) -> tuple[Path, Path]:
        repository = self.base / name
        repository.mkdir()
        subprocess.run(["git", "init", "-q", str(repository)], check=True)
        subprocess.run(["git", "-C", str(repository), "remote", "add", "origin", "https://github.test/fixture/board.git"], check=True)
        fixture = self.base / f"fixture-{name}"
        fixture.mkdir()
        (fixture / "scenario.json").write_text(json.dumps({
            "repo": slug,
            "maps": [],
            "trees": [],
            "comments": {},
        }), encoding="utf-8")
        return repository, fixture

    def copied_supervisor(self) -> Path:
        """A copy of the board and the tools it loads, so a test can change the code."""
        ignore = shutil.ignore_patterns("__pycache__", "node_modules")
        copy = self.base / "checkout" / "mmw-v5"
        shutil.copytree(ROOT / "mmw-v5" / "board", copy / "board", ignore=ignore)
        for skill in ("dispatch", "verify-ticket"):
            shutil.copytree(ROOT / "mmw-v5" / "tools" / skill,
                            copy / "tools" / skill, ignore=ignore)
        return copy / "board" / "supervisor.py"

    def start(self, registry: dict[Path, int], fixtures: dict[Path, Path],
              supervisor: Path = SUPERVISOR):
        (self.home / "boards.json").write_text(json.dumps({
            str(path): port for path, port in registry.items()
        }), encoding="utf-8")
        log_path = self.base / f"supervisor-{len(self.processes)}.log"
        log = log_path.open("w+", encoding="utf-8")
        env = os.environ.copy()
        env.update({
            "MMW_HOME": str(self.home),
            "HOME": str(self.base / "user"),
            "PATH": str(self.bin) + os.pathsep + env["PATH"],
            "MMW_TEST_REPO_FIXTURES": json.dumps({
                str(path.resolve()): str(fixture) for path, fixture in fixtures.items()
            }),
        })
        process = subprocess.Popen(
            [sys.executable, "-u", str(supervisor), "--interval", "0.05"],
            cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
        )
        self.processes.append((process, log))
        return process, log

    def board(self, port: int) -> dict:
        deadline = time.monotonic() + 10
        last = None
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/board",
                                            timeout=0.5) as response:
                    return json.load(response)
            except Exception as exc:
                last = exc
                time.sleep(0.05)
        self.fail(f"board on {port} did not answer: {last}")

    @staticmethod
    def child_pid(parent: int, port: int) -> int | None:
        output = subprocess.check_output(["ps", "-axo", "pid=,ppid=,command="], text=True)
        suffix = f"server.py --port {port}"
        for line in output.splitlines():
            fields = line.strip().split(None, 2)
            if len(fields) == 3 and int(fields[1]) == parent and suffix in fields[2]:
                return int(fields[0])
        return None

    def wait_for_new_child(self, supervisor: int, port: int, old_pid: int) -> int:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            candidate = self.child_pid(supervisor, port)
            if candidate is not None and candidate != old_pid:
                return candidate
            time.sleep(0.05)
        self.fail(f"no new board replaced pid {old_pid} on port {port}")


class SupervisorTests(SupervisorFixture, unittest.TestCase):
    def test_starts_a_board_per_registered_repo(self):
        first, first_fixture = self.repository("first", "fixture/first")
        second, second_fixture = self.repository("second", "fixture/second")
        first_port = free_port()
        second_port = free_port({first_port})
        self.start({first: first_port, second: second_port},
                   {first: first_fixture, second: second_fixture})
        self.assertEqual(self.board(first_port)["repo"], "fixture/first")
        self.assertEqual(self.board(second_port)["repo"], "fixture/second")

    def test_restarts_a_board_that_exits(self):
        repository, fixture = self.repository("repo", "fixture/restarted")
        port = free_port()
        supervisor, _ = self.start({repository: port}, {repository: fixture})
        self.board(port)
        old_pid = self.child_pid(supervisor.pid, port)
        self.assertIsNotNone(old_pid)
        os.kill(old_pid, signal.SIGTERM)
        deadline = time.monotonic() + 10
        new_pid = None
        while time.monotonic() < deadline:
            candidate = self.child_pid(supervisor.pid, port)
            if candidate is not None and candidate != old_pid:
                new_pid = candidate
                break
            time.sleep(0.05)
        self.assertIsNotNone(new_pid)
        self.assertEqual(self.board(port)["repo"], "fixture/restarted")

    def test_runs_the_new_code_after_the_checkout_files_change(self):
        repository, fixture = self.repository("repo", "fixture/updated")
        port = free_port()
        copy = self.copied_supervisor()
        supervisor, log = self.start({repository: port}, {repository: fixture}, copy)
        self.board(port)
        old_pid = self.child_pid(supervisor.pid, port)
        self.assertIsNotNone(old_pid)
        events = copy.parents[1] / "tools" / "verify-ticket" / "scripts" / "events.py"
        events.write_text(events.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
        new_pid = self.wait_for_new_child(supervisor.pid, port, old_pid)
        self.assertEqual(self.board(port)["repo"], "fixture/updated")
        self.assertIsNone(supervisor.poll(), "the supervisor must replace itself, not exit")
        with self.assertRaises(ProcessLookupError):
            os.kill(old_pid, 0)
        self.assertNotEqual(new_pid, old_pid)

    def test_a_changed_role_table_restarts_the_board(self):
        repository, fixture = self.repository("repo", "fixture/roles")
        port = free_port()
        copy = self.copied_supervisor()
        supervisor, log = self.start({repository: port}, {repository: fixture}, copy)
        self.board(port)
        old_pid = self.child_pid(supervisor.pid, port)
        self.assertIsNotNone(old_pid)
        roles = copy.parents[1] / "tools" / "dispatch" / "roles.json"
        roles.write_text(roles.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        new_pid = self.wait_for_new_child(supervisor.pid, port, old_pid)
        self.assertNotEqual(new_pid, old_pid)

    def test_a_board_started_outside_the_supervisor_exits_when_its_code_changes(self):
        repository, fixture = self.repository("repo", "fixture/orphan")
        copy = self.copied_supervisor()
        port = free_port()
        env = os.environ.copy()
        env.update({"MMW_HOME": str(self.home), "PATH": str(self.bin) + os.pathsep + env["PATH"],
                    "MMW_TEST_REPO_FIXTURES": json.dumps({str(repository.resolve()): str(fixture)})})
        log = (self.base / "server.log").open("w+", encoding="utf-8")
        server = subprocess.Popen(
            [sys.executable, "-u", str(copy.with_name("server.py")), "--port", str(port),
             "--watch-interval", "0.05"],
            cwd=repository, env=env, stdout=log, stderr=subprocess.STDOUT,
        )
        self.processes.append((server, log))
        self.assertEqual(self.board(port)["repo"], "fixture/orphan")
        gates = copy.with_name("gates.py")
        gates.write_text(gates.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
        self.assertEqual(server.wait(timeout=10), 0)

    def test_skips_a_missing_repository(self):
        repository, fixture = self.repository("present", "fixture/present")
        missing = self.base / "missing-repository"
        port = free_port()
        _, log = self.start({repository: port, missing: free_port()}, {repository: fixture})
        self.assertEqual(self.board(port)["repo"], "fixture/present")
        deadline = time.monotonic() + 5
        text = ""
        while time.monotonic() < deadline:
            log.flush()
            log.seek(0)
            text = log.read()
            if str(missing) in text:
                break
            time.sleep(0.05)
        self.assertIn(str(missing), text)



class EnsureFixture(SupervisorFixture):
    def setUp(self):
        super().setUp()
        self.owned = []
        self.script = self.copied_supervisor()
        self.port = free_port()
        self.script.write_text(self.script.read_text().replace('FIRST_PORT = 47100', f'FIRST_PORT = {self.port}'))
        self.repo, self.fixture = self.repository('ensured', 'fixture/ensured')
        self.env = dict(os.environ, MMW_HOME=str(self.home), HOME=str(self.base/'user'),
                        PATH=str(self.bin)+os.pathsep+os.environ['PATH'],
                        MMW_TEST_REPO_FIXTURES=json.dumps({str(self.repo.resolve()):str(self.fixture)}))

    def own_current_processes(self):
        env=dict(os.environ, LC_ALL='C', LANG='C', TZ='UTC')
        lines = subprocess.check_output(['ps','-axo','pid=,lstart=,command='], text=True,env=env).splitlines()
        for line in lines:
            fields=line.strip().split(None,6)
            if len(fields)==7 and str(self.script.parent) in fields[6] and ('server.py --port' in fields[6] or 'supervisor.py --interval' in fields[6]):
                record=(int(fields[0]),' '.join(fields[1:6]))
                if record not in self.owned:self.owned.append(record)

    def tearDown(self):
        self.stop_owned()
        super().tearDown()

    def stop_owned(self):
        self.own_current_processes()
        for pid,identity in reversed(self.owned):
            if not self._alive(pid,identity):continue
            try:os.kill(pid,signal.SIGTERM)
            except ProcessLookupError:continue
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            if not any(self._alive(pid,identity) for pid,identity in self.owned):return
            time.sleep(.05)
        for pid,identity in self.owned:
            if self._alive(pid,identity):os.kill(pid,signal.SIGKILL)

    @staticmethod
    def _alive(pid,identity):
        env=dict(os.environ, LC_ALL='C', LANG='C', TZ='UTC')
        out=subprocess.run(['ps','-o','lstart=,stat=','-p',str(pid)],capture_output=True,text=True,env=env).stdout.split()
        return len(out)==6 and ' '.join(out[:5])==identity and not out[5].startswith('Z')

    def ensure(self):
        result=subprocess.run([sys.executable,str(self.script),'--ensure',str(self.repo),'--interval','.05'],
                              env=self.env,capture_output=True,text=True,timeout=15)
        self.own_current_processes()
        return result


class ExplicitEnsureTests(EnsureFixture, unittest.TestCase):
    def test_existing_reserved_port_occupied_by_another_service_is_refused(self):
        import socket
        with socket.socket() as other:
            other.bind(('127.0.0.1',self.port));other.listen()
            (self.home/'boards.json').write_text(json.dumps({str(self.repo.resolve()):self.port}))
            result=self.ensure()
            self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('occupied',result.stderr)
            with socket.create_connection(('127.0.0.1',self.port),timeout=.2):pass

    def test_ensure_explicitly_starts_one_keeper_and_reuses_it(self):
        first=self.ensure();self.assertEqual(first.returncode,0,first.stderr)
        self.assertEqual(int(first.stdout.strip()),self.port)
        record_path=self.home/'board-supervisor.json'
        self.assertTrue(record_path.exists(),'explicit ensure must retain the existing supervisor loop without installation')
        record=json.loads(record_path.read_text());self.owned.append((record['pid'],record['identity']))
        self.assertTrue(record['identity']);self.assertEqual(self.board(self.port)['repo'],'fixture/ensured')
        child=self.child_pid(record['pid'],self.port);self.assertIsNotNone(child)
        second=self.ensure();self.assertEqual(second.returncode,0,second.stderr)
        self.assertEqual(json.loads(record_path.read_text())['pid'],record['pid'])
        self.assertEqual(self.child_pid(record['pid'],self.port),child)
        self.assertEqual((self.home/'boards.json').stat().st_mode & 0o777,0o600)

    def test_default_state_is_v5_when_mmw_home_is_unset(self):
        env=dict(self.env);env.pop('MMW_HOME',None)
        result=subprocess.run([sys.executable,str(self.script),'--register',str(self.repo)],env=env,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue((Path(env['HOME'])/'.mmw-v5/boards.json').exists())
        self.assertFalse((Path(env['HOME'])/'.mmw').exists())

    def test_two_ensure_calls_share_the_keeper_and_registered_port(self):
        args=[sys.executable,str(self.script),'--ensure',str(self.repo),'--interval','.05']
        calls=[subprocess.Popen(args,env=self.env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(2)]
        for call in calls:
            out,err=call.communicate(timeout=15);self.assertEqual(call.returncode,0,out+err);self.assertEqual(int(out.strip()),self.port)
        self.own_current_processes()
        record=json.loads((self.home/'board-supervisor.json').read_text())
        self.assertTrue(self._alive(record['pid'],record['identity']))
        children=subprocess.check_output(['ps','-axo','ppid=,command='],text=True).splitlines()
        self.assertEqual(sum(line.strip().startswith(str(record['pid'])+' ') and 'server.py --port' in line for line in children),1)

    def test_a_stale_process_identity_does_not_stop_an_unrelated_process(self):
        log=(self.base/'unrelated.log').open('w+')
        unrelated=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],stdout=log,stderr=log)
        self.processes.append((unrelated,log))
        (self.home/'board-supervisor.json').write_text(json.dumps({'pid':unrelated.pid,'identity':'stale','script':str(self.script)}))
        result=self.ensure();self.assertEqual(result.returncode,0,result.stderr)
        self.assertIsNone(unrelated.poll())
        self.assertNotEqual(json.loads((self.home/'board-supervisor.json').read_text())['pid'],unrelated.pid)

    def test_relative_home_is_preserved_when_the_keeper_changes_working_directory(self):
        env=dict(self.env,MMW_HOME='relative-home')
        result=subprocess.run([sys.executable,str(self.script),'--ensure',str(self.repo),'--interval','.05'],
                              cwd=self.base,env=env,capture_output=True,text=True,timeout=20)
        self.own_current_processes()
        self.assertEqual(result.returncode,0,result.stderr)
        record=json.loads((self.base/'relative-home/board-supervisor.json').read_text())
        self.assertTrue(self._alive(record['pid'],record['identity']))
        self.assertEqual(self.board(self.port)['repo'],'fixture/ensured')
        self.assertFalse((self.base/'relative-home/relative-home').exists())


if __name__ == "__main__":
    unittest.main()
