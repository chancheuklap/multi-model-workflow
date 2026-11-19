#!/usr/bin/env python3
"""Run one named journey against this repository's product, and prove it can fail.

    journey.py run <name> [--break "<METHOD> <route>"]

`<name>` is `<product>/<flow>`, including
a repository with one product. The run uses that product's `start`, `stop` and
`discover`. The script is `<journeys>/<flow>` (a `run` executable, or the command
`package.json` declares), and `journeys` defaults to `.mmw/<product>/journeys`.

Named products start their needs first and receive each dependency's discovered keys
under its uppercase product prefix. Cleanup stops only products this invocation
started, in reverse order, then checks their port segments. A dependency already
running under this lease is left running for its owner. A tested product already
started under this lease is refused before any commands run.

Acquires or reuses this worktree's lease, runs `start` every time, runs `discover`
and puts each printed address into the environment under its uppercase key (plus
the lease variables and `MMW_EVIDENCE_DIR`). Each started product that declares
`doctor` runs that command after its own `discover`. A dependency runs it before
the product under test starts. The product under test runs it before the script. The command
receives `MMW_WORKTREE_COMMIT`, this worktree's commit. A non-zero `doctor`, or
one that exits 0 without a `pid`, stops the run before the script and names that
product. Otherwise the script runs. When the script exits non-zero, each of those
commands runs once more before `stop`, with `MMW_DOCTOR_PID` set to the pid that
product's first `doctor` printed. `stop` runs whether the script succeeded or not.

With `--break`, it starts the product again with `MMW_BREAK` supplied only to `start`,
requires `BREAK ARMED <METHOD> <route>`, discovers the product again, and re-runs the
script in the same environment. That pass must fail. Without `--break`, the contract
ticket's smoke journey keeps the product down, moves discovered addresses to a closed
port, and runs the same script again. An oracle that cannot go red is not an
oracle (`docs/adr/0008-silence-is-never-a-pass.md`).

Cleanup stops every product still owned by this invocation and its ports must be quiet: a journey ends leaving the
machine as it found it, and anything still listening on the slot outlives the run and
blocks whichever run is given the slot next.

A script that exits non-zero is printed in full first (stdout, then stderr, SGR
color codes removed). `JOURNEY FAILED` follows, then each second `doctor`'s
output for every started product that declares one, then `MMW_DATA_DIR <path>`,
then the files in this run's evidence directory. A pid that differs from the
first is written on its own line there. A `start`, `discover` or `doctor`
that fails names the command, its command string and its exit code, forwards its
output or `(no output)`, names `MMW_DATA_DIR`, and exits 2. A `doctor` that
exits 0 without a `pid` also writes that a pid was expected and what was found in its place.
A product with a name is named on that line. The `--break` second pass prints the script only when
that pass exits 0.

    JOURNEY OK <name>                                 exit 0
    JOURNEY FAILED <name> at <last line>              exit 1
    JOURNEY GREEN WITH BREAK <name> — <line>          exit 1
    JOURNEY GREEN WITHOUT PRODUCT <name> — <line>     exit 1
    JOURNEY LEFT THE PRODUCT UP <name> — <listeners>  exit 1
    the run never got as far as the script            exit 2
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from target_config import DISCOVER_NOTES, discover, repo_root, run_command, target_config  # noqa: E402
from lease import (  # noqa: E402
    ProductCommandFailed, ProductRun, TargetJSONError, addresses_into,
    holder, judge_run, listener, ports_of, product_at_port, product_port_ranges,
    product_journey, read_target_json, registered, worktree_of,
)
from refusal import refusal  # noqa: E402

# The first critical-flow ticket builds the fault-injection switch, so a switch that does not arm is
# that worker's own defect to fix; for any other ticket it is a fault to report.
BREAK_NEXT = ("If this ticket owns .mmw/<product>/harness/, fix the switch and run the criterion "
              "again; otherwise report the ticket blocked and stop.")

BREAK_RE = re.compile(r"[A-Z]+ /\S*")
# SGR color sequences only. Other ANSI (cursor, OSC) is not a color code.
COLOR_RE = re.compile(r"\x1b\[[0-9;]*m")


def last_line(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else "(no output)"


def strip_color(text: str) -> str:
    return COLOR_RE.sub("", text)


def command_was_silent(proc: subprocess.CompletedProcess) -> bool:
    if (proc.stdout or "").strip():
        return False
    lines = [line for line in (proc.stderr or "").splitlines() if line.strip()]
    return all(line.startswith(DISCOVER_NOTES) for line in lines)


def prepare_evidence(root: Path, name: str, *, break_pass: bool) -> Path:
    """An empty directory for this pass. The break pass keeps the first pass's files."""
    dest = root / ".scratch" / "journeys" / name
    if break_pass:
        dest = dest / "break"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    return dest.resolve()


def emit_evidence(dest: Path) -> None:
    files = sorted(item for item in dest.rglob("*") if item.is_file())
    if not files:
        print(f"no evidence files in {dest}; references/journey.md")
        return
    for path in files:
        print(path)


def emit_script_output(proc: subprocess.CompletedProcess) -> str:
    """Print the script's stdout and then its stderr, and return the line `at` quotes."""
    parts: list[str] = []
    for chunk in (strip_color(proc.stdout or ""), strip_color(proc.stderr or "")):
        if not chunk:
            continue
        if parts and not parts[-1].endswith("\n"):
            parts.append("\n")
        parts.append(chunk)
    text = "".join(parts)
    if text:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
    return last_line(text)


def still_up(root: Path, initial_started: list[str] | None = None) -> list[str]:
    """What still listens on this run's slot, once its `stop` has been run for the last
    time: one `port <n> pid <pid> cwd <dir>` line each, empty when the slot is quiet.

    A journey's last act is to leave the machine as it found it. A script that starts
    anything itself leaves that process behind on this slot. The next run given this slot
    then starts onto live ports and can report nothing but blocked, far from the journey
    that caused it, which is how agentflow spent a night in 2026-09-11. The run that left
    them says so itself instead.
    """
    record = registered(worktree_of(root))
    if record is None:
        return []
    left = []
    previous_ports = set()
    segments = product_port_ranges(record) if initial_started else {}
    # A product the layout no longer lists has no segment; its ports are checked as this run's.
    for name in initial_started or []:
        previous_ports.update(segments.get(name, ()))
    for port in ports_of(record["slot"]):
        if port in previous_ports:
            continue
        pid = listener(port)
        if pid is not None:
            left.append(f"{product_at_port(record, port)}port {port} pid {pid} cwd {holder(pid)}")
    return left


def journey_command(dest: Path) -> list[str] | str | None:
    """How to run `<journeys>/<name>`: a `run` file, or `package.json`'s `scripts.run`."""
    runner = dest / "run"
    if runner.is_file() and os.access(runner, os.X_OK):
        return [str(runner)]
    package = dest / "package.json"
    if package.is_file():
        try:
            data = json.loads(package.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"{package} cannot be read as JSON: {exc}")
        scripts = data.get("scripts") if isinstance(data, dict) else None
        command = scripts.get("run") if isinstance(scripts, dict) else None
        if isinstance(command, str) and command.strip():
            return command
    return None


ADDRESS_RE = re.compile(r"^([A-Za-z][A-Za-z0-9+.\-]*://)?([^/:\s]+):(\d+)(.*)$")


def closed_port() -> int:
    """A port on this machine that nothing is listening on: bound, read, released."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def repointed(value: str, port: int) -> str | None:
    """`value` with its port replaced, or None when it carries no address."""
    found = ADDRESS_RE.match(value)
    if not found:
        return None
    scheme, host, _, rest = found.groups()
    return f"{scheme or ''}{host}:{port}{rest}"


def negative_env(env: dict[str, str], data: dict) -> dict[str, str]:
    """The environment the control pass gets: the same one, pointing nowhere.

    Only the keys `discover` printed are touched, and only those that carry a port —
    `instance` is left as it is, because a script may read it to say which run it is
    rather than to reach anything. The lease variables stay too: the control pass is
    the same run, not a different one.

    The script gets no pass-specific variable: it cannot tell the control from the real
    run and fail early instead of proving that its product assertion can go red.
    """
    port = closed_port()
    control = dict(env)
    for key in data:
        name = str(key).upper()
        moved = repointed(control.get(name, ""), port)
        if moved is not None:
            control[name] = moved
    return control


def doctor_environment(env: dict[str, str], pid: str | None = None) -> dict[str, str]:
    """The lease environment `doctor` runs in; the lease carries this worktree's commit
    as `MMW_WORKTREE_COMMIT`.

    `MMW_DOCTOR_PID` from the parent session is dropped. `pid` is the one the
    first `doctor` printed, and is set only on the run after a failed script.
    """
    prepared = dict(env)
    prepared.pop("MMW_DOCTOR_PID", None)
    if pid is not None:
        prepared["MMW_DOCTOR_PID"] = pid
    return prepared


def reported_pid(proc: subprocess.CompletedProcess) -> str | None:
    """The `pid` a `doctor` that exited 0 printed, or None when it printed none."""
    try:
        data = json.loads((proc.stdout or "").strip())
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or "pid" not in data:
        return None
    pid = data["pid"]
    if isinstance(pid, bool) or not isinstance(pid, (int, str)):
        return None
    text = str(pid).strip()
    return text or None


def pid_actual(proc: subprocess.CompletedProcess) -> str:
    """What a `doctor` showed where a usable `pid` would be.

    A usable `pid` is a number or a non-empty string. Anything else is the
    failure `examine` reports, so the words here are the actual half of that line.
    """
    raw = (proc.stdout or "").strip()
    if not raw:
        return "none"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return "not a JSON object"
    if not isinstance(data, dict) or "pid" not in data:
        return "no pid"
    return json.dumps(data["pid"], ensure_ascii=False)


def journey_binding(name: str, root: Path) -> tuple[dict, Path]:
    """The product config this run starts, and the directory the script lives in.

    Every journey takes `<product>/<flow>` and that product's `journeys` directory.
    `target_config` reports a missing file, a
    missing product and a product file that is not JSON.
    """
    try:
        read_target_json(root)
    except TargetJSONError as exc:
        raise SystemExit(str(exc)) from None
    parts = product_journey(name)
    if parts is None:
        raise SystemExit(refusal(
            f"journey name {name!r} is not <product>/<flow>.",
            "Every journey needs a product name, including a single-product repository.",
            "Run `journey.py run <product>/<flow>` again.",
        ))
    product, flow = parts
    cfg = target_config(root, product)
    journeys = cfg.get("journeys") or f".mmw/{product}/journeys"
    return cfg, (root / journeys / flow).resolve()


def _run_named(name: str, root: Path, break_spec: str | None = None) -> int:
    try:
        cfg, dest = journey_binding(name, root)
        stack = ProductRun(root, cfg.name)
        if cfg.name in stack.initial_started:
            raise SystemExit(refusal(
                f"Product {cfg.name} is already started under this lease.",
                "This journey cannot restart or stop a product another run owns.",
                "Stop that instance through its owner, then run the journey again.",
            ))
        env = stack.env()
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 2
    env.pop("MMW_BREAK", None)

    def bail(message: str | None = None,
             proc: subprocess.CompletedProcess | None = None,
             kind: str | None = None,
             command: str | None = None,
             detail: str | None = None) -> int:
        stack.stop()
        if proc is not None:
            # stdout is block-buffered on a pipe. Flush the naming line, and the
            # command's own stdout, before stderr, or a merged stream shows the
            # command's error first.
            print(f"{kind} {command} exit {proc.returncode}")
            sys.stdout.flush()
            if proc.stdout:
                sys.stdout.write(proc.stdout)
                if not proc.stdout.endswith("\n"):
                    sys.stdout.write("\n")
                sys.stdout.flush()
            if proc.stderr:
                sys.stderr.write(proc.stderr)
            if detail:
                print(detail)
                sys.stdout.flush()
            if command_was_silent(proc):
                print("(no output)")
            print(f"MMW_DATA_DIR {env['MMW_DATA_DIR']}")
        if message:
            print(message, file=sys.stderr)
        return 2

    seen_pids: dict[str, str] = {}

    def run_doctor(product_cfg: dict, product_env: dict[str, str],
                   pid: str | None = None
                   ) -> tuple[str, str | None, subprocess.CompletedProcess] | None:
        command = product_cfg.get("doctor")
        if not isinstance(command, str) or not command.strip():
            return None
        product = getattr(product_cfg, "name", None)
        proc = run_command(
            command, root, env=doctor_environment(product_env, pid), check=False)
        return command, product, proc

    def examine(product_cfg: dict, product_env: dict[str, str]) -> int | None:
        ran = run_doctor(product_cfg, product_env)
        if ran is None:
            return None
        command, product, proc = ran
        kind = "doctor" if not product else f"product {product} doctor"
        found = reported_pid(proc)
        if proc.returncode != 0:
            return bail(proc=proc, kind=kind, command=command)
        if found is None:
            label = product or "doctor"
            return bail(
                proc=proc, kind=kind, command=command,
                detail=(f"product {label} doctor pid expected a pid "
                        f"actual {pid_actual(proc)}"))
        seen_pids[product or ""] = found
        return None

    def diagnose(product_cfg: dict, product_env: dict[str, str]) -> str:
        product_name = getattr(product_cfg, "name", None)
        previous = seen_pids.get(product_name or "")
        ran = run_doctor(product_cfg, product_env, previous)
        if ran is None:
            return ""
        _, product, proc = ran
        parts: list[str] = []
        for chunk in (proc.stdout or "", proc.stderr or ""):
            if chunk:
                parts.append(chunk if chunk.endswith("\n") else chunk + "\n")
        second = reported_pid(proc)
        if previous is not None and second is not None and previous != second:
            label = product or "doctor"
            parts.append(f"product {label} doctor pid expected {previous} actual {second}\n")
        return "".join(parts)

    def diagnose_started() -> str:
        parts: list[str] = []
        for product in stack.order:
            if product == cfg.name:
                parts.append(diagnose(cfg, env))
            else:
                parts.append(diagnose(target_config(root, product), stack.env(product)))
        return "".join(parts)

    start_cmd = cfg.get("start")
    if not isinstance(start_cmd, str) or not start_cmd.strip():
        return bail(f"`.mmw/{cfg.name}/target.json` has no `start` command")

    stop_cmd = cfg.get("stop")
    if not isinstance(stop_cmd, str) or not stop_cmd.strip():
        return bail(f"`.mmw/{cfg.name}/target.json` has no `stop` command")

    # A run that dies in start or discover still replaces the previous run's evidence.
    prepare_evidence(root, name, break_pass=False)

    def prepare_start() -> int | None:
        nonlocal env
        try:
            stack.start_needs()
        except ProductCommandFailed as exc:
            return bail(proc=exc.proc, kind=f"product {exc.product} {exc.kind}", command=exc.command)
        for dependency in stack.order[:-1]:
            failed = examine(target_config(root, dependency), stack.env(dependency))
            if failed is not None:
                return failed
        env = stack.env()
        stack.mark_started(cfg.name)
        return None

    failed = prepare_start()
    if failed is not None:
        return failed
    try:
        run_command(start_cmd, root, env=env)
    except SystemExit as exc:
        return bail(proc=exc.code, kind="start", command=start_cmd)
    try:
        data = discover(cfg, root, env=env)
    except SystemExit as exc:
        return bail(proc=exc.code, kind="discover", command=str(cfg.get("discover")))
    addresses_into(env, data)
    stack.remember(cfg.name, data)
    failed = examine(cfg, env)
    if failed is not None:
        return failed

    spec = journey_command(dest)
    if spec is None:
        stack.stop()
        print(f"JOURNEY FAILED {name} at {dest} has no executable `run` "
              f"and no package.json scripts.run")
        return 1

    def attempt(environment: dict[str, str], *, break_pass: bool = False
                ) -> tuple[subprocess.CompletedProcess, Path]:
        evidence = prepare_evidence(root, name, break_pass=break_pass)
        script_env = dict(environment)
        script_env.pop("FORCE_COLOR", None)
        script_env["MMW_EVIDENCE_DIR"] = str(evidence)
        proc = subprocess.run(
            spec, shell=isinstance(spec, str), cwd=dest,
            capture_output=True, text=True, env=script_env,
        )
        return proc, evidence

    try:
        script, evidence = attempt(env)
        follow_up = diagnose_started() if script.returncode != 0 else ""
    finally:
        stack.stop()

    if script.returncode != 0:
        print(f"JOURNEY FAILED {name} at {emit_script_output(script)}")
        if follow_up:
            sys.stdout.write(follow_up)
        print(f"MMW_DATA_DIR {env['MMW_DATA_DIR']}")
        emit_evidence(evidence)
        return 1

    if break_spec is not None:
        failed = prepare_start()
        if failed is not None:
            return failed
        start_env = dict(env)
        start_env["MMW_BREAK"] = break_spec
        try:
            armed = run_command(start_cmd, root, env=start_env)
        except SystemExit as exc:
            proc = exc.code
            return bail(refusal(
                f"`start` exited {proc.returncode} while arming {break_spec!r}.",
                "The fault-injection switch in references/journey.md did not come up.",
                BREAK_NEXT,
            ), proc=proc, kind="start", command=start_cmd)
        expected_arm = f"BREAK ARMED {break_spec}"
        if expected_arm not in (armed.stdout + armed.stderr).splitlines():
            return bail(refusal(
                f"`start` exited 0 without printing `{expected_arm}`.",
                "The fault-injection switch in references/journey.md was not confirmed.",
                BREAK_NEXT,
            ))
        try:
            control_data = discover(cfg, root, env=env)
        except SystemExit as exc:
            return bail(proc=exc.code, kind="discover", command=str(cfg.get("discover")))
        addresses_into(env, control_data)
        stack.remember(cfg.name, control_data)
        failed = examine(cfg, env)
        if failed is not None:
            return failed
        control_env = env
        green_prefix = f"JOURNEY GREEN WITH BREAK {name} — "
        green_explanation = (
            " — it passed again with that operation failing. Make the journey read the "
            "result back through a different page and assert it there."
        )
    else:
        # The product is down and the addresses point nowhere. A journey that reached it
        # cannot pass this; one that asserted nothing passes it exactly as it passed above,
        # which is the whole difference the run is here to print.
        control_env = negative_env(env, data)
        green_prefix = f"JOURNEY GREEN WITHOUT PRODUCT {name} at "
        green_explanation = (
            " — it passed again with the product stopped and its addresses pointing "
            "nowhere. Make the journey assert something only the running product can "
            "satisfy."
        )
    try:
        control, _control_evidence = attempt(control_env, break_pass=break_spec is not None)
    finally:
        stack.stop()
    if control.returncode == 0:
        # A break pass that passes is the one the worker has to read. A pass that fails
        # as designed stays quiet: that failure is the negative control.
        if break_spec is not None:
            quoted = emit_script_output(control)
        else:
            quoted = last_line(strip_color((control.stdout or "") + (control.stderr or "")))
        print(f"{green_prefix}{quoted}{green_explanation}")
        return 1
    left = still_up(root, stack.initial_started)
    if left:
        print(f"JOURNEY LEFT THE PRODUCT UP {name} — this run's slot still has "
              f"{len(left)} listener(s) after `stop`: {'; '.join(left)}. Whatever started "
              f"them outlives this run and blocks the next run given this slot. A journey "
              f"script starts nothing itself in either pass; "
              f"everything it needs is started by `start` and ended by `stop`.")
        return 1
    print(f"JOURNEY OK {name}")
    return 0


def run_named(name: str, start: Path | None = None, break_spec: str | None = None) -> int:
    root = repo_root(start)
    code: int | None = None
    try:
        with judge_run(root):
            code = _run_named(name, root, break_spec)
    except SystemExit as exc:
        if code is None:
            raise
        print(exc, file=sys.stderr)
        return max(code, 1)
    assert code is not None
    return code


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) not in (2, 4) or argv[0] != "run" or (len(argv) == 4 and argv[2] != "--break"):
        sys.stderr.write('usage: journey.py run <name> [--break "<METHOD> <route>"]\n')
        return 2
    if len(argv) == 4 and not BREAK_RE.fullmatch(argv[3]):
        print(refusal(
            f"--break value {argv[3]!r} does not have one uppercase method, one space, "
            "and a route starting with `/`.",
            "journey.py cannot identify one route to fail.",
            'Use a value such as `--break "POST /items/{id}"` and run the criterion again.',
        ), file=sys.stderr)
        return 2
    return run_named(argv[1], break_spec=argv[3] if len(argv) == 4 else None)


if __name__ == "__main__":
    sys.exit(main())
