#!/usr/bin/env python3
"""Run the unchanged board against isolated GitHub replies; never writes the real tracker."""

import argparse
import concurrent.futures
import contextlib
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mmw-v4/tests/board"))
from board_process import RunningBoard
from test_board_data import container, event, leaf, tickets


def ev(name, n, ident, second, **fields):
    at = (dt.datetime(2026, 10, 31, 8, tzinfo=dt.timezone.utc)
          + dt.timedelta(seconds=second)).isoformat().replace("+00:00", "Z")
    row = event(name, n, id=ident, at=at, **fields)
    row.update(created_at=at, updated_at=at)
    return row


def started(n):
    return ev("worker.started", n, n * 100 + 1, 0, session=f"fixture-worker-{n}",
              runner="codex-app", machine="fixture", host="codex", model="fixture",
              effort="high", grade="senior-worker", worktree="/tmp/mmw-641-fixture",
              branch=f"ticket-{n}", base="a" * 40)


def workload(count=2):
    nodes = [leaf(11, "source ticket")]
    nodes += [leaf(n, f"dependent ticket {n}", blocked=[{"number": 11, "state": "OPEN"}])
              for n in range(12, 11 + count)]
    tree = container(1, "diagnostic map",
                     [container(10, "diagnostic spec", nodes, ["mmw:spec"])], ["mmw:map"])
    old = [started(11), ev("ticket.claimed", 11, 1102, 1)]
    landed = old + [ev("ticket.passed", 11, 1103, 2),
                    ev("ticket.landed", 11, 1104, 3, into="dev")]
    regressed = landed + [ev("ticket.regressed", 11, 1105, 4, commit="b" * 40)]
    review = old + [ev("reviewer.started", 11, 1103, 2, session="fixture-reviewer",
                       runner="codex-app", machine="fixture"),
                    ev("reviewer.reported", 11, 1104, 3),
                    ev("ticket.claimed", 11, 1105, 4)]
    closed = json.loads(json.dumps(tree))
    closed["subIssues"]["nodes"][0]["subIssues"]["nodes"][0]["state"] = "CLOSED"
    result = {"repo": "fixture/mmw-641", "maps": [
        {"number": 1, "title": "diagnostic map", "state": "OPEN",
         "labels": [{"name": "mmw:map"}]}], "trees": [tree, closed], "tree_active": 0,
        "comments": {"11": [{"etag": '"working"', "comments": old},
                            {"etag": '"landed"', "comments": landed},
                            {"etag": '"regressed"', "comments": regressed},
                            {"etag": '"review-returned"', "comments": review}]},
        "comment_active": {"11": 0}}
    for n in range(12, 11 + count):
        result["comments"][str(n)] = [{"etag": f'"active-{n}"', "comments": [started(n)]}]
    return result


@contextlib.contextmanager
def isolated_board(data, delay=0):
    with tempfile.TemporaryDirectory(prefix="mmw-641-home-") as temp:
        directory = Path(temp)
        home = directory / "home"
        home.mkdir()
        for name in ("models.json", "catalog.json"):
            shutil.copyfile(ROOT / "scripts/dev/board-fixtures" / name, home / name)
        fake = ROOT / "mmw-v4/tests/board/github/gh"
        bin_dir = directory / "bin"
        bin_dir.mkdir()
        wrapper = bin_dir / "gh"
        wrapper.write_text(
            "#!/usr/bin/env python3\n"
            "import json,os,re,subprocess,sys,time\nfrom pathlib import Path\n"
            "start=time.perf_counter()\ntime.sleep(float(os.environ['MMW_641_DELAY']))\n"
            f"run=subprocess.run([{str(fake)!r},*sys.argv[1:]],capture_output=True,text=True)\n"
            "status=re.search(r'HTTP/\\S+ (\\d+)',run.stdout)\n"
            "row={'command':sys.argv[1:3],'seconds':time.perf_counter()-start,"
            "'status':int(status[1]) if status else None,'exit':run.returncode}\n"
            "with (Path(os.environ['MMW_BOARD_FAKE_DIR'])/'spans.jsonl').open('a') as f:"
            " f.write(json.dumps(row)+'\\n')\n"
            "sys.stdout.write(run.stdout);sys.stderr.write(run.stderr)\nsys.exit(run.returncode)\n")
        wrapper.chmod(0o700)
        environment = {"MMW_HOME": str(home),
            "MMW_HOST_CATALOG": str(ROOT / "scripts/dev/board-fixtures/host-catalog.json"),
            "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"], "MMW_641_DELAY": str(delay)}
        with RunningBoard(environment=environment, fixture=data) as board:
            yield board


def read(board, method="GET"):
    start = time.perf_counter()
    status, raw = board.request(method, "/api/board" if method == "GET" else "/api/board/refresh",
                                headers={} if method == "GET" else board.write_headers)
    payload = json.loads(raw)
    if status != 200 or payload.get("read_failed"):
        raise RuntimeError(f"board read failed: HTTP {status}, {payload.get('read_failed')}")
    return payload, time.perf_counter() - start


def reproduce(output):
    data = workload()
    with isolated_board(data) as board:
        first, _ = read(board)
        assert tickets(first)[11]["state"] == "open"
        data["tree_active"], data["comment_active"]["11"] = 1, 1
        board.write_fixture(data)
        landed, _ = read(board, "POST")
        source = tickets(landed)[11]
        result = [{"contract": "manual refresh reads closure and releases dependency",
            "passed": source["state"] == "closed" and source["blocker_hold"] == "",
            "observed": {k: source[k] for k in ("state", "blocker_hold")},
            "landed_event_read": source["fold"]["landed"]}]
        before = len(board.fixture_calls())
        data["tree_active"], data["comment_active"]["11"] = 0, 2
        board.write_fixture(data)
        regressed, _ = read(board, "POST")
        source = tickets(regressed)[11]
        result.append({"contract": "reads an existing regression after landing",
            "passed": any(e["event"] == "ticket.regressed" for e in source["events"]),
            "observed_events": [e["event"] for e in source["events"]],
            "source_comment_reads": sum(c[:2] == ["api", "-i"] and "/issues/11/comments" in c[2]
                                        for c in board.fixture_calls()[before:])})
        (output / "landed-response.json").write_text(json.dumps(landed))
    (output / "state-reproduction.json").write_text(json.dumps(result, indent=2))
    return result


def benchmark(output, count, delay, repeats):
    runs = []
    with isolated_board(workload(count), delay) as board:
        payload, cold = read(board)
        assert len(tickets(payload)) == count
        for repeat in range(repeats):
            for clients in ((1, 2) if repeat % 2 == 0 else (2, 1)):
                before = len(board.fixture_calls())
                barrier = threading.Barrier(clients)
                def request(_):
                    barrier.wait()
                    payload, duration = read(board)
                    assert len(tickets(payload)) == count, "incomplete board"
                    return duration
                start = time.perf_counter()
                with concurrent.futures.ThreadPoolExecutor(max_workers=clients) as pool:
                    durations = list(pool.map(request, range(clients)))
                calls = board.fixture_calls()[before:]
                runs.append({"repeat": repeat, "clients": clients,
                    "seconds": time.perf_counter() - start, "client_seconds": durations,
                    "gh_commands": len(calls), "errors": 0,
                    "conditional_comments": sum(c[:2] == ["api", "-i"]
                        and any(v.startswith("If-None-Match:") for v in c) for c in calls)})
        (output / "gh-spans.jsonl").write_text((board.directory / "spans.jsonl").read_text())
    summary = {}
    for clients in (1, 2):
        rows = [r for r in runs if r["clients"] == clients]
        times = [r["seconds"] for r in rows]
        summary[str(clients)] = {"median_seconds": statistics.median(times),
            "range_seconds": [min(times), max(times)],
            "gh_commands": [r["gh_commands"] for r in rows], "errors": 0}
    result = {"kind": "controlled replay, not live GitHub latency", "tickets": count,
        "injected_delay_seconds_per_gh": delay, "repeats": repeats,
        "cold_seconds": cold, "summary": summary, "runs": runs}
    (output / "baseline.json").write_text(json.dumps(result, indent=2))
    return result


def browser_reproduce(output):
    result = []
    for name, active in (("landed-edge", 0), ("review-return", 3)):
        data = workload()
        data["comment_active"]["11"] = active
        with isolated_board(data) as board:
            result_path = output / f"{name}.json"
            result_path.unlink(missing_ok=True)
            run = subprocess.run(["node", str(Path(__file__).with_name("reproduce-ui.mjs")),
                board.origin, str(board.directory), str(output), name],
                cwd=ROOT, capture_output=True, text=True, timeout=45)
            print(run.stdout, end="")
            if run.returncode not in (0, 1) or not result_path.exists():
                raise RuntimeError(run.stderr or run.stdout)
            result.append(json.loads(result_path.read_text()))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("reproduce", "benchmark", "browser"))
    parser.add_argument("--output", type=Path, default=ROOT / ".scratch/fix-641/diagnosis")
    parser.add_argument("--tickets", type=int, default=12)
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.mode == "benchmark":
        result = benchmark(args.output, args.tickets, args.delay, args.repeats)
        print(json.dumps({k: v for k, v in result.items() if k != "runs"}, indent=2))
    else:
        result = reproduce(args.output) if args.mode == "reproduce" else browser_reproduce(args.output)
        print(json.dumps(result, indent=2))
        raise SystemExit(1 if any(not r["passed"] for r in result) else 0)
