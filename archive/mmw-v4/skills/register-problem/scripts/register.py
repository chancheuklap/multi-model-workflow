#!/usr/bin/env python3
"""Find and register problems without deleting issues or changing an owner's refusal.

Exit 0: registered or found. Exit 1: GitHub accepted part of a registration; rerun
that command to finish it. Exit 2: nothing changed; stderr names the missing input.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verify = _load("registration_verify", SKILLS / "verify-ticket" / "scripts" / "verify-ticket.py")
events = verify.events
statedir = _load("registration_state", SKILLS / "dispatch" / "scripts" / "statedir.py")
tracker = _load("registration_tracker", SKILLS / "dispatch" / "scripts" / "tracker.py")


class RegistrationError(RuntimeError):
    pass


class UnconfirmedWrite(RegistrationError):
    pass


def command(args):
    try:
        result = subprocess.run(args, capture_output=True, text=True,
                                env={k: v for k, v in os.environ.items() if k not in ("CLICOLOR_FORCE", "CLICOLOR")}, timeout=120)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RegistrationError(f"{args[0]} could not run: {exc}") from None
    if result.returncode:
        raise RegistrationError(f"{' '.join(args[:3])}: {(result.stderr or result.stdout).strip()}")
    return result.stdout


def gh_json(args):
    raw = command(["gh", *args])
    try:
        return json.loads(raw)
    except ValueError:
        raise RegistrationError(f"gh {' '.join(args[:2])} returned invalid JSON") from None


def repository(value):
    try:
        statedir.slug(value)
    except ValueError as exc:
        raise RegistrationError(str(exc)) from None
    return value.lower()


def toolbox_repo():
    marker = statedir.home() / "installed-root"
    try:
        root = marker.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RegistrationError(f"cannot read {marker}: {exc}; repair the MMW install record") from None
    if not root or not Path(root).is_dir():
        raise RegistrationError(f"{marker} names no existing checkout; repair the MMW install record")
    remote = command(["git", "-C", root, "remote", "get-url", "origin"]).strip()
    match = re.fullmatch(r"(?:git@github\.com:|(?:https?|ssh)://(?:git@)?github\.com/)([^/]+/[^/]+?)(?:\.git)?/?", remote)
    if not match:
        raise RegistrationError(f"{marker}'s checkout has no GitHub origin; set its origin to the MMW repository")
    return repository(match[1])


def current_repo():
    return repository(tracker.repository())


def whole_list(endpoint):
    pages = gh_json(["api", endpoint, "--paginate", "--slurp"])
    if not isinstance(pages, list) or any(not isinstance(page, list) for page in pages):
        raise RegistrationError(f"{endpoint} did not return complete list pages; retry the read")
    return [row for page in pages for row in page]


def issue_list(repo):
    return [r for r in whole_list(f"repos/{repo}/issues?state=all&per_page=100")
            if "pull_request" not in r]


def problem_fields(body):
    section = re.search(r"^## Problem\s*\n(.*?)(?=^## |\Z)", body, re.M | re.S)
    return {key: value.strip() for key, value in
            re.findall(r"^\s*(问题代号|角度|发生了什么|证据|代价|该谁修)\s*[:：]\s*(.+)$",
                       section[1] if section else "", re.M)}


def find(words, repos):
    for repo in repos:
        for row in issue_list(repo):
            text = f"{row['title']}\n{row.get('body') or ''}".casefold()
            if not all(word.casefold() in text for word in words):
                continue
            kind = ",".join(l['name'] for l in row['labels'] if l['name'].startswith("mmw:")) or "-"
            code = problem_fields(row.get('body') or '').get("问题代号", "-")
            print(f"#{row['number']}\t{repo}\t{row['state']}\t{kind}\t{code}\t{row['title']}")
    return 0


def body_file_command(args, body):
    with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8") as fh:
        fh.write(body)
        fh.flush()
        return command(["gh", *args, "--body-file", fh.name])


def confirmed_write(args, accepted, body=None):
    try:
        return body_file_command(args, body) if body is not None else command(["gh", *args])
    except RegistrationError as failed:
        try:
            confirmed = accepted()
        except (RegistrationError, OSError, ValueError, KeyError, TypeError) as exc:
            raise UnconfirmedWrite(f"{failed}; could not confirm whether GitHub accepted it: {exc}") from None
        if not confirmed:
            raise failed
        return ""


def ensure_label(repo, name):
    color, description = verify.LABELS[name]
    try:
        command(["gh", "label", "create", name, "--repo", repo, "--color", color,
                 "--description", description])
    except RegistrationError as exc:
        if "already exists" not in str(exc):
            try:
                labels = whole_list(f"repos/{repo}/labels?per_page=100")
            except RegistrationError as unreadable:
                raise UnconfirmedWrite(f"{exc}; label acceptance could not be confirmed: {unreadable}") from None
            if any(label["name"] == name for label in labels):
                return True
            raise exc
        return False
    return True


def closing_link(repo, number):
    owner, name = repo.split("/")
    query = """query($o:String!, $r:String!, $n:Int!) {
      repository(owner:$o, name:$r) { issue(number:$n) {
        timelineItems(last:1, itemTypes:[CLOSED_EVENT]) { nodes {
          ... on ClosedEvent { closer { ... on Commit { url } ... on PullRequest { url } } }
        } }
      } }
    }"""
    data = gh_json(["api", "graphql", "-f", f"query={query}", "-f", f"o={owner}",
                    "-f", f"r={name}", "-F", f"n={number}"])
    if data.get("errors"):
        raise RegistrationError(f"#{number}'s closing record could not be read: {data['errors']}")
    nodes = data["data"]["repository"]["issue"]["timelineItems"]["nodes"]
    closer = (nodes[-1].get("closer") or {}).get("url") if nodes else None
    if closer:
        return closer
    record = events.newest(comments(repo, number), "ticket.passed", "ticket.landed")
    commit = record["payload"].get("commit") if record else None
    return f"https://github.com/{repo}/commit/{commit}" if commit and re.fullmatch(r"[0-9a-f]{40}", commit) else None


def read_issue(repo, number):
    return gh_json(["issue", "view", str(number), "--repo", repo,
                    "--json", "number,state,stateReason,labels,parent"])


def comments(repo, number):
    return whole_list(f"repos/{repo}/issues/{number}/comments?per_page=100")


def readable_state(repo, number):
    state = events.fold(comments(repo, number), issue=number)
    if state["unreadable"]:
        raise RegistrationError(f"{repo}#{number} has unreadable events: {state['unreadable']}; repair those comments before retrying")
    return state


def unfinished_spec(repo, number):
    parent = read_issue(repo, number).get("parent")
    if not parent:
        return None
    number = parent["number"]
    labels = {l["name"] for l in read_issue(repo, number)["labels"]}
    if "mmw:spec" in labels and not readable_state(repo, number)["spec_merged"]:
        return number
    return None


def add_problem(path, source, target, repos, ticket):
    body = path.read_text(encoding="utf-8")
    fields = problem_fields(body)
    required = ("问题代号", "角度", "发生了什么", "证据", "代价", "该谁修")
    if not re.search(r"^## Problem\s*$", body, re.M) or any(not fields.get(k) for k in required):
        raise RegistrationError(f"{path} needs ## Problem with all six fields; complete the registration")
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", fields["问题代号"]):
        raise RegistrationError(f"{path}'s 问题代号 must be a lower-case hyphenated phrase")
    if len(fields["问题代号"]) > 80:
        raise RegistrationError(f"{path}'s 问题代号 has {len(fields['问题代号'])} characters; "
                                "the limit is 80; shorten the code before registering")
    if fields["角度"] not in ("判断", "环境", "流程", "产品"):
        raise RegistrationError(f"{path}'s 角度 must be 判断、环境、流程 or 产品")
    responsible = fields["该谁修"]
    if responsible in ("MMW", "MMW 仓库"):
        responsible = toolbox_repo()
    named_repo = re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)?", responsible)
    expected = target if "/" in responsible else target.split("/")[1]
    if named_repo and responsible.casefold() != expected.casefold():
        destination = responsible if "/" in responsible else f"<owner>/{responsible}"
        raise RegistrationError(f"{path}'s 该谁修 names {responsible}, but the target is {target}; "
                                f"add --repo {destination} to register where the fix belongs")
    seen_in = current_repo()
    context = registration_context(seen_in, ticket)
    key = hashlib.sha256(json.dumps([str(path.resolve()), body, source, target, seen_in, context["ticket"]],
                                    sort_keys=True).encode()).hexdigest()
    directory = statedir.state_dir(toolbox_repo()) / "registrations"
    directory.mkdir(parents=True, exist_ok=True)
    code_key = hashlib.sha256(fields["问题代号"].encode()).hexdigest()
    with statedir.locked(directory / f"{code_key}.lock", purpose="register a problem"):
        pending = directory / f"{key}.json"
        rows = [(repo, row) for repo in repos for row in issue_list(repo)
                if problem_fields(row.get("body") or "").get("问题代号") == fields["问题代号"]]
        if len(rows) > 1:
            raise RegistrationError("multiple issues have this exact problem code: "
                                    + ", ".join(f"{r}#{i['number']}" for r, i in rows)
                                    + "; select the canonical code before retrying")
        if pending.exists():
            receipt = json.loads(pending.read_text(encoding="utf-8"))
        else:
            repo, row = rows[0] if rows else (target, None)
            plan = reopen_plan(repo, row) if row else dict(reopen=False, triage=False, note="", blocked_spec=None)
            receipt = dict(repo=repo, number=row["number"] if row else None,
                           request=uuid.uuid4().hex, plan=plan, context=context,
                           action="APPENDED" if row else "OPENED", changed=False)
            statedir.write_atomic(pending, json.dumps(receipt, ensure_ascii=False))
        return finish_registration(receipt, pending, fields, body, source, seen_in, rows)


def registration_context(repo, explicit_ticket):
    session_pair = verify.own_session()
    session = ":".join(session_pair) if session_pair else "none"
    ticket = explicit_ticket if explicit_ticket is not None else os.environ.get("MMW_TICKET")
    if not ticket:
        branch = command(["git", "branch", "--show-current"]).strip()
        match = re.fullmatch(r"(?:issue|fix)-(\d+)", branch)
        ticket = match[1] if match else None
    spec = None if explicit_ticket is not None else os.environ.get("MMW_SPEC")
    actor = "main"
    if ticket:
        ticket = int(ticket)
        try:
            row = read_issue(repo, ticket)
            parent = row.get("parent")
            if spec is None and parent:
                parent_row = read_issue(repo, parent["number"])
                if "mmw:spec" in {l["name"] for l in parent_row["labels"]}:
                    spec = parent["number"]
        except RegistrationError as exc:
            if explicit_ticket is None:
                raise
            print(f"register: could not read parent spec for {repo}#{ticket}: {exc}; "
                  "recording spec=null", file=sys.stderr)
        history = comments(repo, ticket)
        state = events.fold(history, issue=ticket)
        if state["unreadable"]:
            raise RegistrationError(f"#{ticket}'s events cannot be read; repair the history before registering")
        if session_pair:
            match = next((r for r in reversed(state["sessions"])
                          if (r["runner"], r["session"]) == session_pair), None)
            if match:
                actor = match["grade"] if match["kind"] == "worker" else match["kind"]
    context = dict(ticket=ticket, spec=int(spec) if spec else None, actor=actor, session=session)
    events.build("lesson.seen", line="Validate registration context", lesson=1,
                 seen_in=repo, source="noticed", **context)
    return context


def reopen_plan(repo, row):
    number = row["number"]
    readable_state(repo, number)
    labels = {l["name"] for l in row["labels"]}
    plan = dict(reopen=False, triage=False, note="", blocked_spec=None)
    if row["state"] != "closed" or "wontfix" in labels:
        return plan
    reason = row.get("state_reason")
    if reason == "not_planned":
        plan.update(reopen=True, triage="mmw:problem" in labels)
    elif reason == "completed":
        spec = unfinished_spec(repo, number)
        if spec is not None:
            plan["blocked_spec"] = spec
        else:
            link = closing_link(repo, number)
            plan.update(reopen=True, triage=True,
                        note=f"修了又犯。上次关闭的提交或 PR：{link or 'GitHub 未记录关闭它的提交或 PR'}。")
    return plan


def finish_registration(receipt, pending, fields, body, source, seen_in, matches):
    repo, number, plan = receipt["repo"], receipt["number"], receipt["plan"]
    def saved():
        statedir.write_atomic(pending, json.dumps(receipt, ensure_ascii=False))
    def created():
        found = [r for r in issue_list(repo)
                 if problem_fields(r.get("body") or "").get("问题代号") == fields["问题代号"]]
        if len(found) != 1:
            return False
        receipt["number"] = found[0]["number"]
        return True
    def occurrence_recorded():
        for comment in comments(repo, number):
            what, payload = events.parse(comment["body"])
            if what == "event" and payload.get("request") == receipt["request"]:
                return True
        return False
    try:
        if number is None and matches:
            matched_repo, matched = matches[0]
            if matched_repo != repo:
                raise RegistrationError(f"new match appeared at {matched_repo}#{matched['number']}; inspect it before retrying")
            number = receipt["number"] = matched["number"]
            saved()
        if number is None:
            labels = ["mmw:problem", "needs-triage"] if fields["角度"] == "产品" else ["mmw:lesson"]
            for label in labels:
                receipt["changed"] |= ensure_label(repo, label)
                saved()
            title = f"{fields['问题代号']}: {fields['发生了什么']}"
            if len(title) > 256:
                title = title[:255] + "…"
            printed = confirmed_write(["issue", "create", "--repo", repo, "--title", title,
                                         *[a for label in labels for a in ("--label", label)]], created, body)
            receipt["changed"] = True
            match = re.search(r"/issues/(\d+)", printed)
            if match:
                receipt["number"] = int(match[1])
            elif receipt["number"] is None and not created():
                raise RegistrationError("GitHub accepted issue creation but printed no number; find the problem code, then rerun")
            number = receipt["number"]
            saved()
        history = comments(repo, number)
        state = events.fold(history, issue=number)
        if state["unreadable"]:
            raise RegistrationError(f"#{number} has unreadable events; repair those comments before retrying")
        session = receipt["context"]["session"]
        duplicate = None
        if session != "none":
            for comment in history:
                what, payload = events.parse(comment["body"])
                if (what == "event" and payload["event"] == "lesson.seen"
                        and (payload["session"], payload["ticket"])
                        == (session, receipt["context"]["ticket"])):
                    duplicate = comment
                    break
        recorded = any(events.parse(c["body"])[0] == "event" and
                       events.parse(c["body"])[1].get("request") == receipt["request"]
                       for c in history)
        row = read_issue(repo, number)
        if "wontfix" in {l["name"] for l in row["labels"]}:
            plan.update(reopen=False, triage=False, note="")
        if plan["reopen"] and row["state"].lower() == "closed":
            confirmed_write(["issue", "reopen", str(number), "--repo", repo],
                            lambda: read_issue(repo, number)["state"].lower() == "open")
            receipt["changed"] = True
            saved()
        if plan["triage"] and "needs-triage" not in {l["name"] for l in row["labels"]}:
            receipt["changed"] |= ensure_label(repo, "needs-triage")
            saved()
            confirmed_write(["issue", "edit", str(number), "--repo", repo, "--add-label", "needs-triage"],
                            lambda: "needs-triage" in {l["name"] for l in read_issue(repo, number)["labels"]})
            receipt["changed"] = True
            saved()
        if not recorded and duplicate is None:
            comment = events.build("lesson.seen", line=f"登记 #{number}，在 {seen_in} 发现。{plan['note']}",
                                   lesson=number, seen_in=seen_in, source=source,
                                   request=receipt["request"], **receipt["context"])
            confirmed_write(["issue", "comment", str(number), "--repo", repo], occurrence_recorded, comment)
            receipt["changed"] = True
        pending.unlink()
        if plan["blocked_spec"] is not None:
            print(f"NOT REOPENED: #{number} sits under spec #{plan['blocked_spec']}, which has not finished")
        if duplicate is not None:
            link = duplicate.get("html_url") or f"https://github.com/{repo}/issues/{number}#issuecomment-{duplicate['id']}"
            print(f"ALREADY RECORDED: #{number} in {repo}, session {session}: {link}")
            return 0
        action = "REOPENED" if plan["reopen"] else receipt["action"]
        print(f"{action}: #{number} in {repo}")
        return 0
    except (RegistrationError, OSError, ValueError, KeyError, TypeError) as exc:
        partial = receipt["changed"] or isinstance(exc, UnconfirmedWrite)
        print(f"register: {repo}#{number or '?'} registration incomplete: {exc}; "
              "rerun the same command to finish missing writes", file=sys.stderr)
        return 1 if partial else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    search = sub.add_parser("find", help="search every open and closed issue in the target and MMW repositories")
    search.add_argument("words", nargs="+")
    search.add_argument("--repo", help="target owner/repo, default current repository")
    add = sub.add_parser("add", help="register a six-field ## Problem file")
    add.add_argument("file", type=Path)
    add.add_argument("--repo")
    add.add_argument("--ticket", type=int, help="originating ticket; read its parent spec")
    add.add_argument("--source", choices=events.LESSON_SOURCES, default="noticed")
    args = parser.parse_args(argv)
    if args.command == "add" and args.ticket is not None and args.ticket <= 0:
        parser.error("--ticket must be a positive issue number")
    try:
        toolbox = toolbox_repo()
        target = repository(args.repo) if args.repo else current_repo()
        repos = list(dict.fromkeys((target, toolbox)))
        if args.command == "find":
            return find(args.words, repos)
        return add_problem(args.file, args.source, target, repos, args.ticket)
    except (RegistrationError, statedir.LockHeld, events.EventError, OSError, ValueError, KeyError) as exc:
        print(f"register: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
