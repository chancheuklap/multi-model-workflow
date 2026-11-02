#!/usr/bin/env python3
"""Record ticket results, review reports and repository checks.

    verify-ticket.py N --closeout FILE --result complete|incomplete --commit SHA [--into BRANCH]
    verify-ticket.py N --review FILE --base REF --head SHA
    verify-ticket.py [N] --repository-check --base REF [--tier default|all]
    verify-ticket.py N --sub-issue KIND FILE [--existing CHILD]
    verify-ticket.py N --route CHILD fixed --report FILE [--commit SHA]
    verify-ticket.py N --route CHILD stale --report FILE --reason invalid|fixed-elsewhere
    verify-ticket.py N --route CHILD became-ticket --became TICKET --report FILE

Reports are UTF-8 text without required headings or acceptance-criterion syntax.
Completion is the caller's explicit declaration, not a machine proof of prose criteria.
The script checks commit/session identity and records metadata through events.py.
Repository checks execute scripts/check independently of ticket completion.

Exit 0: recorded, already recorded, or a passing repository check. Exit 1: a repository
check failed or the tracker operation did not finish. Exit 2: invalid input or a check
cannot run. --check-only validates a report without changing tracker records.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "dispatch/scripts"))
import events
import statedir
import tracker
from repository_checks import (
    checks_bounce_prose, covering_proof, proof_fields, repository_check_missing,
    run_repository_check, run_worktree_environment, tree_identity,
)


class Refusal(ValueError):
    pass


class TrackerError(RuntimeError):
    pass


def gh(*args: str) -> str:
    run = subprocess.run(["gh", *args], env=tracker.environment(), capture_output=True, text=True)
    if run.returncode:
        detail = (run.stderr or run.stdout).strip()
        raise TrackerError(f"gh {' '.join(args[:3])} failed: {detail or run.returncode}")
    return run.stdout


def gh_json(*args: str):
    try:
        return json.loads(gh(*args))
    except json.JSONDecodeError:
        raise TrackerError(f"gh {' '.join(args[:3])} did not return JSON") from None


def fetch_ticket(number: int) -> dict:
    ticket = gh_json("issue", "view", str(number), "--json",
                     "number,state,stateReason,labels,parent,body,assignees")
    if not isinstance(ticket, dict) or ticket.get("state") not in ("OPEN", "CLOSED"):
        raise TrackerError(f"could not read the state of #{number}")
    return ticket


def fetch_comments(number: int) -> list[dict]:
    repo = tracker.repository()
    pages = gh_json("api", "--paginate", "--slurp", f"repos/{repo}/issues/{number}/comments?per_page=100")
    if not isinstance(pages, list) or any(not isinstance(page, list) for page in pages):
        raise TrackerError(f"could not read every comment page of #{number}")
    rows = [row for page in pages for row in page]
    if any(not isinstance(row, dict) or not isinstance(row.get("body"), str) for row in rows):
        raise TrackerError(f"comments of #{number} contain unreadable rows")
    return rows


def read_state(number: int) -> tuple[dict, dict]:
    ticket = fetch_ticket(number)
    comments = fetch_comments(number)
    state = events.fold(comments, issue=number)
    state["comments"] = comments
    if state["unreadable"]:
        bad = state["unreadable"][0]
        raise Refusal(f"#{number} comment {bad['comment']} cannot be read: {bad['reason']}; nothing was written")
    return ticket, state


def post_comment(number: int, body: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as file:
        file.write(body)
        path = file.name
    try:
        gh("issue", "comment", str(number), "--body-file", path)
    finally:
        os.unlink(path)


def post_event(number: int, ticket: dict, event: str, line: str, text: str, **fields) -> None:
    parent = ticket.get("parent") or {}
    body = events.build(event, ticket=number, spec=parent.get("number"), line=line, text=text, **fields)
    post_comment(number, body)


def git(*args: str, cwd: Path | None = None) -> str:
    run = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if run.returncode:
        raise Refusal(f"git {' '.join(args)} failed: {(run.stderr or run.stdout).strip()}")
    return run.stdout.strip()


def commit_ref(ref: str, root: Path) -> str:
    return git("rev-parse", "--verify", f"{ref}^{{commit}}", cwd=root)


def report_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise Refusal(f"report {path} is empty; write the actual result before submitting")
    return text


def own_session() -> tuple[str, str] | None:
    script = HERE.parents[1] / "dispatch/scripts/dispatch.sh"
    run = subprocess.run(["bash", str(script), "self"], capture_output=True, text=True,
                         env=tracker.environment(), timeout=60)
    runner, _, session = run.stdout.strip().partition("\t")
    return (runner, session) if run.returncode == 0 and runner and session else None


def result_lock(number: int):
    state = statedir.state_dir(tracker.repository())
    return statedir.locked(state / f"ticket-{number}-result.lock", purpose=f"ticket #{number} result")


def bound_identity(number: int, state: dict, kind: str, root: Path) -> dict:
    marker = os.environ.get("MMW_TICKET")
    if marker is not None and marker != str(number):
        raise Refusal(f"this dispatched session belongs to ticket #{marker}, not #{number}; nothing was written")
    own = own_session()
    live = [s for s in state["sessions"] if s["kind"] == kind and s["live"]]
    chosen = live[-1] if live else None
    pair = (chosen.get("runner"), chosen.get("session")) if chosen else own
    latest = None
    any_start = False
    matching_start = False
    for comment in events.normalise(state["comments"]):
        what, payload = events.parse(comment["body"])
        if what == "event" and payload["event"] == f"{kind}.started":
            any_start = True
            if (payload.get("runner"), payload.get("session")) == own:
                matching_start = True
            if (payload.get("runner"), payload.get("session")) == pair:
                latest = payload
    if marker is not None and not matching_start:
        raise Refusal(f"#{number} has no matching {kind}.started for this dispatched session "
                      f"{own}; retry after dispatch records {kind}.started; nothing was written")
    if any_start and latest is None:
        raise Refusal(f"#{number} has no {kind} startup for this caller {own}; nothing was written")
    if latest:
        if own != (latest.get("runner"), latest.get("session")):
            raise Refusal(f"#{number} belongs to {kind} {latest.get('runner')} session {latest.get('session')}; "
                          f"this caller is {own or 'not an identifiable runner session'}")
        if latest.get("worktree") and Path(latest["worktree"]).resolve() != root:
            raise Refusal(f"#{number} {kind} belongs to worktree {latest['worktree']}, not {root}")
        if latest.get("branch") and latest["branch"] != git("symbolic-ref", "--quiet", "--short", "HEAD", cwd=root):
            raise Refusal(f"#{number} {kind} belongs to branch {latest['branch']}")
    return {**(latest or {}), **({"runner": own[0], "session": own[1]} if own else {}),
            "active": bool(chosen) or not any_start}


def current_commit(expected: str, root: Path, clean: bool) -> str:
    head = commit_ref("HEAD", root)
    if not re.fullmatch(r"[0-9a-f]{40}", expected) or expected != head:
        raise Refusal(f"report names commit {expected}, but current HEAD is {head}; report the actual output commit")
    if clean and git("status", "--porcelain", cwd=root):
        raise Refusal("worktree has uncommitted or untracked files; no commit names that output")
    return head


def same_report(record: dict | None, fields: dict, text: str) -> bool:
    if not record:
        return False
    payload = record["payload"]
    if any(payload.get(key) != value for key, value in fields.items()):
        return False
    prose = events.BLOCK_RE.sub("", record["body"]).strip()
    return "\n".join(prose.splitlines()[1:]).strip() == events.neutralise(text).strip()


def run_review(number: int, path: Path, base: str, head: str, check_only: bool = False) -> int:
    text = report_text(path)
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    reviewed = current_commit(head, root, clean=False)
    baseline = commit_ref(base, root)
    with result_lock(number):
        ticket, state = read_state(number)
        identity = bound_identity(number, state, "reviewer", root)
        for key, actual in (("base", baseline), ("head", reviewed)):
            if identity.get(key) and identity[key] != actual:
                raise Refusal(f"#{number} reviewer.started names {key} {identity[key]}, not {actual}")
        fields = {"base": baseline, "head": reviewed}
        fields.update({k: identity[k] for k in ("runner", "session") if identity.get(k)})
        if same_report(state["review"], fields, text):
            print(f"REVIEW ALREADY RECORDED: #{number} {baseline}..{reviewed}")
            return 0
        if not identity["active"]:
            raise Refusal(f"#{number} reviewer session has ended; only an identical recorded report may be retried")
        if check_only:
            print(f"REVIEW READY: #{number} {baseline}..{reviewed}")
            return 0
        current_commit(reviewed, root, clean=False)
        post_event(number, ticket, "reviewer.reported", f"Review of #{number}: {baseline}..{reviewed}", text, **fields)
    print(f"REVIEW RECORDED: #{number} {baseline}..{reviewed}")
    return 0


def push_ticket_branch(number: int, root: Path, commit: str) -> str | None:
    """Push the output commit to `origin/issue-<n>` without rewriting history."""
    ref = f"refs/heads/issue-{number}"
    try:
        pushed = subprocess.run(
            ["git", "push", "origin", f"{commit}:{ref}"], cwd=root,
            capture_output=True, text=True,
        )
        if pushed.returncode != 0:
            detail = " ".join((pushed.stderr or pushed.stdout).strip().splitlines())
            return (f"origin rejected {commit} for issue-{number}: "
                    f"{detail[:500] or f'git push exited {pushed.returncode}'}. "
                    f"Resolve the rejection and run --closeout again. "
                    f"No force-push was used")
        remote = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", ref], cwd=root,
            capture_output=True, text=True,
        )
    except OSError as exc:
        return (f"git could not reach origin for issue-{number} at output commit {commit}: "
                f"{exc}. Fix Git access and run --closeout again")
    remote_commit = (remote.stdout.strip().split() or [""])[0]
    if remote.returncode != 0 or remote_commit != commit:
        detail = " ".join((remote.stderr or remote.stdout).strip().splitlines())
        resolved = remote_commit or "nothing"
        return (f"origin/issue-{number} could not be confirmed at output commit {commit}: "
                f"{detail[:500] or f'it resolved to {resolved}'}. "
                f"Confirm the remote and run --closeout again")
    return None


def run_closeout(number: int, path: Path, result: str, commit: str,
                 into: str | None = None, check_only: bool = False) -> int:
    text = report_text(path)
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    head = current_commit(commit, root, clean=(result == "complete"))
    with result_lock(number):
        ticket, state = read_state(number)
        identity = bound_identity(number, state, "worker", root)
        target = into or identity.get("into")
        if into and identity.get("into") and into != identity["into"]:
            raise Refusal(f"#{number} worker targets {identity['into']}, not {into}")
        if result == "complete":
            if not target:
                raise Refusal("a completed output needs its target branch: --into BRANCH or worker.started.into")
            git("check-ref-format", "--branch", target, cwd=root)
        fields = {"commit": head, "branch": git("symbolic-ref", "--quiet", "--short", "HEAD", cwd=root)}
        if result == "complete" and fields["branch"] != f"issue-{number}":
            raise Refusal(f"#{number} output belongs on issue-{number}, not {fields['branch']}; nothing was pushed or recorded")
        if target:
            fields["into"] = target
        fields.update({k: identity[k] for k in ("runner", "session") if identity.get(k)})
        event = "ticket.passed" if result == "complete" else "ticket.returned"
        names = {row["name"] for row in ticket.get("labels") or []}
        settled = (ticket["state"] == "CLOSED" if result == "complete" else
                   ticket["state"] == "OPEN" and "needs-triage" in names)
        previous = state["outcome"]
        newer_start = any(e["event"] == "worker.started" and
                          e.get("comment", 0) > (previous or {}).get("comment", 0) for e in state["events"])
        if ticket["state"] == "CLOSED" and (result != "complete" or ticket.get("stateReason") != "COMPLETED"):
            raise Refusal(f"#{number} is closed as {ticket.get('stateReason')}; this command will not replace that disposition")
        if settled and not newer_start and previous and previous["event"] == event and same_report(previous, fields, text):
            print(f"RESULT ALREADY RECORDED: #{number} {event} at {head}")
            return 0
        if not identity["active"]:
            raise Refusal(f"#{number} worker session has ended; only an identical recorded result may be retried")
        if check_only:
            print(f"RESULT READY: #{number} {event} at {head}")
            return 0
        current_commit(head, root, clean=(result == "complete"))
        if result == "complete":
            problem = push_ticket_branch(number, root, head)
            if problem:
                raise TrackerError(problem)
        try:
            if result == "complete":
                if ticket["state"] != "CLOSED":
                    gh("issue", "close", str(number), "--reason", "completed")
                gh("issue", "edit", str(number), "--remove-label", "ready-for-agent", "--remove-assignee", "@me")
            else:
                gh("issue", "edit", str(number), "--add-label", "needs-triage", "--remove-label", "ready-for-agent",
                   "--remove-assignee", "@me")
            post_event(number, ticket, event, f"Ticket #{number}: {result}", text, **fields)
        except TrackerError as exc:
            raise TrackerError(f"result for #{number} is incomplete: {exc}; inspect the issue and rerun the same command") from None
    print(f"RESULT RECORDED: #{number} {event} at {head}")
    return 0


def run_sub_issue(number: int, kind: str, path: Path, existing: int | None = None) -> int:
    text = report_text(path)
    with result_lock(number):
        return _sub_issue(number, kind, text, existing)


def _sub_issue(number: int, kind: str, text: str, existing: int | None) -> int:
    ticket, state = read_state(number)
    title = text.strip().splitlines()[0].strip()[:256]
    if existing is not None:
        child_issue = fetch_ticket(existing)
        names = {label["name"] for label in child_issue.get("labels") or []}
        if ((child_issue.get("parent") or {}).get("number") != number or "mmw:child" not in names
                or (child_issue.get("body") or "").strip() != text.strip()):
            raise Refusal(f"#{existing} does not match this parent, child label and report; nothing was created or recorded")
        entry = state["children"].get(str(existing)) or {}
        if entry.get("opened"):
            if entry.get("kind") != kind:
                raise Refusal(f"#{existing} was recorded as {entry.get('kind')}, not {kind}")
            print(existing)
            return 0
        child = existing
    else:
        args = ["issue", "create", "--parent", str(number), "--label", "mmw:child", "--title", title]
        if kind in ("decision", "deferred"):
            args.extend(("--label", "needs-triage"))
        with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as file:
            file.write(text)
            name = file.name
        try:
            printed = gh(*args, "--body-file", name).strip()
        finally:
            os.unlink(name)
        found = re.search(r"/issues/(\d+)", printed)
        if not found:
            raise TrackerError(f"child was created under #{number}, but gh returned no issue number: {printed}; do not create another")
        child = int(found[1])
    try:
        post_event(number, ticket, "child.opened", f"Opened #{child} ({kind}): {title}", "", child=child, kind=kind, title=title)
    except TrackerError as exc:
        raise TrackerError(f"child #{child} exists, but its event was not posted: {exc}; "
                           f"retry --sub-issue {kind} FILE --existing {child} with the same report; do not create another") from None
    print(child)
    return 0


def _child_report(state: dict, child: int) -> dict | None:
    previous = None
    for comment in events.normalise(state["comments"]):
        record = events.newest([comment], "child.closed")
        if record and record["payload"].get("child") == child:
            previous = record
    return previous


def _became_ticket(number: int, child: int, became: int, ticket: dict, state: dict,
                   entry: dict, text: str) -> int:
    spec = entry.get("spec")
    if not spec and ticket.get("parent"):
        raise Refusal(f"#{number} has a parent but child.opened for #{child} names no spec; nothing was changed")
    child_issue = fetch_ticket(child)
    parent = (child_issue.get("parent") or {}).get("number")
    if parent not in (number, spec):
        raise Refusal(f"#{child} is not natively linked under #{number} or its recorded spec; nothing was changed")
    target = child_issue if became == child else fetch_ticket(became)
    labels = {label["name"] for label in target.get("labels") or []}
    for kind in ("mmw:map", "mmw:spec"):
        if kind in labels:
            raise Refusal(f"#{became} carries {kind}; a map or spec cannot become a ticket")
    fields = {"child": child, "resolution": "became-ticket", "became": became}
    if entry.get("resolution"):
        if entry.get("ticket") != became or not same_report(_child_report(state, child), fields, text):
            raise Refusal(f"#{child} has a different recorded target or resolution report; nothing was changed")
        print(f"CHILD ALREADY ROUTED: #{child} became ticket #{became}")
        return 0
    edit = []
    if "mmw:ticket" not in labels:
        edit.extend(("--add-label", "mmw:ticket"))
    current_parent = (target.get("parent") or {}).get("number")
    if spec and current_parent != spec:
        edit.extend(("--parent", str(spec)))
    elif not spec and became == child and current_parent is not None:
        edit.append("--remove-parent")
    for kind in ("mmw:child", "mmw:lesson", "mmw:problem"):
        if kind in labels:
            edit.extend(("--remove-label", kind))
    try:
        if edit:
            gh("issue", "edit", str(became), *edit)
        if became != child and child_issue["state"] != "CLOSED":
            gh("issue", "close", str(child), "--duplicate-of", str(became))
        origin = {**ticket, "parent": {"number": spec} if spec else None}
        post_event(number, origin, "child.closed", f"Child #{child} became ticket #{became}", text, **fields)
    except TrackerError as exc:
        raise TrackerError(f"routing #{child} to ticket #{became} is incomplete: {exc}; rerun the same command") from None
    print(f"CHILD ROUTED: #{child} became ticket #{became}")
    return 0


def run_route(number: int, child: int, resolution: str, path: Path, reason: str | None,
              commit: str | None = None, became: int | None = None) -> int:
    text = report_text(path)
    with result_lock(number):
        ticket, state = read_state(number)
        entry = state["children"].get(str(child)) or {}
        if not entry.get("opened"):
            raise Refusal(f"#{number} has no child.opened for #{child}; nothing was changed")
        if entry.get("resolution") and (entry["resolution"] != resolution or entry.get("reason") != reason):
            raise Refusal(f"#{child} was already routed {entry['resolution']}")
        if resolution == "became-ticket":
            if became is None or became < 1 or reason is not None or commit is not None:
                raise Refusal("became-ticket needs --became TICKET and takes no --reason or --commit")
            if entry.get("resolution") and entry.get("ticket") != became:
                raise Refusal(f"#{child} was already routed to ticket #{entry.get('ticket')}; nothing was changed")
            return _became_ticket(number, child, became, ticket, state, entry, text)
        if became is not None:
            raise Refusal("--became is only available with became-ticket")
        if resolution == "stale" and reason not in ("invalid", "fixed-elsewhere"):
            raise Refusal("stale needs --reason invalid|fixed-elsewhere")
        if resolution == "fixed" and reason:
            raise Refusal("fixed takes no stale reason")
        head = None
        if resolution == "fixed" and commit is not None:
            root = Path(git("rev-parse", "--show-toplevel")).resolve()
            head = current_commit(commit, root, clean=True)
        child_issue = fetch_ticket(child)
        if (child_issue.get("parent") or {}).get("number") != number:
            raise Refusal(f"#{child} is not natively linked under #{number}; nothing was changed")
        if child_issue["state"] == "CLOSED" and resolution == "fixed" and child_issue.get("stateReason") != "COMPLETED":
            raise Refusal(f"#{child} is closed as {child_issue.get('stateReason')}; nothing was changed")
        fields = {"child": child, "resolution": resolution}
        if reason:
            fields["reason"] = reason
        if head:
            fields["commit"] = head
        if entry.get("resolution") and child_issue["state"] == "CLOSED":
            previous = _child_report(state, child)
            if not same_report(previous, fields, text) or (resolution == "fixed" and previous["payload"].get("commit") != head):
                raise Refusal(f"#{child} has a different recorded resolution report; no new report was posted")
            print(f"CHILD ALREADY ROUTED: #{child}")
            return 0
        if child_issue["state"] != "CLOSED":
            gh("issue", "close", str(child), "--reason", "completed" if resolution == "fixed" else "not planned")
        try:
            post_event(number, ticket, "child.closed", f"Resolved #{child}: {resolution}", text, **fields)
        except TrackerError as exc:
            raise TrackerError(f"child #{child} was closed but its resolution event failed: {exc}; rerun the same command") from None
    print(f"CHILD ROUTED: #{child} {resolution}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ticket", nargs="?", type=int)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--closeout", type=Path)
    action.add_argument("--review", type=Path)
    action.add_argument("--repository-check", action="store_true")
    action.add_argument("--sub-issue", nargs=2, metavar=("KIND", "FILE"))
    action.add_argument("--route", nargs=2, metavar=("CHILD", "RESOLUTION"))
    parser.add_argument("--result", choices=("complete", "incomplete"))
    parser.add_argument("--commit")
    parser.add_argument("--into")
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--tier", choices=("default", "all"), default="default")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--reason", choices=("invalid", "fixed-elsewhere"))
    parser.add_argument("--existing", type=int)
    parser.add_argument("--became", type=int)
    args = parser.parse_args(argv)
    try:
        if args.check_only and not (args.closeout or args.review):
            raise Refusal("--check-only is available for --closeout and --review; nothing was run or written")
        if args.repository_check:
            if not args.base:
                raise Refusal("--repository-check needs --base REF")
            root = Path(git("rev-parse", "--show-toplevel"))
            checked = run_repository_check(root, args.base, root if args.ticket else None, args.ticket, args.tier)
            print(json.dumps(checked, ensure_ascii=False))
            return {"pass": 0, "red": 1, "missing": 2, "cannot-run": 2}[checked["status"]]
        if args.ticket is None or args.ticket < 1:
            raise Refusal("a positive ticket number is required")
        if args.closeout:
            if not args.result or not args.commit:
                raise Refusal("--closeout needs --result complete|incomplete and --commit SHA")
            return run_closeout(args.ticket, args.closeout, args.result, args.commit, args.into, args.check_only)
        if args.review:
            if not args.base or not args.head:
                raise Refusal("--review needs --base REF and --head SHA")
            return run_review(args.ticket, args.review, args.base, args.head, args.check_only)
        if args.sub_issue:
            kind, path = args.sub_issue
            if kind not in events.CHILD_KINDS:
                raise Refusal(f"child kind must be one of {', '.join(events.CHILD_KINDS)}")
            return run_sub_issue(args.ticket, kind, Path(path), args.existing)
        if args.route:
            child, resolution = args.route
            if not child.isdigit() or resolution not in ("fixed", "stale", "became-ticket") or not args.report:
                raise Refusal("--route needs CHILD fixed|stale|became-ticket and --report FILE")
            return run_route(args.ticket, int(child), resolution, args.report, args.reason, args.commit, args.became)
    except TrackerError as exc:
        print(f"verify-ticket: {exc}", file=sys.stderr)
        return 1
    except (ValueError, OSError, subprocess.SubprocessError, statedir.LockHeld) as exc:
        print(f"verify-ticket: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
