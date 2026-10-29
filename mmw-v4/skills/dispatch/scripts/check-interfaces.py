#!/usr/bin/env python3
"""Check that the dispatcher's side and the agent's side of every role still meet.

    python3 check-interfaces.py

A session is started by a script and woken by the relay, so things written in several
places have to agree, and nothing else notices when one of them moves:

1. **Every event that wakes someone is an event.** Each key of the relay's `WAKES` is in
   `EVENTS` of the verify-ticket skill's `events.py`, the one table of what a ticket can
   carry.
2. **The session an event wakes has a step for it.** Each event `WAKES` sends to `main` is
   named in both orchestrators' playbooks: as `#<n> <event>` in One ticket, which handles one
   wake at a time, and as `` `<event>` `` in the wake table of Run a night. Each it sends to
   `worker` is named as `#<n> <event>` in the worker's (Work a ticket). And every `#<n> <event>` a playbook waits for
   is one the relay sends: a step that waits for anything else waits for ever.
3. **A worker put back on its ticket finds its step.** Each title in `RESUME_STEPS` of
   `verify-ticket.py`, which a `RESUME:` line names, is the bold title of a step in the
   worker's playbook.
4. **Only mmw-mode routes to a playbook.** Which playbook a task runs is written once: in
   the route lines of `## Playbooks` in the mmw-mode skill's `references/handling-a-request.md`. A `SKILL.md` of any other skill
   whose `## Find your moment`, `## Reached from here` or `## Next` section names a
   `playbooks/` file routes a second time, and the second statement drifts from the first.
   A moment table that sends its reader to the skill's own references is not a route.
5. **Every role has a default a fresh machine can start, and every role sent is a role.**
   Each role of the dispatch skill's `roles.json` has a `default` naming a host, a model and
   an effort, the host one `hosts.json` describes and the effort one that host lists. Every `dispatch.sh send <role>` (or `send <role>`) a `SKILL.md`, a
   playbook or the mmw-mode skill's `references/handling-a-request.md` writes names a role, or
   `worker`, which `send` resolves to the junior or senior worker by the ticket's grade. A
   role sent with a brief is sent by one of those files.
6. **Every session is told what it works by, and that file is there.** A start prompt
   carries `Read the mmw-mode skill in full, then follow <what>.`: for a role sent with a
   ticket, <what> is its `follows` in `roles.json`; for a role sent with a brief, the
   `--follow "<what>"` the sending step writes after `send <role>`. <what> is
   `the <skill> skill`, `the <skill> skill's <path>` or `the brief`, and the skill and the
   file must exist. A send of a brief role without `--follow` would start a session that
   has to guess its job.

It reads the files and parses Python with `ast`; it imports nothing it checks and writes
nothing. Exit 0 prints `INTERFACES OK`; exit 1 prints one finding per line, each naming
the file to change.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parents[1]
DISPATCH_SH = HERE / "dispatch.sh"
ROLES_JSON = HERE.parent / "roles.json"
HOSTS_JSON = HERE.parent / "hosts.json"
RELAY_PY = HERE / "relay.py"
EVENTS_PY = SKILLS / "verify-ticket" / "scripts" / "events.py"
VERIFY_PY = SKILLS / "verify-ticket" / "scripts" / "verify-ticket.py"
MODE = SKILLS / "mmw-mode" / "SKILL.md"
ROUTES = SKILLS / "mmw-mode" / "references" / "handling-a-request.md"

# The orchestrators' playbooks, which the owner's session routes to itself, each with how it
# names an event it is woken with. The worker's is the file its role follows in roles.json,
# which its start prompt names.
ORCHESTRATOR_PLAYBOOKS = {"Run a night": "`{event}`", "One ticket": "#<n> {event}"}

ROUTE_LINE = re.compile(r"^- \*\*(.+?)\.\*\* .*`(playbooks/[a-z0-9-]+\.md)`\.?\s*$", re.M)
WAITED = re.compile(r"#<n> ([a-z]+\.[a-z]+)")
SENT = re.compile(r"`(?:[^`\n]*dispatch\.sh )?send ([a-z][a-z-]*)")
FOLLOWED = re.compile(r'`(?:[^`\n]*dispatch\.sh )?send ([a-z][a-z-]*)( --follow "([^"`]+)")?')
FOLLOWS = re.compile(r"^the ([a-z0-9-]+) skill(?:'s (\S+?))?\.?$")
ROUTING = re.compile(r"^## (?:Find your moment|Reached from here|Next)\n(.*?)(?=^## |\Z)", re.M | re.S)


def section(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def module_constants(path: Path) -> dict[str, object]:
    """Every module-level `NAME = <literal>` and `NAME: T = <literal>` of a file, with the
    names of earlier such constants resolved inside a later literal."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: dict[str, object] = {}

    def value(node):
        if isinstance(node, ast.Name) and node.id in found:
            return found[node.id]
        if isinstance(node, ast.Dict):
            return {value(k): value(v) for k, v in zip(node.keys, node.values)}
        if isinstance(node, (ast.Tuple, ast.List)):
            return tuple(value(e) for e in node.elts)
        return ast.literal_eval(node)

    for node in tree.body:
        targets, rhs = [], None
        if isinstance(node, ast.Assign):
            targets, rhs = [t for t in node.targets if isinstance(t, ast.Name)], node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value:
            targets, rhs = [node.target], node.value
        for target in targets:
            try:
                found[target.id] = value(rhs)
            except (ValueError, TypeError, SyntaxError, KeyError):
                continue
    return found


def check_roles() -> list[str]:
    """Rule 5: each role's default against hosts.json, and every `dispatch.sh send` written."""
    out: list[str] = []
    where = ROLES_JSON.relative_to(SKILLS)
    try:
        roles = json.loads(ROLES_JSON.read_text(encoding="utf-8"))["roles"]
        hosts = json.loads(HOSTS_JSON.read_text(encoding="utf-8"))["hosts"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f"{where}: the role table or hosts.json cannot be read: {exc}"]
    names = {r["name"] for r in roles}
    for role in roles:
        if why := default_fault(role.get("default"), hosts):
            out.append(f"{where}: the {role['name']} role's `default` {why}, so a fresh machine "
                       f"has no session it can start for it")
    sent: set[str] = set()
    texts = sorted(SKILLS.glob("*/SKILL.md")) + sorted((MODE.parent / "playbooks").glob("*.md"))
    for path in texts + [ROUTES]:
        for name in sorted(set(SENT.findall(path.read_text(encoding="utf-8")))):
            sent.add(name)
            if name not in names | {"worker"}:
                out.append(f"{path.relative_to(SKILLS)}: `dispatch.sh send {name}` names no role "
                           f"in {where}")
    for role in roles:
        if role.get("sent_with") == "ticket":
            what = role.get("follows", "")
            why = resolve_follows(what) if what else "it has no `follows`"
            if why:
                out.append(f"{where}: the {role['name']} role's start prompt says what to follow, "
                           f"and {why}")
    brief_roles = {r["name"] for r in roles if r.get("sent_with") == "brief"}
    for path in sorted(SKILLS.glob("*/SKILL.md")) + sorted(SKILLS.glob("*/playbooks/*.md")) \
            + sorted(SKILLS.glob("*/references/*.md")):
        for name, flag, what in FOLLOWED.findall(path.read_text(encoding="utf-8")):
            if name not in brief_roles:
                continue
            if not flag:
                out.append(f"{path.relative_to(SKILLS)}: `send {name}` has no `--follow \"<what>\"`, "
                           f"so its session would have to guess what it works by")
            elif why := resolve_follows(what):
                out.append(f"{path.relative_to(SKILLS)}: `send {name} --follow`: {why}")
    for role in roles:
        if role.get("sent_with") == "brief" and role["name"] not in sent:
            out.append(f"{where}: {role['name']} is sent with a brief, and no SKILL.md, playbook or handling-a-request.md "
                       f"writes `dispatch.sh send {role['name']}`")
    return out


def default_fault(default: object, hosts: dict) -> str | None:
    """Why a role's `default` cannot start a session, or None when it can."""
    if not isinstance(default, dict):
        return "is missing; give it {\"host\", \"model\", \"effort\"}"
    blank = [k for k in ("host", "model", "effort")
             if not isinstance(default.get(k), str) or not default[k].strip()]
    if blank:
        return "has no " + ", ".join(blank)
    host = default["host"]
    if host not in hosts:
        return f"names host {host!r}, which hosts.json does not describe ({', '.join(sorted(hosts))})"
    efforts = hosts[host].get("efforts") or []
    if default["effort"] not in efforts:
        return f"names effort {default['effort']!r}, which host {host} does not list ({', '.join(efforts)})"
    return None


def resolve_follows(what: str) -> str | None:
    """Why <what> does not name a file that exists, or None when it does."""
    if what.rstrip(".") == "the brief":
        return None
    m = FOLLOWS.match(what)
    if not m:
        return (f'"{what}" is not `the <skill> skill`, `the <skill> skill\'s <path>` or '
                f'`the brief`')
    skill, rel = m.group(1), m.group(2)
    if not (SKILLS / skill / "SKILL.md").is_file():
        return f'"{what}" names the {skill} skill, which does not exist'
    if rel and not (SKILLS / skill / rel).is_file():
        return f'"{what}" names {rel} of the {skill} skill, which does not exist'
    return None


def worker_playbook_file(findings: list[str]) -> Path | None:
    """The file the worker roles follow, from roles.json, for the wake and RESUME checks."""
    try:
        roles = json.loads(ROLES_JSON.read_text(encoding="utf-8"))["roles"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    what = next((r.get("follows", "") for r in roles if r.get("name") == "junior-worker"), "")
    m = FOLLOWS.match(what)
    if not m or not m.group(2) or resolve_follows(what):
        return None
    return SKILLS / m.group(1) / m.group(2)


def main() -> int:
    findings: list[str] = []
    owning = ROUTES.read_text(encoding="utf-8")
    routes = {name: rel for name, rel in ROUTE_LINE.findall(section(owning, "Playbooks"))}

    def playbook(name: str, why: str) -> Path | None:
        rel = routes.get(name)
        if rel is None:
            findings.append(f"{ROUTES.relative_to(SKILLS)}: `## Playbooks` has no route line for "
                            f"**{name}.**, which {why}; add one, or change what names it")
            return None
        path = MODE.parent / rel
        if not path.is_file():
            findings.append(f"{ROUTES.relative_to(SKILLS)}: the route line for **{name}.** names "
                            f"{rel}, which does not exist")
            return None
        return path

    files = {"worker": worker_playbook_file(findings)}
    orchestrators = [(playbook(name, "the orchestrator routes to"), form)
                     for name, form in ORCHESTRATOR_PLAYBOOKS.items()]

    relay = module_constants(RELAY_PY)
    wakes = relay.get("WAKES")
    main_role, worker_role = relay.get("MAIN"), relay.get("WORKER")
    if not isinstance(wakes, dict) or not all(isinstance(x, str) for x in (main_role, worker_role)):
        findings.append(f"{RELAY_PY.relative_to(SKILLS)}: WAKES, MAIN or WORKER is not a literal this check can read")
        print("\n".join(findings))
        return 1
    known = module_constants(EVENTS_PY).get("EVENTS")
    if not isinstance(known, dict):
        findings.append(f"{EVENTS_PY.relative_to(SKILLS)}: EVENTS is not a literal this check can read")
        known = {}
    for event in wakes:
        if known and event not in known:
            findings.append(f"{RELAY_PY.relative_to(SKILLS)}: {event} wakes a session, and "
                            f"{EVENTS_PY.relative_to(SKILLS)} EVENTS has no such event")

    def must_name(path: Path | None, events: list[str], form: str = "#<n> {event}") -> None:
        if path is None:
            return
        text = path.read_text(encoding="utf-8")
        for event in events:
            if form.format(event=event) not in text:
                findings.append(f"{path.relative_to(SKILLS)}: the relay wakes this playbook's session "
                                f"with #<n> {event}, and no step names it as {form.format(event=event)}")

    to_main = [e for e, rule in wakes.items() if rule.get("to") == main_role]
    to_worker = [e for e, rule in wakes.items() if rule.get("to") == worker_role]
    for path, form in orchestrators:
        must_name(path, to_main, form)
    must_name(files.get("worker"), to_worker)

    steps = module_constants(VERIFY_PY).get("RESUME_STEPS")
    worker_playbook = files.get("worker")
    if not isinstance(steps, tuple):
        findings.append(f"{VERIFY_PY.relative_to(SKILLS)}: RESUME_STEPS is not a literal this check can read")
    elif worker_playbook is not None:
        text = worker_playbook.read_text(encoding="utf-8")
        for title in steps:
            if not re.search(rf"^\s*\d+\. \*\*{re.escape(title)}\.\*\*", text, re.M):
                findings.append(f"{worker_playbook.relative_to(SKILLS)}: a RESUME: line can name the step "
                                f"**{title}.**, and no step has that title")

    sent = set(wakes)
    for path in sorted((MODE.parent / "playbooks").glob("*.md")):
        for event in sorted(set(WAITED.findall(path.read_text(encoding="utf-8")))):
            if event not in sent:
                findings.append(f"{path.relative_to(SKILLS)}: a step waits for #<n> {event}, and the "
                                f"relay's WAKES sends no such wake")

    for path in sorted(SKILLS.glob("*/SKILL.md")):
        if path == MODE:
            continue
        for body in ROUTING.findall(path.read_text(encoding="utf-8")):
            if "playbooks/" in body:
                findings.append(f"{path.relative_to(SKILLS)}: a moment section names a playbook file, and "
                                f"only the mmw-mode skill's route lines route to a playbook; name the "
                                f"playbook by its title, or move the row into the playbook step that "
                                f"uses this skill")

    findings += check_roles()

    if findings:
        print("\n".join(findings))
        return 1
    print("INTERFACES OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
