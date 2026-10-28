#!/usr/bin/env bash

run_scenarios() {
  local script="$1" fn name code
  shift
  local scenarios=() wanted=() parallel=() serial=()
  while read -r _ _ fn; do
    case "$fn" in
      scenario_start_worker) scenarios+=(start-worker) ;;
      scenario_start_reviewer) scenarios+=(start-reviewer) ;;
      scenario_*) scenarios+=("${fn#scenario_}") ;;
    esac
  done < <(declare -F)

  if [ "$#" -eq 1 ] && [ "$1" = all ]; then
    wanted=("${scenarios[@]}")
  else
    wanted=("$@")
  fi
  if [ "${#wanted[@]}" -eq 0 ]; then
    echo "usage: $script $(IFS='|'; echo "${scenarios[*]}")|all" >&2
    return 2
  fi
  for name in "${wanted[@]}"; do
    local known=0
    for fn in "${scenarios[@]}"; do
      if [ "$fn" = "$name" ]; then known=1; break; fi
    done
    if [ "$known" -eq 0 ]; then
      echo "unknown scenario '$name'; known names: ${scenarios[*]}" >&2
      return 2
    fi
  done

  if [ "${#wanted[@]}" -eq 1 ]; then
    if declare -F setup_fixture >/dev/null; then setup_fixture; fi
    name="${wanted[0]}"
    fn="scenario_${name//-/_}"
    echo "=== $name"
    "$fn"
    code=$?
    if [ "$code" -ne 0 ] || [ "${rc:-0}" -ne 0 ]; then
      echo "$name failed: $fn exited $code, assertions ${rc:-0}" >&2
      return 1
    fi
    echo "PASS $name"
    return 0
  fi

  for name in "${wanted[@]}"; do
    if declare -F needs_exclusive_ports >/dev/null && needs_exclusive_ports "$name"; then
      serial+=("$name")
    else
      parallel+=("$name")
    fi
  done
  python3 - "$script" "${#parallel[@]}" ${parallel[@]+"${parallel[@]}"} ${serial[@]+"${serial[@]}"} <<'PY'
from collections import deque
import fcntl
import os
import signal
import subprocess
import sys
import tempfile
import time

script = sys.argv[1]
count = int(sys.argv[2])
parallel = sys.argv[3:3 + count]
serial = sys.argv[3 + count:]
raw_jobs = os.environ.get("MMW_TEST_JOBS", str(os.cpu_count() or 1))
if not raw_jobs.isascii() or not raw_jobs.isdecimal() or int(raw_jobs) < 1:
    print(f"MMW_TEST_JOBS must be a positive integer, got {raw_jobs!r}; set it before running {script}", file=sys.stderr)
    sys.exit(2)


failed = []


def report(name, code, output):
    if code:
        failed.append((name, code, output))
    else:
        sys.stdout.buffer.write(output)
        sys.stdout.buffer.flush()


def run_group(names, limit, environment):
    pending = deque(names)
    active = []
    try:
        while pending or active:
            while pending and len(active) < limit:
                name = pending.popleft()
                output = tempfile.TemporaryFile()
                process = subprocess.Popen(["bash", script, name], stdout=output,
                                           stderr=subprocess.STDOUT, env=environment,
                                           start_new_session=True)
                active.append((name, process, output))
            for job in active[:]:
                name, process, output = job
                code = process.poll()
                if code is not None:
                    active.remove(job)
                    output.seek(0)
                    report(name, code, output.read())
                    output.close()
            if active:
                time.sleep(.02)
    finally:
        for _, process, _ in active:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        deadline = time.monotonic() + 5
        while any(process.poll() is None for _, process, _ in active) and time.monotonic() < deadline:
            time.sleep(.02)
        for _, process, output in active:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait()
            output.close()


def interrupt(signum, frame):
    raise KeyboardInterrupt


signal.signal(signal.SIGTERM, interrupt)
environment = dict(os.environ)
environment.setdefault("MMW_TEST_BOARD_LOCK", f"/tmp/mmw-dispatch-board-ports-{os.getuid()}.lock")
try:
    run_group(parallel, int(raw_jobs), environment)
    if serial:
        with open(environment["MMW_TEST_BOARD_LOCK"], "a") as lock:
            deadline = time.monotonic() + 60
            waiting = False
            while True:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if not waiting:
                        print(f"Waiting for dispatch board port lock {lock.name}", file=sys.stderr, flush=True)
                        waiting = True
                    if time.monotonic() >= deadline:
                        sys.exit(f"Dispatch board port lock {lock.name} stayed busy for 60 seconds; stop the other suite before retrying {script}")
                    time.sleep(.02)
            environment["MMW_TEST_BOARD_LOCK_HELD"] = "1"
            run_group(serial, 1, environment)
except KeyboardInterrupt:
    sys.exit("Interrupted: stopped active scenarios and discarded queued scenarios")
for name, code, output in failed:
    print(f"FAIL {name} (exit {code})", flush=True)
    sys.stdout.buffer.write(output)
    sys.stdout.buffer.flush()
sys.exit(1 if failed else 0)
PY
}
