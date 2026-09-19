#!/usr/bin/env python3
"""Inventory one completed spec, search older retro, and finalize its one receipt.

Usage: retro.py gather <spec> | search <category> <cause> | finalize <spec> <analysis.json>
The model owns analysis; this entry validates primary sources and writes proposals,
one fixed-id Memory and the script-authored spec.retroed event, in that order.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

MMW = Path(__file__).resolve().parents[3]
REPO = Path.cwd().resolve()
REPOSITORY_OVERRIDE = ""
SPACE_CACHE = ""
VERIFY = MMW / "skills" / "verify-ticket" / "scripts"
UI_ACCEPTANCE = MMW / "skills" / "ui-acceptance" / "scripts"
CATEGORIES = ("Navigation", "Automated checks", "Coding standards",
              "Global AGENTS.md", "Tool economy", "No-ops", "Information access")
DESTINATIONS = ("check", "script", "repository-agents", "repository-skill",
                "reviewer-rule", "mmw-skill", "toolbox-memory", "none")
SHA = re.compile(r"^[0-9a-f]{40}$")
GH_ENV = {k: v for k, v in os.environ.items() if k not in ("CLICOLOR", "CLICOLOR_FORCE")}


def load(name: str, directory: Path = VERIFY):
    path = directory / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"retro_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


tree = load("tree")
events = load("events")
refusal = load("refusal", UI_ACCEPTANCE)


class RetroError(RuntimeError):
    pass


def git_root(path: Path) -> Path:
    try:
        proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=path,
                              text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, check=False)
    except OSError as exc:
        raise RetroError(f"git rev-parse --show-toplevel: {exc}") from exc
    if proc.returncode or not proc.stdout.strip():
        detail = (proc.stderr or proc.stdout).strip()[:500]
        raise RetroError(f"{path} is not inside a Git checkout: {detail}")
    return Path(proc.stdout.strip()).resolve()


def command(args: list[str], *, stdin: str | None = None, cwd: Path | None = None,
            env: dict | None = None) -> str:
    try:
        proc = subprocess.run(args, input=stdin, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, cwd=cwd or REPO, env=env)
    except OSError as exc:
        raise RetroError(f"{' '.join(args)}: {exc}") from exc
    if proc.returncode:
        raise RetroError(f"{' '.join(args)} exited {proc.returncode}: "
                         f"{(proc.stderr or proc.stdout).strip()[:500]}")
    return proc.stdout.strip()


def gh(*args: str, stdin: str | None = None) -> str:
    return command(["gh", *args], stdin=stdin, env=GH_ENV)


def parsed(args: list[str], *, env: dict | None = None) -> dict:
    output = command(args, env=env)
    try:
        value = json.loads(output)
    except ValueError as exc:
        raise RetroError(f"{' '.join(args)} returned unreadable JSON") from exc
    if not isinstance(value, dict):
        raise RetroError(f"{' '.join(args)} returned no JSON object")
    return value


def issue(number: int, fields: str = "body,title,comments,parent") -> dict:
    return parsed(["gh", "issue", "view", str(number), "--json", fields], env=GH_ENV)


def space() -> str:
    global SPACE_CACHE
    if SPACE_CACHE:
        return SPACE_CACHE
    expected = repository().lower().replace("/", "__")
    value = os.environ.get("NMEM_SPACE") or expected
    if value != expected or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", value):
        raise RetroError(f"NMEM_SPACE {value!r} differs from repository Space {expected}")
    row = parsed(["nmem", "--json", "spaces", "show", value])
    if (row.get("id") != value or row.get("defaultRetrievalMode") != "shared" or
            row.get("sharedSpaceIds") != ["mmw-toolbox"]):
        raise RetroError(f"repository Space {value} did not read back as shared with mmw-toolbox only")
    SPACE_CACHE = value
    return value


def repository() -> str:
    if REPOSITORY_OVERRIDE:
        return REPOSITORY_OVERRIDE
    origin = command(["git", "remote", "get-url", "origin"])
    match = re.search(r"(?:[:/])([^/:]+/[^/]+?)(?:\.git)?$", origin)
    if not match:
        raise RetroError(f"origin does not name an owner/repository: {origin}")
    return match.group(1)


def issue_url(number: int) -> str:
    return f"https://github.com/{repository()}/issues/{number}"


def inventory(source: str, status: str, detail: str = "") -> dict:
    return {"source": source, "status": status, "detail": detail}


def section(body: str, title: str) -> str | None:
    lines = body.splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == f"## {title}"), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
               len(lines))
    return "\n".join(lines[start:end]).strip()


def memory_list(limit: int = 2) -> dict:
    result = parsed(["nmem", "--json", "memories", "list", "--label", "mmw-retro",
                     "--space", space(), "--limit", str(limit)])
    rows = result.get("memories")
    if not isinstance(rows, list) or not isinstance(result.get("total", len(rows)), int):
        raise RetroError("mmw-retro list has no readable memories and total")
    # This is the intentionally bounded *latest* read, not a claim that history
    # was exhaustively listed. A specific older record is discovered by search.
    if len(rows) > limit:
        raise RetroError("mmw-retro latest list ignored its requested limit")
    return result


def memory_show(ident: str) -> dict:
    row = parsed(["nmem", "--json", "memories", "show", ident, "--space", space()])
    if row.get("id") != ident or not isinstance(row.get("content"), str):
        raise RetroError(f"Memory {ident} did not return its complete content")
    return row


def nodes(root: dict):
    for child in root.get("children", []):
        yield child
        yield from nodes(child)


def valid_closing(value: object) -> bool:
    if not isinstance(value, dict) or not isinstance(value.get("decisions"), list):
        return False
    if value.get("status") == "unchecked":
        return (bool(value.get("reason")) and value["decisions"] == [] and
                all(value.get(key) is None or isinstance(value[key], int)
                    for key in ("total", "returned")))
    if value.get("status") != "complete":
        return False
    decisions = value["decisions"]
    if (not isinstance(value.get("total"), int) or
            value["total"] != value.get("returned") or value["total"] != len(decisions)):
        return False
    ids = []
    for item in decisions:
        if not isinstance(item, dict) or not all(
                isinstance(item.get(key), str) and item[key].strip()
                for key in ("memory_id", "decision", "reason", "evidence")):
            return False
        if item["decision"] not in ("retain", "propose", "deprecate", "supersede"):
            return False
        if item["decision"] == "supersede" and not item.get("replacement_id"):
            return False
        ids.append(item["memory_id"])
    return len(ids) == len(set(ids))


def gather(number: int) -> dict:
    checked: list[dict] = []
    spec_url = issue_url(number)
    try:
        current = issue(number)
        checked.append(inventory(spec_url, "present", "spec body and comments"))
    except RetroError as exc:
        raise RetroError(f"cannot verify completed spec #{number}: {exc}") from exc
    body = current.get("body")
    if not isinstance(body, str):
        raise RetroError(f"{spec_url} has unreadable body")
    intent = {}
    for heading in ("Problem Statement", "User Stories", "Out of Scope"):
        value = section(body, heading)
        intent[heading] = value
        checked.append(inventory(f"{spec_url} ## {heading}",
                                 "present" if value else "missing", "spec section"))
    comments = current.get("comments")
    if not isinstance(comments, list):
        raise RetroError(f"{spec_url} has no readable comments list")
    state = events.fold(comments, issue=number)
    for item in comments:
        if events.parse(item.get("body") or "")[0] == "event":
            checked.append(inventory(item.get("url") or f"{spec_url} comment {item.get('id')}",
                                     "present", "script-written event comment"))
    if state["unreadable"]:
        checked.extend(inventory(f"{spec_url} comment {row['comment']}", "unreadable",
                                 row["reason"]) for row in state["unreadable"])
    opened = events.newest(comments, "spec.opened")
    closed = events.newest(comments, "spec.closed")
    if not closed:
        raise RetroError(f"{spec_url} has no spec.closed; retro runs after summary")
    checked.append(inventory(f"{spec_url} spec.closed", "present", "event comment"))
    if not opened:
        checked.append(inventory(f"{spec_url} spec.opened", "missing", "base unknown"))
    parent = current.get("parent")
    if parent is None:
        task_root = {"kind": "standalone-spec", "number": number}
    elif isinstance(parent, dict) and isinstance(parent.get("number"), int):
        parent_issue = issue(parent["number"], "labels")
        labels = [x.get("name") for x in parent_issue.get("labels", []) if isinstance(x, dict)]
        if "mmw:map" not in labels:
            raise RetroError(f"#{number} has parent #{parent['number']} without mmw:map")
        task_root = {"kind": "map", "number": parent["number"]}
    else:
        raise RetroError(f"#{number} parent was unreadable")
    try:
        native = tree.read(number, "spec")
        checked.append(inventory(f"{spec_url} native ticket tree", "present",
                                 f"{native.get('total', 0)} direct tickets"))
    except tree.TreeUnreadable as exc:
        native = {"number": number, "children": []}
        checked.append(inventory(f"{spec_url} native ticket tree", "unreadable", str(exc)))
    tickets = []
    for node in nodes(native):
        target = issue_url(node["number"])
        try:
            row = issue(node["number"], "body,title,comments")
            if not isinstance(row.get("comments"), list):
                raise RetroError("comments is not a list")
            fold = events.fold(row["comments"], issue=node["number"])
            checked.append(inventory(target, "present", "event-bearing comments and fold"))
            for comment in row["comments"]:
                if events.parse(comment.get("body") or "")[0] == "event":
                    checked.append(inventory(comment.get("url") or
                                             f"{target} comment {comment.get('id')}",
                                             "present", "script-written event comment"))
            for unreadable in fold["unreadable"]:
                checked.append(inventory(f"{target} comment {unreadable['comment']}",
                                         "unreadable", unreadable["reason"]))
            tickets.append({"number": node["number"], "title": row.get("title"),
                            "events": fold["events"],
                            "comments": [{"url": c.get("url"), "body": c.get("body")}
                                         for c in row["comments"] if "<!-- mmw " in str(c.get("body"))]})
        except RetroError as exc:
            checked.append(inventory(target, "unreadable", str(exc)))
    closing = (closed.get("payload") or {}).get("memory_closing")
    proposed = []
    if valid_closing(closing):
        proposed = [item["memory_id"] for item in closing.get("decisions", [])
                    if isinstance(item, dict) and item.get("decision") == "propose"
                    and isinstance(item.get("memory_id"), str)]
        checked.append(inventory(f"{spec_url} spec.closed.payload.memory_closing", "present",
                                 closing["status"]))
    else:
        checked.append(inventory(f"{spec_url} spec.closed.payload.memory_closing",
                                 "unreadable", "not the #429 complete or unchecked object"))
    base = (opened or {}).get("payload", {}).get("base", "")
    into = (opened or {}).get("payload", {}).get("into", "")
    project = (opened or {}).get("payload", {}).get("project", "")
    # spec.opened records the project and base branches, not a base SHA. The
    # common ancestor is the branch point until finish merges the two branches.
    if not base and into and project:
        try:
            base = command(["git", "merge-base", f"origin/{project}", f"origin/{into}"])
        except RetroError:
            pass
    result = ""
    commits = []
    source_range = f"{base or '?'}..origin/{into or '?'}"
    if SHA.fullmatch(base) and isinstance(into, str) and into:
        try:
            result = command(["git", "rev-parse", f"origin/{into}"])
            command(["git", "merge-base", "--is-ancestor", base, result])
            log = command(["git", "log", "--format=%H %s", f"{base}..{result}"])
            commits = [{"sha": line.split(" ", 1)[0], "subject": line.split(" ", 1)[1]}
                       for line in log.splitlines() if " " in line]
            checked.append(inventory(source_range, "present", f"{len(commits)} commits"))
        except RetroError as exc:
            checked.append(inventory(source_range, "unreadable", str(exc)))
    else:
        checked.append(inventory(source_range, "unreadable", "no readable spec.opened base/into"))
    earlier = []
    try:
        rows = memory_list()["memories"]
        own_id = f"mmw-retro-{space()}-spec-{number}"
        first = next((row for row in rows if isinstance(row, dict)
                      and isinstance(row.get("id"), str) and row["id"] != own_id), None)
        earlier = [memory_show(first["id"])] if first else []
        checked.append(inventory(f"{space()} mmw-retro latest", "present",
                                 earlier[0]["id"] if earlier else "none checked"))
    except RetroError as exc:
        checked.append(inventory(f"{space()} mmw-retro latest", "unreadable", str(exc)))
    return {"spec": number, "spec_url": spec_url, "title": current.get("title", ""),
            "task_root": task_root, "intent": intent, "tree": native, "tickets": tickets,
            "spec_events": state["events"], "spec_comments": comments,
            "memory_closing": closing, "proposed_memory_ids": proposed,
            "commits": commits, "prior_retro": earlier[0] if earlier else None,
            "evidence_checked": checked, "observed": {"at": datetime.now(timezone.utc).isoformat(),
                                                        "base_commit": base}, "result_commit": result}


def search(category: str, cause: str) -> dict:
    if category not in CATEGORIES or not cause.strip():
        raise RetroError("search needs one of the seven categories and a specific cause")
    response = parsed(["nmem", "--json", "memories", "search", f"{category} {cause}",
                       "--label", "mmw-retro", "--space", space(), "--limit", "10"])
    rows = response.get("memories")
    if not isinstance(rows, list):
        raise RetroError("retro search returned no memories list")
    return {"category": category, "cause": cause,
            "matches": [memory_show(row["id"]) for row in rows
                        if isinstance(row, dict) and isinstance(row.get("id"), str)]}


def observed_check(source: str) -> str:
    """Reopen one read-only observed check without interpreting shell syntax."""
    try:
        args = shlex.split(source.removeprefix("check:").strip())
    except ValueError as exc:
        raise RetroError(f"observed check {source!r} has unreadable arguments") from exc
    if not args:
        raise RetroError("observed check has no command")
    if args[0] == "rg" and not any(arg.startswith("--pre") for arg in args[1:]):
        args.insert(1, "--no-config")
    elif (args[:2] in (["git", "diff"], ["git", "show"], ["git", "log"],
                       ["git", "status"], ["git", "grep"], ["git", "rev-parse"],
                       ["git", "cat-file"])):
        if any(arg in ("--output", "-o", "--ext-diff", "--textconv") or
               arg.startswith(("--output=", "--pre=", "--ext-diff="))
               for arg in args[2:]):
            raise RetroError(f"observed check {source!r} contains a writing or external-diff option")
    else:
        raise RetroError(f"observed check {source!r} is not a read-only rg/git command")
    try:
        run = subprocess.run(args, cwd=REPO, text=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    except OSError as exc:
        raise RetroError(f"observed check {source!r} could not run: {exc}") from exc
    output = (run.stdout + "\n" + run.stderr).strip()
    if not output:
        raise RetroError(f"observed check {source!r} returned no primary output")
    return f"exit={run.returncode}\n{output}"


def evidence_source(source: str) -> tuple[str, str]:
    """Return reopened primary text for an event, commit, current file or check."""
    if not isinstance(source, str) or not source.strip():
        raise RetroError(f"primary evidence source is empty: {source!r}")
    if source.startswith("check:"):
        return "check", observed_check(source)
    if not source.startswith("https://"):
        target = (REPO / source).resolve()
        if not target.is_relative_to(REPO.resolve()) or not target.is_file():
            raise RetroError(f"current repository file {source!r} cannot be read inside {REPO}")
        try:
            return "file", target.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise RetroError(f"current repository file {source!r} is unreadable: {exc}") from exc
    if not source.startswith("https://github.com/"):
        raise RetroError(f"primary event or commit URL is not GitHub: {source!r}")
    parsed_url = urlparse(source)
    match = re.fullmatch(r"/([^/]+)/([^/]+)/(issues|commit)/(\d+|[0-9a-f]{40})", parsed_url.path)
    if not match:
        raise RetroError(f"not an issue event or commit source: {source}")
    owner, name, kind, ident = match.groups()
    if kind == "commit":
        sha = ident
        return "commit", command(["git", "show", "-s", "--format=%B", sha])
    if not parsed_url.fragment.startswith("issuecomment-"):
        raise RetroError(f"an issue status without an event comment is not evidence: {source}")
    comment_id = parsed_url.fragment.split("issuecomment-", 1)[1]
    row = parsed(["gh", "api", f"repos/{owner}/{name}/issues/comments/{comment_id}"], env=GH_ENV)
    body = row.get("body")
    if not isinstance(body, str):
        raise RetroError(f"{source} has no readable primary comment")
    what, value = events.parse(body)
    if what != "event" or not isinstance(value, dict):
        raise RetroError(f"{source} is not a script-written event comment")
    if value.get("ticket") not in (None, int(ident)) and value.get("spec") != int(ident):
        raise RetroError(f"{source} event identifies a different ticket or spec")
    return "event", body


def occurrence(url: str) -> str:
    """One issue's event or one commit; repeat comments on one issue are one occurrence."""
    path = urlparse(url).path
    return ("commit:" if "/commit/" in path else "issue:") + path.rsplit("/", 1)[-1]


def check_analysis(number: int, data: dict, gathered: dict) -> None:
    required = ("spec", "task_root", "evidence_checked", "previous_proposals",
                "categories", "problems", "intent_reconciliation", "review_learning", "observed")
    if any(key not in data for key in required) or data["spec"] != number:
        raise RetroError("analysis lacks a required field or names a different spec")
    if data["task_root"] != gathered["task_root"]:
        raise RetroError("task_root differs from the native parent")
    if data["evidence_checked"] != gathered["evidence_checked"]:
        raise RetroError("evidence_checked must carry gather's entire unchanged inventory")
    if not isinstance(data["observed"], dict):
        raise RetroError("observed must contain base_commit and at")
    if data["observed"].get("base_commit") != gathered["observed"]["base_commit"] or not data["observed"].get("at"):
        raise RetroError("observed needs gather's base commit and a retro time")
    if not isinstance(data["categories"], dict) or set(data["categories"]) != set(CATEGORIES):
        raise RetroError("all seven categories need an explicit result")
    if any(not isinstance(value, str) or not value.strip() for value in data["categories"].values()):
        raise RetroError("a category result is empty")
    for name in ("evidence_checked", "previous_proposals", "problems"):
        if not isinstance(data[name], list):
            raise RetroError(f"{name} must be a list")
        if any(not isinstance(row, dict) for row in data[name]):
            raise RetroError(f"{name} has a non-object entry")
    for row in data["previous_proposals"]:
        if row.get("status") not in ("landed", "no-evidence-found") or not row.get("url"):
            raise RetroError("previous proposals need a URL and landed/no-evidence-found")
        prior = gathered.get("prior_retro") or {}
        if row["url"] not in prior.get("content", ""):
            raise RetroError("previous proposal is not cited by the latest earlier Retro Memory")
        if row["status"] == "landed" and row.get("evidence") in (None, "none", ""):
            raise RetroError("landed proposal needs commit, active Rule, Memory or current file evidence")
        if row["status"] == "landed":
            proof = row["evidence"]
            if SHA.fullmatch(proof):
                command(["git", "cat-file", "-e", proof])
            elif proof.startswith("nowledgemem://memory/"):
                memory_show(proof.rsplit("/", 1)[-1])
            elif proof.startswith("Rule: "):
                rule_id = proof.split("Rule: ", 1)[1]
                active = parsed(["nmem", "--json", "rules", "show", rule_id])
                if active.get("id") != rule_id or active.get("status") != "active":
                    raise RetroError("previous proposal Rule is not active")
            elif not (REPO / proof).resolve().is_relative_to(REPO.resolve()) or not (REPO / proof).is_file():
                raise RetroError("previous proposal lacks a checked current file, commit or Memory")
    intent = data["intent_reconciliation"]
    if not isinstance(intent, dict) or intent.get("gap") not in ("aligned", "diverged", "unverified"):
        raise RetroError("intent reconciliation needs expected, observed and valid gap")
    if not all(isinstance(intent.get(key), str) and intent[key] for key in ("expected", "observed")):
        raise RetroError("intent reconciliation has no expected or observed surface")
    if not isinstance(data["review_learning"], str) or not data["review_learning"]:
        raise RetroError("review learning must report evidence or none")
    if any(row.get("status") not in ("present", "missing", "unreadable") or
           not row.get("source") for row in data["evidence_checked"]):
        raise RetroError("evidence inventory has an unknown status or source")
    for problem in data["problems"]:
        if problem.get("category") not in CATEGORIES or not isinstance(problem.get("cause"), str) or not problem["cause"]:
            raise RetroError("problem needs one of seven categories and a cause")
        if data["categories"][problem["category"]].strip().lower() == "none":
            raise RetroError("a supported problem cannot have a none category result")
        if (not isinstance(problem.get("evidence"), list) or not problem["evidence"] or
                any(not isinstance(source, str) for source in problem["evidence"])):
            raise RetroError("problem lacks primary evidence")
        if not isinstance(problem.get("handled_here"), str) or not problem["handled_here"]:
            raise RetroError("problem lacks Handled here")
        prevention = problem.get("prevention")
        if (not isinstance(prevention, dict) or prevention.get("destination") not in DESTINATIONS or
                not isinstance(prevention.get("text"), str) or not prevention["text"]):
            raise RetroError("problem lacks Prevention and its destination")
        if (not isinstance(problem.get("earlier_occurrences"), list) or
                any(not isinstance(row, dict) for row in problem["earlier_occurrences"])):
            raise RetroError("problem lacks Earlier occurrences, even when none")
        for source in problem["evidence"]:
            evidence_source(source)
        for previous in problem["earlier_occurrences"]:
            if not previous.get("memory_id") or not previous.get("evidence"):
                raise RetroError("earlier occurrence needs a Memory id and original evidence")
            evidence_source(previous["evidence"])
            match = search(problem["category"], problem["cause"])["matches"]
            matched = next((row for row in match if row["id"] == previous["memory_id"]), None)
            if not matched or previous["evidence"] not in matched["content"]:
                raise RetroError("earlier mmw-retro does not cite the original same-cause source")
            if previous["evidence"] in problem["evidence"]:
                raise RetroError("an earlier occurrence repeats the same event or commit")
            if occurrence(previous["evidence"]) in {occurrence(url) for url in problem["evidence"]}:
                raise RetroError("an earlier event belongs to the same issue occurrence")
        proposal = problem.get("proposal")
        if proposal is not None:
            if not isinstance(proposal, dict) or not all(proposal.get(key) for key in ("repository", "title", "body")):
                raise RetroError("proposal needs responsible repository, title and body")
            if not re.fullmatch(r"[^/\s]+/[^/\s]+", proposal["repository"]):
                raise RetroError("proposal repository is not owner/name")
            for key in ("prompt_change",):
                if key in proposal:
                    validate_prompt(proposal[key], problem)
            if not qualifies(problem, gathered):
                raise RetroError("proposal has no two independent sources or proposed Memory blocker")


def validate_prompt(change: dict, problem: dict) -> None:
    keys = ("target_file", "heading", "source", "current_passage", "proposed_passage",
            "changes_made", "expected_behavior")
    if not isinstance(change, dict) or any(not change.get(key) for key in keys):
        raise RetroError("prompt_change lacks target, full passages, Changes Made or expected behavior")
    if change["source"] not in problem["evidence"]:
        raise RetroError("prompt change source is not this problem's primary evidence")
    answers = change["changes_made"]
    if not isinstance(answers, dict) or set(answers) != {"context_or_constraints", "ambiguity",
                                                      "success_criteria_or_requirement", "timing"}:
        raise RetroError("prompt_change needs all four Changes Made answers")
    if any(not isinstance(x, str) or not x for x in answers.values()):
        raise RetroError("prompt_change has an empty Changes Made answer")
    target = REPO / change["target_file"]
    if not target.resolve().is_relative_to(REPO.resolve()):
        raise RetroError("prompt target leaves the responsible repository")
    if not target.is_file() or change["heading"] not in target.read_text(encoding="utf-8"):
        raise RetroError("prompt target file and heading do not exist")
    if change["current_passage"] not in target.read_text(encoding="utf-8"):
        raise RetroError("current complete passage does not occur in target file")
    if change["current_passage"] == change["proposed_passage"]:
        raise RetroError("prompt proposal does not change the passage")


def qualifies(problem: dict, gathered: dict) -> bool:
    urls = list(dict.fromkeys(problem["evidence"] + [p["evidence"] for p in problem["earlier_occurrences"]]))
    sources = [evidence_source(url) for url in urls]
    occurrences = {occurrence(url) for url, (kind, _) in zip(urls, sources)
                   if kind in ("event", "commit")}
    if len(occurrences) >= 2:
        return True
    manifest = gathered.get("memory_closing") or {}
    for item in manifest.get("decisions", []):
        if item.get("decision") != "propose" or item.get("memory_id") not in gathered["proposed_memory_ids"]:
            continue
        if item.get("evidence") not in problem["evidence"]:
            continue
        if any((value.get("event") in ("worker.queued", "ticket.returned") or
                (value.get("event") == "child.opened" and value.get("kind") == "fault") or
                (value.get("event") == "ticket.checked" and value.get("result") == "handoff"))
               for kind, text in sources if kind == "event"
               for what, value in [events.parse(text)] if what == "event"):
            return True
    return False


def proposal_body(problem: dict, gathered: dict, memory_id: str) -> str:
    proposal = problem["proposal"]
    evidence = sorted(set(problem["evidence"] + [p["evidence"] for p in problem["earlier_occurrences"]]))
    text = (f"Problem: {problem['category']}: {problem['cause']}\n"
            f"Sources:\n" + "".join(f"- {url}\n" for url in evidence) +
            f"Handled here: {problem['handled_here']}\n"
            f"Prevention: {problem['prevention']['text']}\n"
            f"Destination: {problem['prevention']['destination']}\n"
            f"Source spec: {gathered['spec_url']}\nRetro Memory: nowledgemem://memory/{memory_id}\n\n"
            f"{proposal['body'].strip()}\n")
    change = proposal.get("prompt_change")
    if change:
        text += (f"\nPrompt target: {change['target_file']} ## {change['heading']}\n"
                 f"Prompt source: {change['source']}\n"
                 f"Current complete passage:\n{change['current_passage']}\n"
                 f"Proposed complete passage:\n{change['proposed_passage']}\n"
                 f"Changes Made:\n" + "".join(f"- {key}: {value}\n" for key, value in change["changes_made"].items()) +
                 f"Expected behavior: {change['expected_behavior']}\n")
    return text


def create_or_reuse(problem: dict, gathered: dict, memory_id: str) -> str:
    proposal = problem["proposal"]
    body = proposal_body(problem, gathered, memory_id)
    repo = proposal["repository"]
    # gh issue list emits a JSON array, unlike issue view. Do not infer that the
    # default page of 30 is the complete needs-triage queue.
    raw = gh("issue", "list", "--repo", repo, "--state", "open", "--label",
             "needs-triage", "--limit", "500", "--json", "number,url,body")
    try:
        rows = json.loads(raw)
    except ValueError as exc:
        raise RetroError("proposal lookup returned unreadable JSON") from exc
    if not isinstance(rows, list):
        raise RetroError("proposal lookup did not return a complete list")
    sources = sorted(set(problem["evidence"] + [p["evidence"] for p in problem["earlier_occurrences"]]))
    for row in rows:
        if isinstance(row, dict) and gathered["spec_url"] in str(row.get("body", "")) and all(
                url in str(row.get("body", "")) for url in sources):
            return row["url"]
    return gh("issue", "create", "--repo", repo, "--label", "needs-triage",
              "--title", proposal["title"], "--body-file", "-", stdin=body).splitlines()[-1]


def evidence_line(items: list[dict]) -> str:
    """Name every missing or unreadable source; count present sources per issue and detail.

    A night's event comments run to hundreds, and one line each would exceed the Space's
    content limit. A present source is recoverable from `gather`, so only its count is kept.
    """
    present: dict[tuple[str, str], list[str]] = {}
    order: list[tuple[str, str] | dict] = []
    for item in items:
        if item["status"] != "present":
            order.append(item)
            continue
        key = (item["source"].split("#issuecomment-", 1)[0], item["detail"])
        if key not in present:
            present[key] = []
            order.append(key)
        present[key].append(item["source"])
    parts = []
    for entry in order:
        if isinstance(entry, dict):
            parts.append(f"{entry['source']} [{entry['status']}] {entry['detail']}")
        elif len(present[entry]) == 1:
            parts.append(f"{present[entry][0]} [present] {entry[1]}")
        else:
            parts.append(f"{entry[0]} [present] {len(present[entry])}× {entry[1]}")
    return "; ".join(parts)


def render(data: dict, gathered: dict, proposal_urls: dict[int, str]) -> str:
    root = data["task_root"]
    label = f"map #{root['number']}" if root["kind"] == "map" else f"standalone spec #{root['number']}"
    lines = [f"Spec: {repository()}#{data['spec']}", f"Task root: {label}",
             "Evidence checked: " + evidence_line(data["evidence_checked"]),
             "", "## Previous proposals"]
    lines += [f"- {x['url']} — " + (f"已落地：{x['evidence']}" if x["status"] == "landed"
                                     else "没找到证据") for x in data["previous_proposals"]] or ["none"]
    lines += ["", "## Problems observed"]
    for index, problem in enumerate(data["problems"]):
        earlier = "; ".join(f"{x['memory_id']} + {x['evidence']}" for x in problem["earlier_occurrences"]) or "none"
        lines += [f"### {problem['category']}: {problem['cause']}",
                  "Evidence: " + "; ".join(problem["evidence"]),
                  f"Handled here: {problem['handled_here']}",
                  f"Prevention: {problem['prevention']['text']} [{problem['prevention']['destination']}]",
                  f"Earlier occurrences: {earlier}", f"Proposal: {proposal_urls.get(index, 'none')}", ""]
    if not data["problems"]:
        lines.append("none")
    intent = data["intent_reconciliation"]
    lines += ["", "## Intent reconciliation", f"Expected: {intent['expected']}",
              f"Observed: {intent['observed']}", f"Gap: {intent['gap']}", "",
              "## Review learning", data["review_learning"], "",
              f"Observed: {data['observed']['at']} {data['observed']['base_commit']}"]
    return "\n".join(lines) + "\n"


def receipt(number: int, *, result: str, memory_id: str = "", problems: int = 0,
            proposals: list[str] | None = None, unreadable: list[str] | None = None,
            reason: str = "") -> None:
    if result == "recorded":
        unreadable = unreadable or []
        links = proposals or []
        evidence = "partial" if unreadable else "complete"
        line = ("NIGHT RETRO\nResult: recorded\nRetro Memory: nowledgemem://memory/"
                f"{memory_id}\nProblems: {problems}\nProposals: " + (", ".join(links) or "none") +
                f"\nEvidence: {evidence}" + (f" ({', '.join(unreadable)})" if unreadable else ""))
        numbers = [int(urlparse(url).path.rsplit("/", 1)[-1]) for url in links]
        body = events.build("spec.retroed", ticket=None, spec=number, line=line,
                            result="recorded", retro_memory=memory_id,
                            problem_count=problems, proposals=numbers, evidence=evidence,
                            unreadable_sources=unreadable)
    else:
        line = f"NIGHT RETRO\nResult: unrecorded\nReason: {reason}"
        body = events.build("spec.retroed", ticket=None, spec=number, line=line,
                            result="unrecorded", reason=reason)
    gh("issue", "comment", str(number), "--body-file", "-", stdin=body)


def finalize(number: int, file: Path) -> dict:
    gathered = gather(number)
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RetroError(f"analyzed UTF-8 JSON is unreadable: {exc}") from exc
    if not isinstance(data, dict):
        raise RetroError("analysis is not one JSON object")
    check_analysis(number, data, gathered)
    ident = f"mmw-retro-{space()}-spec-{number}"
    links = {}
    for index, problem in enumerate(data["problems"]):
        if problem.get("proposal") is not None:
            links[index] = create_or_reuse(problem, gathered, ident)
    unreadable = list(dict.fromkeys(x["source"] for x in data["evidence_checked"]
                                if x["status"] != "present"))
    content = render(data, gathered, links)
    env = dict(os.environ)
    env["NMEM_SPACE"] = space()
    try:
        output = command(["nmem", "--json", "memories", "add", "--stdin", "--id", ident,
                          "--space", space(), "--source", "mmw-retro", "--unit-type", "event",
                          "--label", "mmw-retro", "--title",
                          f"Retro: {repository()}#{number} — {gathered['title']}"], stdin=content, env=env)
        saved = json.loads(output)
        if not isinstance(saved, dict) or saved.get("id") != ident:
            raise RetroError(f"Memory write did not confirm fixed id {ident}")
    except (RetroError, ValueError) as exc:
        reason = f"Retro Memory write failed: {exc}"
        receipt(number, result="unrecorded", reason=reason)
        return {"result": "unrecorded", "reason": reason,
                "proposals": list(dict.fromkeys(links.values()))}
    proposal_links = list(dict.fromkeys(links.values()))
    receipt(number, result="recorded", memory_id=ident, problems=len(data["problems"]),
            proposals=proposal_links, unreadable=unreadable)
    return {"result": "recorded", "retro_memory": ident, "problem_count": len(data["problems"]),
            "proposals": proposal_links, "evidence": "partial" if unreadable else "complete",
            "unreadable_sources": unreadable}


class RetroArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        next_step = f"Next: python3 {Path(__file__).resolve()} --help."
        sys.stderr.write("retro: " + refusal.refusal(
            f"arguments: {message}", "because the retro command is incomplete or invalid.",
            next_step) + "\n")
        raise SystemExit(2)


def refusal_for(exc: Exception, args: argparse.Namespace) -> str:
    fact = f"{args.verb} {getattr(args, 'spec', '')}: {exc}".strip()
    if args.verb == "gather":
        return refusal.refusal(fact, "because primary completed-spec sources could not be verified.",
                                refusal.REPORT_BLOCKED)
    if args.verb == "search":
        return refusal.refusal(fact, "because the category, cause or earlier Memory could not be verified.",
                                f"Next: python3 {Path(__file__).resolve()} search 'Automated checks' '<specific cause>'.")
    return refusal.refusal(fact, "because analyzed evidence or proposal support could not be verified.",
                           f"Next: python3 {Path(__file__).resolve()} gather {args.spec}.")


def main(argv: list[str] | None = None) -> int:
    global REPO, REPOSITORY_OVERRIDE
    parser = RetroArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, help="checkout to read; used for isolated tests")
    parser.add_argument("--repository", help="origin repository name; used with temporary Git origins")
    sub = parser.add_subparsers(dest="verb", required=True)
    sub.add_parser("gather").add_argument("spec", type=int)
    query = sub.add_parser("search")
    query.add_argument("category")
    query.add_argument("cause")
    finish = sub.add_parser("finalize")
    finish.add_argument("spec", type=int)
    finish.add_argument("analysis", type=Path)
    args = parser.parse_args(argv)
    try:
        REPO = git_root(args.repo.resolve() if args.repo else Path.cwd())
    except RetroError as exc:
        sys.stderr.write(f"retro: {refusal_for(exc, args)}\n")
        return 2
    if args.repository:
        if not args.repo or not re.fullmatch(r"[^/\s]+/[^/\s]+", args.repository):
            parser.error("--repository is available only with --repo and needs owner/name")
        REPOSITORY_OVERRIDE = args.repository
    try:
        value = (gather(args.spec) if args.verb == "gather" else
                 search(args.category, args.cause) if args.verb == "search" else
                 finalize(args.spec, args.analysis))
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0
    except (RetroError, events.EventError) as exc:
        sys.stderr.write(f"retro: {refusal_for(exc, args)}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
