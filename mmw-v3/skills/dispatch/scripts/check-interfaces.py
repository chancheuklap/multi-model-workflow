#!/usr/bin/env python3
"""Check that the dispatcher's side and the agent's side of every role still meet.

    python3 check-interfaces.py

A session is started by a script and woken by the relay, so three things written in
three places have to agree, and nothing else notices when one of them moves:

1. **The playbook a start prompt names has a route.** `dispatch.sh` names the playbook
   of each session it starts (`WORKER_PLAYBOOK`, `REVIEWER_PLAYBOOK`); each has a route
   line in the mmw-mode skill's `## Playbooks`, and the file that line names exists. So do
   the orchestrator's playbooks, which the owner's session routes to itself.
2. **Every event that wakes someone is an event.** Each key of the relay's `WAKES`, and
   the slot wake `worker.queued`, is in `EVENTS` of the verify-ticket skill's `events.py`,
   the one table of what a ticket can carry.
3. **The session an event wakes has a step for it.** Each event `WAKES` sends to `main`,
   and `relay.recovered`, is named as `#<n> <event>` (or, for `relay.recovered`, by name)
   in every orchestrator playbook; each it sends to `worker`, and `worker.queued`, in the
   worker's playbook. And every `#<n> <event>` a playbook waits for is one the relay
   sends: a step that waits for anything else waits for ever.
4. **A worker put back on its ticket finds its step.** Each title in `RESUME_STEPS` of
   `verify-ticket.py`, which a `RESUME:` line names, is the bold title of a step in the
   worker's playbook.
5. **Only mmw-mode routes.** Which playbook a task runs, and which step comes next, is
   written once: in the route lines of the mmw-mode skill's `## Playbooks` and in the steps
   of its playbooks. A `SKILL.md` of any other skill with a `## Find your moment`,
   `## Reached from here` or `## Next` section, or a table whose first header is `You are`,
   routes a second time, and the second statement drifts from the first (the mmw-mode
   skill's `references/skill-set-rules.md` rule 7).
6. **Every agent has a row in the role table, and every row is used.** The dispatch
   skill's `roles.json` lists each role once. A `session` role has a default row in
   `hosts.json` (`defaults`), and nothing else does. A file a row names (a `lead` file,
   a `brief` template, a subagent `prompt`) exists, and so does a `lead` skill. Each
   sender in a row's `sent_by`, a skill or a playbook (`mmw-mode/playbooks/<name>.md`),
   exists and its text uses the role: `dispatch.sh brief <role>` for a session role, each
   prompt file's path for a subagent role. Every `dispatch.sh brief <role>` a `SKILL.md`
   or playbook writes names a `brief` role, and a `SKILL.md` or playbook that sends out a
   subagent is the `sent_by` of a subagent row.

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

# The playbooks of the session `open` or `open-ticket` makes the orchestrator. Nothing
# starts it with a start prompt: the owner's session routes to one of these itself.
ORCHESTRATOR_PLAYBOOKS = ("Run a night", "Run one ticket")

PLAYBOOK_VAR = re.compile(r'^([A-Z]+)_PLAYBOOK="([^"]+)"$', re.M)
ROUTE_LINE = re.compile(r"^- \*\*(.+?)\.\*\* .*`(playbooks/[a-z0-9-]+\.md)`\.?\s*$", re.M)
WAITED = re.compile(r"#<n> ([a-z]+\.[a-z]+)")
BRIEFED = re.compile(r"dispatch\.sh brief ([a-z-]+)")
SENDS_SUBAGENT = re.compile(r"\b(?:send|spawn|dispatch)\w*\s[^.\n]{0,40}\bsub-?agents?\b", re.I)
ROUTING = re.compile(r"^(## (?:Find your moment|Reached from here|Next)|\|\s*You are\s*\|)", re.M)


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
    """Rule 6: the role table against hosts.json, the files it names and the skills."""
    out: list[str] = []
    where = ROLES_JSON.relative_to(SKILLS)
    try:
        roles = json.loads(ROLES_JSON.read_text(encoding="utf-8"))["roles"]
        defaults = {row["agent"] for row in json.loads(HOSTS_JSON.read_text(encoding="utf-8"))["defaults"]}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f"{where}: the role table or hosts.json cannot be read: {exc}"]
    sessions = {r["name"] for r in roles if r.get("kind") == "session"}
    briefed = {r["name"] for r in roles if r.get("command") == "brief"}
    for name in sorted(sessions - defaults):
        out.append(f"{HOSTS_JSON.relative_to(SKILLS)}: the session role {name} has no row in "
                   f"`defaults`, so a fresh machine has no model for it")
    for name in sorted(defaults - sessions):
        out.append(f"{HOSTS_JSON.relative_to(SKILLS)}: `defaults` has a row for {name}, which "
                   f"is no session role in {where}")
    senders: dict[str, set[str]] = {}
    for role in roles:
        name = role.get("name")
        lead = role.get("lead") or {}
        files = [lead["file"]] if lead.get("file") else []
        files += list(role.get("brief") or []) + list(role.get("prompt") or [])
        for rel in files:
            if not (SKILLS / rel).is_file():
                out.append(f"{where}: {name} names {rel}, which does not exist")
        if lead.get("skill") and not (SKILLS / lead["skill"] / "SKILL.md").is_file():
            out.append(f"{where}: {name} leads with the {lead['skill']} skill, which does not exist")
        for skill in role.get("sent_by") or []:
            path = SKILLS / skill if skill.endswith(".md") else SKILLS / skill / "SKILL.md"
            if not path.is_file():
                out.append(f"{where}: {name} is sent by {skill}, which does not exist")
                continue
            text = path.read_text(encoding="utf-8")
            if role.get("kind") == "subagent":
                senders.setdefault(skill, set()).add(name)
                for rel in role.get("prompt") or []:
                    if rel.split("/", 1)[1] not in text:
                        out.append(f"{path.relative_to(SKILLS)}: sends the {name} subagent, and "
                                   f"never names its prompt {rel.split('/', 1)[1]}")
            elif f"dispatch.sh brief {name}" not in text:
                out.append(f"{path.relative_to(SKILLS)}: {where} says this skill starts the "
                           f"{name}, and it never writes `dispatch.sh brief {name}`")
    texts = sorted(SKILLS.glob("*/SKILL.md")) + sorted((MODE.parent / "playbooks").glob("*.md"))
    for path in texts:
        text = path.read_text(encoding="utf-8")
        for name in sorted(set(BRIEFED.findall(text)) - briefed - {"show", "close", "watch"}):
            out.append(f"{path.relative_to(SKILLS)}: `dispatch.sh brief {name}` names no `brief` "
                       f"role in {where}")
        sender = path.parent.name if path.name == "SKILL.md" else path.relative_to(SKILLS).as_posix()
        if path != MODE and SENDS_SUBAGENT.search(text) and sender not in senders:
            out.append(f"{path.relative_to(SKILLS)}: sends out a subagent, and no subagent row of "
                       f"{where} names this skill in `sent_by`; add the row, or start a session role "
                       f"with `dispatch.sh brief`")
    return out


def main() -> int:
    findings: list[str] = []
    mode = MODE.read_text(encoding="utf-8")
    routes = {name: rel for name, rel in ROUTE_LINE.findall(section(mode, "Playbooks"))}

    def playbook(name: str, why: str) -> Path | None:
        rel = routes.get(name)
        if rel is None:
            findings.append(f"{MODE.relative_to(SKILLS)}: `## Playbooks` has no route line for "
                            f"**{name}.**, which {why}; add one, or change what names it")
            return None
        path = MODE.parent / rel
        if not path.is_file():
            findings.append(f"{MODE.relative_to(SKILLS)}: the route line for **{name}.** names "
                            f"{rel}, which does not exist")
            return None
        return path

    started = dict((kind.lower(), name) for kind, name in
                   PLAYBOOK_VAR.findall(DISPATCH_SH.read_text(encoding="utf-8")))
    if "worker" not in started:
        findings.append(f"{DISPATCH_SH.relative_to(SKILLS)}: no WORKER_PLAYBOOK, so no worker start prompt names a playbook")
    if "reviewer" not in started:
        findings.append(f"{DISPATCH_SH.relative_to(SKILLS)}: no REVIEWER_PLAYBOOK, so no reviewer start prompt names a playbook")
    files = {kind: playbook(name, f"the {kind}'s start prompt in dispatch.sh names")
             for kind, name in started.items()}
    orchestrators = [playbook(name, "the orchestrator routes to") for name in ORCHESTRATOR_PLAYBOOKS]

    relay = module_constants(RELAY_PY)
    wakes = relay.get("WAKES")
    queued, recovered = relay.get("QUEUED"), relay.get("RECOVERED")
    main_role, worker_role = relay.get("MAIN"), relay.get("WORKER")
    if not isinstance(wakes, dict) or not all(isinstance(x, str) for x in (queued, recovered, main_role, worker_role)):
        findings.append(f"{RELAY_PY.relative_to(SKILLS)}: WAKES, QUEUED, RECOVERED, MAIN or WORKER is not a literal this check can read")
        print("\n".join(findings))
        return 1
    known = module_constants(EVENTS_PY).get("EVENTS")
    if not isinstance(known, dict):
        findings.append(f"{EVENTS_PY.relative_to(SKILLS)}: EVENTS is not a literal this check can read")
        known = {}
    for event in [*wakes, queued]:
        if known and event not in known:
            findings.append(f"{RELAY_PY.relative_to(SKILLS)}: {event} wakes a session, and "
                            f"{EVENTS_PY.relative_to(SKILLS)} EVENTS has no such event")

    def must_name(path: Path | None, events: list[str]) -> None:
        if path is None:
            return
        text = path.read_text(encoding="utf-8")
        for event in events:
            named = (event in text) if event == recovered else (f"#<n> {event}" in text)
            if not named:
                findings.append(f"{path.relative_to(SKILLS)}: the relay wakes this playbook's session "
                                f"with {'' if event == recovered else '#<n> '}{event}, and no step names it")

    to_main = [e for e, rule in wakes.items() if rule.get("to") == main_role] + [recovered]
    to_worker = [e for e, rule in wakes.items() if rule.get("to") == worker_role] + [queued]
    for path in orchestrators:
        must_name(path, to_main)
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

    sent = set(wakes) | {queued}
    for path in sorted((MODE.parent / "playbooks").glob("*.md")):
        for event in sorted(set(WAITED.findall(path.read_text(encoding="utf-8")))):
            if event not in sent:
                findings.append(f"{path.relative_to(SKILLS)}: a step waits for #<n> {event}, and the "
                                f"relay's WAKES sends no such wake")

    for path in sorted(SKILLS.glob("*/SKILL.md")):
        if path == MODE:
            continue
        for found in ROUTING.findall(path.read_text(encoding="utf-8")):
            what = "a table headed `You are`" if found.startswith("|") else f"`{found}`"
            findings.append(f"{path.relative_to(SKILLS)}: {what} routes its reader, and only the mmw-mode "
                            f"skill's route lines and playbooks route; move it into the playbook step that "
                            f"uses this skill")

    findings += check_roles()

    if findings:
        print("\n".join(findings))
        return 1
    print("INTERFACES OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
