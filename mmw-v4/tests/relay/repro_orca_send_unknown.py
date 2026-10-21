"""Reproduce #1211: the Orca runner's `send` must not invite a fresh resend of a wake
Orca could not confirm.

    python3 mmw-v4/tests/relay/repro_orca_send_unknown.py

Drives runners/orca.sh `send` against a fake `orca` whose `terminal send` answers with
the envelopes Orca 1.4.235 prints (shape read off a real `orca terminal send --json`
refusal on 1.4.232: `ok`, `error.code`, `error.message`, `error.data`; messages and data
copied from Orca v1.4.235 src/cli/runtime/terminal-prompt-mutation-recovery.ts). Exit 3
tells the relay nothing was typed and a fresh send is safe; exit 4 tells it the text may
be in the terminal and must not be typed again.

Every `terminal send` must carry `--retry-request <uuid>`. On Orca 1.4.232, two sends
with one caller-chosen request id typed the text once (measured 2026-10-21 on a plain
`cat` terminal), so a replay under the same id can learn what became of the first send
without typing it twice. Prints one line per case and `REPRO GREEN` when every case gets
the exit and the calls it should, else `REPRO RED` and exits 1.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

ADAPTER = Path(__file__).resolve().parents[2] / "skills/dispatch/scripts/runners/orca.sh"
SESSION = "term_recipient"

FAKE_ORCA = r'''
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with Path(os.environ["FAKE_ORCA_LOG"]).open("a") as log:
    log.write(json.dumps(args) + "\n")
if args[:2] == ["terminal", "list"]:
    print(json.dumps({"result": {"terminals": [{"handle": "term_recipient",
        "connected": True, "writable": True, "agentIdentity": "codex"}]}}))
elif args[:2] == ["terminal", "show"]:
    print(json.dumps({"result": {"terminal": {"handle": "term_recipient",
        "agentIdentity": "codex"}}}))
elif args[:2] == ["terminal", "wait"]:
    print(json.dumps({"result": {"wait": {"satisfied": True, "status": "running"}}}))
elif args[:2] == ["terminal", "send"]:
    answers = json.loads(os.environ["FAKE_ORCA_SENDS"])
    count = Path(os.environ["FAKE_ORCA_COUNT"])
    n = int(count.read_text()) if count.exists() else 0
    count.write_text(str(n + 1))
    answer = answers[min(n, len(answers) - 1)]
    print(json.dumps(answer, indent=2))
    sys.exit(0 if answer.get("ok", True) else 1)
else:
    sys.exit(99)
'''


def error(code, message, data):
    return {"id": "x", "ok": False, "error": {"code": code, "message": message, "data": data},
            "_meta": {"runtimeId": "r"}}


def receipt(stages):
    return {"id": "x", "result": {"send": {"accepted": True, "prompt": {
        "requestId": "from-orca", "stages": stages, "observation": "supported"}}}}


UNKNOWN = error("runtime_error",
                "socket closed The legacy host cannot prove whether the prompt was delivered; "
                "inspect the terminal before deciding what to do, and do not resend automatically.",
                {"deliveryOutcome": "unknown", "retrySafe": False,
                 "nextSteps": ["Inspect the terminal output and agent state without sending input."]})
DURABLE = error("runtime_unavailable",
                "runtime_unavailable Terminal prompt request ID: {id}. Re-issue the exact command "
                "with --retry-request {id} --wait-submit <seconds>; do not retry it without that ID.",
                {"orchestrationRequestId": "{id}"})
REFUSED = error("invalid_argument", "invalid_argument", {})

# name, answers to successive `terminal send` calls, wanted exit, wanted number of sends
CASES = [
    ("delivery unknown, retrySafe false", [UNKNOWN], 4, 1),
    ("failed after a durable request id, replay finds the turn started",
     [DURABLE, receipt(["input_accepted", "turn_started"])], 0, 2),
    ("failed after a durable request id, replay finds it handed over",
     [DURABLE, receipt(["input_accepted"])], 4, 2),
    ("refused before any input, control", [REFUSED], 3, 1),
]


def run(answers):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        fake = root / "orca"
        fake.write_text(f"#!{sys.executable}\n" + FAKE_ORCA)
        fake.chmod(0o755)
        log = root / "calls.jsonl"
        env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"],
                   MMW_HOME=str(root / "mmw-home"), FAKE_ORCA_LOG=str(log),
                   FAKE_ORCA_COUNT=str(root / "count"), FAKE_ORCA_SENDS=json.dumps(answers))
        result = subprocess.run(["bash", str(ADAPTER), "send", SESSION, "#1211 ticket.passed"],
                                env=env, capture_output=True, text=True, timeout=60)
        calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
        return result, [c for c in calls if c[:2] == ["terminal", "send"]]


def request_ids(sends):
    ids = []
    for call in sends:
        value = call[call.index("--retry-request") + 1] if "--retry-request" in call else None
        try:
            ids.append(str(uuid.UUID(value)) if value else None)
        except ValueError:
            ids.append(None)
    return ids


red = False
for name, answers, want_exit, want_sends in CASES:
    result, sends = run(answers)
    ids = request_ids(sends)
    problems = []
    if result.returncode != want_exit:
        problems.append(f"exit {result.returncode}, want {want_exit}")
    if len(sends) != want_sends:
        problems.append(f"{len(sends)} terminal send calls, want {want_sends}")
    if not ids or None in ids:
        problems.append("a terminal send without a --retry-request uuid")
    elif len(set(ids)) != 1:
        problems.append(f"the replay used another request id: {ids}")
    red |= bool(problems)
    print(f"{'BAD' if problems else 'ok '} {name}: {'; '.join(problems) or 'as it should'}; "
          f"stderr: {' '.join(result.stderr.split())}")
print("REPRO RED" if red else "REPRO GREEN")
sys.exit(1 if red else 0)
