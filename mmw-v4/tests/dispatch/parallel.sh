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
    case " ${scenarios[*]} " in
      *" $name "*) ;;
      *)
        echo "unknown scenario '$name'; known names: ${scenarios[*]}" >&2
        return 2 ;;
    esac
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
    if declare -F is_serial >/dev/null && is_serial "$name"; then
      serial+=("$name")
    else
      parallel+=("$name")
    fi
  done
  python3 - "$script" "${#parallel[@]}" ${parallel[@]+"${parallel[@]}"} ${serial[@]+"${serial[@]}"} <<'PY'
import concurrent.futures
import os
import subprocess
import sys

script = sys.argv[1]
count = int(sys.argv[2])
parallel = sys.argv[3:3 + count]
serial = sys.argv[3 + count:]
raw_jobs = os.environ.get("MMW_TEST_JOBS", str(os.cpu_count() or 1))
if not raw_jobs.isascii() or not raw_jobs.isdecimal() or int(raw_jobs) < 1:
    print(f"MMW_TEST_JOBS must be a positive integer, got {raw_jobs!r}; set it before running {script}", file=sys.stderr)
    sys.exit(2)


def run(name):
    result = subprocess.run(["bash", script, name], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return name, result.returncode, result.stdout


failed = []


def report(result):
    name, code, output = result
    if code:
        failed.append(result)
    else:
        sys.stdout.buffer.write(output)
        sys.stdout.buffer.flush()


with concurrent.futures.ThreadPoolExecutor(max_workers=int(raw_jobs)) as pool:
    for future in concurrent.futures.as_completed(pool.submit(run, name) for name in parallel):
        report(future.result())
for name in serial:
    report(run(name))
for name, code, output in failed:
    print(f"FAIL {name} (exit {code})", flush=True)
    sys.stdout.buffer.write(output)
    sys.stdout.buffer.flush()
sys.exit(1 if failed else 0)
PY
}
