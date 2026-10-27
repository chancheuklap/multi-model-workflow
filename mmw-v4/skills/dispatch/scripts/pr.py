#!/usr/bin/env python3
"""Open a ready pull request and wait for its checks through the GitHub CLI.

Interface: pr.py --base <branch> --head <branch> --title <title> --body-file <path>.
Run from the repository whose .github/workflows files describe CI coverage.
MMW_PR_CHECKS_GRACE_SECONDS overrides the 120-second check and workflow-run grace.
Only the Python standard library is required.

Stdout includes the PR URL and a final checks: green, checks: red <names>, or
checks: none line. With no CI for the base, NOTE: GitHub CI does not run for pull
requests into <base> precedes dispatched <workflow>: <conclusion> or
skipped <workflow>: <reason> lines. Unreadable workflow triggers print their path
and assume CI runs. A failed dispatch prints dispatched <workflow>: failed (<reason>).

Exit 0 means checks passed or no checks were expected, with fallback runs passing.
Exit 1 means red checks, failed fallback runs, or expected checks missing after grace.
Exit 2 means invalid arguments or an operational error, with a reason on stderr.
"""

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def split_yaml(value, separator):
    parts, start, depth, quote = [], 0, 0, None
    offset = 0
    while offset < len(value):
        char = value[offset]
        if quote:
            if char == "\\" and quote == '"':
                offset += 2
                continue
            if char == quote:
                if quote == "'" and value[offset:offset + 2] == "''":
                    offset += 2
                    continue
                quote = None
        elif char in "\"'":
            quote = char
        elif char == separator and depth == 0:
            if separator == "#":
                if offset == 0 or value[offset - 1].isspace():
                    return [value[:offset].rstrip()]
                offset += 1
                continue
            parts.append(value[start:offset].strip())
            start = offset + 1
        elif char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
        if depth < 0:
            raise ValueError("unbalanced flow collection")
        offset += 1
    if quote or depth:
        raise ValueError("unclosed quote or flow collection")
    return parts + [value[start:].strip()]


def yaml_value(value):
    value = value.strip()
    if not value or value in ("null", "~"):
        return None
    if value.startswith('"'):
        return json.loads(value)
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value.startswith("[") and value.endswith("]"):
        return [yaml_value(part) for part in split_yaml(value[1:-1], ",") if part]
    if value.startswith("{") and value.endswith("}"):
        return dict(yaml_pair(part) for part in split_yaml(value[1:-1], ",") if part)
    if value[0] in "*&!|>{[\"'" or any(char in value for char in "{}[]"):
        raise ValueError("unsupported YAML value")
    return value


def yaml_pair(value):
    parts = split_yaml(value, ":")
    if len(parts) != 2:
        raise ValueError("expected a YAML mapping entry")
    key = yaml_value(parts[0])
    if not isinstance(key, str):
        raise ValueError("expected a string key")
    return key, yaml_value(parts[1])


def yaml_block(lines):
    if not lines:
        return None
    indent = lines[0][0]
    sequence = lines[0][1].startswith("- ")
    result = [] if sequence else {}
    offset = 0
    while offset < len(lines):
        level, text = lines[offset]
        if level != indent:
            raise ValueError("unexpected YAML indentation")
        if sequence:
            if not text.startswith("- "):
                raise ValueError("expected a sequence entry")
            result.append(yaml_value(text[2:]))
            offset += 1
            continue
        key, value = yaml_pair(text)
        if key in result:
            raise ValueError("duplicate YAML key")
        end = offset + 1
        while end < len(lines) and (lines[end][0] > indent or (
            value is None and lines[end][0] == indent and lines[end][1].startswith("- ")
        )):
            end += 1
        if end > offset + 1:
            if value is not None:
                raise ValueError("inline value also has a nested block")
            value = yaml_block(lines[offset + 1:end])
        result[key] = value
        offset = end
    return result


def branch_matches(base, pattern):
    expression = []
    for token in re.findall(r"\\.|\*\*|\*|\[[A-Za-z0-9-]+\]|.", pattern):
        if token == "**":
            expression.append(".*")
        elif token == "*":
            expression.append("[^/]*")
        elif token in ("?", "+") or token.startswith("[") and token.endswith("]"):
            expression.append(token)
        elif token.startswith("\\"):
            expression.append(re.escape(token[1:]))
        elif token in ("[", "]"):
            raise ValueError("unsupported branch character class")
        else:
            expression.append(re.escape(token))
    return re.fullmatch("".join(expression), base) is not None


@dataclass
class Workflow:
    path: Path
    events: dict | None

    def covers(self, base):
        if self.events is None:
            return True
        if "pull_request" not in self.events:
            return False
        config = self.events["pull_request"] or {}
        if not isinstance(config, dict):
            raise ValueError("pull_request must be a mapping")
        branches = config.get("branches") or []
        ignored = config.get("branches-ignore") or []
        if not isinstance(branches, list) or not isinstance(ignored, list):
            raise ValueError("branch filters must be lists")
        allowed = not branches
        for pattern in branches:
            if branch_matches(base, pattern.removeprefix("!")):
                allowed = not pattern.startswith("!")
        return allowed and not any(branch_matches(base, pattern) for pattern in ignored)

    def skip_reason(self):
        if "pull_request" not in self.events:
            return "no pull_request trigger"
        config = self.events["workflow_dispatch"] or {}
        if not isinstance(config, dict) or not isinstance(config.get("inputs", {}), dict):
            return "could not read workflow_dispatch inputs"
        for name, settings in config.get("inputs", {}).items():
            if not isinstance(settings, dict):
                return f"could not read input {name}"
            required = str(settings.get("required", "false")).lower()
            if required not in ("false", "true"):
                return f"could not read required flag for input {name}"
            if required == "true":
                return f"required input {name}"
        return None


def read_workflow_triggers(path, base):
    try:
        lines = []
        for raw in path.read_text().splitlines():
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            if re.match(r'''^(?:on|'on'|"on")\s*:''', raw):
                if lines:
                    raise ValueError("duplicate on key")
                lines.append((0, split_yaml(raw.strip(), "#")[0]))
            elif lines and (raw.startswith(" ") or raw.startswith("- ")):
                text = split_yaml(raw.strip(), "#")[0]
                lines.append((len(raw) - len(raw.lstrip(" ")), text))
            elif lines:
                break
        if not lines:
            raise ValueError("no supported on declaration")
        events = yaml_block(lines)["on"]
        if isinstance(events, str):
            events = {events: None}
        elif isinstance(events, list) and all(isinstance(event, str) for event in events):
            events = dict.fromkeys(events)
        if not isinstance(events, dict):
            raise ValueError("on must name events")
        workflow = Workflow(path, events)
        workflow.covers(base)
        return workflow
    except (OSError, ValueError, TypeError, AttributeError, re.error) as error:
        print(f"workflow {path}: could not read triggers ({error}); assuming CI runs", flush=True)
        return Workflow(path, None)


def gh(*args):
    env = {key: value for key, value in os.environ.items() if key not in ("CLICOLOR_FORCE", "CLICOLOR")}
    return subprocess.run(["gh", *args], capture_output=True, text=True,
                          stdin=subprocess.DEVNULL, env=env)


def require(result, operation):
    if result.returncode:
        raise ValueError(f"{operation} failed: {(result.stderr or result.stdout).strip()}")
    return result.stdout.strip()


def dispatch_workflow(workflow, head, grace):
    filename = workflow.path.name
    try:
        def runs():
            result = gh("run", "list", "--workflow", filename, "--branch", head,
                        "--event", "workflow_dispatch", "--json", "databaseId")
            return {str(row["databaseId"]) for row in json.loads(require(result, "listing workflow runs"))}

        previous = runs()
        output = require(gh("workflow", "run", filename, "--ref", head), f"dispatching {filename}")
        match = re.search(r"/actions/runs/(\d+)\b", output)
        run = match[1] if match else None
        deadline = time.monotonic() + grace
        while run is None:
            fresh = runs() - previous
            if len(fresh) == 1:
                run = fresh.pop()
            elif len(fresh) > 1:
                raise ValueError("several new runs appeared; cannot identify the dispatched run")
            elif time.monotonic() >= deadline:
                raise ValueError("no new workflow run appeared before the grace period ended")
            else:
                time.sleep(min(2, max(0, deadline - time.monotonic())))
        watched = gh("run", "watch", run, "--exit-status")
        conclusion = require(gh("run", "view", run, "--json", "conclusion", "--jq", ".conclusion"),
                             f"reading workflow run {run}")
        if not conclusion:
            raise ValueError(f"workflow run {run} returned no conclusion")
        print(f"dispatched {filename}: {conclusion}", flush=True)
        if watched.returncode and (watched.stderr.strip() or conclusion in ("success", "neutral", "skipped")):
            detail = (watched.stderr or watched.stdout).strip() or f"exit {watched.returncode}"
            print(f"dispatch: watching workflow run {run} failed: {detail}", file=sys.stderr)
        return watched.returncode == 0 and conclusion in ("success", "neutral", "skipped")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"dispatched {filename}: failed ({error})", flush=True)
        return False


def main():
    parser = argparse.ArgumentParser(prog="dispatch.sh pr")
    for flag in ("base", "head", "title", "body-file"):
        parser.add_argument("--" + flag, required=True)
    args = parser.parse_args()
    if not all((args.base, args.head, args.title)) or not Path(args.body_file).is_file():
        raise ValueError("base, head and title must be nonempty and --body-file must name a file")
    grace = float(os.environ.get("MMW_PR_CHECKS_GRACE_SECONDS", "120"))
    if not 0 <= grace < float("inf"):
        raise ValueError("MMW_PR_CHECKS_GRACE_SECONDS must be a finite nonnegative number")
    root = Path(require(subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                      capture_output=True, text=True), "finding repository"))
    directory = root / ".github/workflows"
    workflows = [read_workflow_triggers(path, args.base) for path in sorted(directory.glob("*"))
                 if path.suffix in (".yml", ".yaml")]
    has_ci = any(workflow.covers(args.base) for workflow in workflows)
    existing = json.loads(require(gh("pr", "list", "--base", args.base, "--head", args.head,
                                     "--state", "open", "--json", "url"), "finding existing pull requests"))
    if not isinstance(existing, list):
        raise ValueError("gh pr list returned an unreadable pull request list")
    if existing:
        raise ValueError(f"pull request already exists at {existing[0]['url']}; no workflows were dispatched; "
                         "read its checks with gh pr checks <url> --watch instead of opening it again")
    fallback_ok = True
    if not has_ci:
        print(f"NOTE: GitHub CI does not run for pull requests into {args.base}", flush=True)
        for workflow in workflows:
            if "workflow_dispatch" not in workflow.events:
                continue
            reason = workflow.skip_reason()
            if reason:
                print(f"skipped {workflow.path.name}: {reason}", flush=True)
            else:
                fallback_ok = dispatch_workflow(workflow, args.head, grace) and fallback_ok
    link = require(gh("pr", "create", "--base", args.base, "--head", args.head,
                      "--title", args.title, "--body-file", args.body_file), "opening pull request")
    match = re.search(r"https://\S+/pull/(\d+)\b", link)
    if not match:
        raise ValueError(f"gh pr create returned no pull request link: {link}")
    print(match[0], flush=True)
    number = match[1]
    deadline = time.monotonic() + grace
    while True:
        watched = gh("pr", "checks", number, "--watch")
        if watched.returncode and (
            watched.returncode != 1 or (watched.stderr.strip() and "no checks reported" not in watched.stderr)
        ):
            raise ValueError(f"watching pull request #{number} failed: {watched.stderr.strip()}")
        checks = gh("pr", "checks", number, "--json", "name,bucket")
        if checks.returncode == 1 and "no checks reported" in checks.stderr:
            rows = []
        else:
            rows = json.loads(require(checks, f"reading pull request #{number} checks"))
        if not isinstance(rows, list) or any(not isinstance(row, dict) or
            row.get("bucket") not in ("pass", "skipping", "fail", "cancel", "pending") or
            not isinstance(row.get("name"), str) for row in rows):
            raise ValueError(f"pull request #{number} returned unreadable checks")
        if any(row["bucket"] == "pending" for row in rows):
            continue
        if rows:
            red = [row["name"] for row in rows if row["bucket"] in ("fail", "cancel")]
            print("checks: red " + ", ".join(red) if red else "checks: green", flush=True)
            return int(bool(red) or not fallback_ok)
        if not has_ci or time.monotonic() >= deadline:
            print("checks: none", flush=True)
            if has_ci:
                print(f"dispatch: expected CI for {args.base}, but no checks appeared within {grace:g} seconds",
                      file=sys.stderr)
            return int(has_ci or not fallback_ok)
        time.sleep(min(2, max(0, deadline - time.monotonic())))


try:
    sys.exit(main())
except (OSError, ValueError, KeyError, TypeError) as error:
    print(f"dispatch: pr: {error}", file=sys.stderr)
    sys.exit(2)
