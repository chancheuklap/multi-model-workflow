#!/usr/bin/env python3
"""Claude Code hook: put the ground rule that applies right now in front of the model.

Installed by mmw-v2/install.sh as ~/.claude/hooks/rule-at-moment.py and registered in
~/.claude/settings.json for PreToolUse, PostToolUse, PostToolUseFailure and Stop. One
invocation handles one event; the event name comes in on stdin (`hook_event_name`).

The text it injects is never written here. It is cut out of ~/.claude/CLAUDE.md
(override with MMW_CLAUDE_MD) by heading and by item number:

  "## Ground rules"          numbered items 1..6
  "## Subagent model"        the reason when an Agent call carries no model
  "## Before ending a turn"  the checklist a Stop block hands back

What each event gets:

  PreToolUse  Read                       rule 2, plus the file's line count, byte
                                         count and token estimate; with `offset`,
                                         how many lines remain
              Grep | WebFetch | Bash     rule 2
              Write | Edit | NotebookEdit rules 1, 3, 4, 6
              Agent                      rule 6; with no `model`, deny with the
                                         Subagent model section as the reason
  PostToolUse (any)                      when the result carries one of the host's
                                         own truncation markers: rule 2 plus the
                                         next Read call to make
  PostToolUseFailure (any)               rule 5 (plus the truncation check)
  Stop                                   when the turn used tools and this is the
                                         first block of the turn: block, reason =
                                         "Before ending a turn"

Anything unexpected — no CLAUDE.md, a heading missing, unreadable stdin — ends
in a silent exit 0: this hook only ever adds a note, it never breaks a call.
"""

import json
import os
import re
import sys
from pathlib import Path

HOST_READ_TOKEN_CAP = 25000
BYTES_PER_TOKEN = 3.5

TRUNCATED_VIEW = re.compile(r"showing lines (\d+)-(\d+) of (\d+) total")
OUTPUT_SAVED = re.compile(r"Output too large.*?saved to: ([^\s\"\\]+)", re.S)
TOKENS_EXCEEDED = re.compile(r"File content \((\d+) tokens\) exceeds maximum allowed tokens")


def load_rules():
    path = Path(os.environ.get("MMW_CLAUDE_MD") or Path.home() / ".claude/CLAUDE.md")
    text = path.read_text(encoding="utf-8")
    sections = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    sections = {k: "\n".join(v).strip() for k, v in sections.items()}
    ground = {}
    for line in sections.get("Ground rules", "").splitlines():
        m = re.match(r"(\d+)\.\s+(.*)", line.strip())
        if m:
            ground[int(m.group(1))] = m.group(2).strip()
    return sections, ground


def rules_text(ground, numbers):
    parts = [f"Ground rule {n}: {ground[n]}" for n in numbers if n in ground]
    return "\n".join(parts)


def measure(path):
    p = Path(path)
    size = p.stat().st_size
    lines = 0
    with p.open("rb") as fh:
        for _ in fh:
            lines += 1
    return size, lines, int(size / BYTES_PER_TOKEN)


def own_model_family(transcript_path):
    """The family of the model writing this session, read from the transcript."""
    try:
        last = None
        with open(transcript_path, encoding="utf-8") as fh:
            for line in fh:
                if '"model"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                m = (d.get("message") or {}).get("model")
                if m:
                    last = m
        return last
    except Exception:
        return None


def pre_tool_use(data, sections, ground):
    tool = data.get("tool_name", "")
    inp = data.get("tool_input") or {}
    out = {"hookEventName": "PreToolUse"}
    if tool == "Read":
        note = []
        path = inp.get("file_path")
        if path:
            try:
                size, lines, tokens = measure(path)
                note.append(f"`{path}`: {lines} lines, {size} bytes, about {tokens} tokens.")
                if tokens > HOST_READ_TOKEN_CAP:
                    note.append(f"The host returns at most about {HOST_READ_TOKEN_CAP} tokens per Read; this file needs consecutive chunks.")
                offset = inp.get("offset")
                if isinstance(offset, int) and offset > 0:
                    note.append(f"Reading from line {offset}; {max(lines - offset + 1, 0)} lines remain after it.")
            except OSError:
                pass
        note.append(rules_text(ground, [2]))
        out["additionalContext"] = "\n".join(note)
    elif tool in ("Grep", "WebFetch", "Bash"):
        out["additionalContext"] = rules_text(ground, [2])
    elif tool in ("Write", "Edit", "NotebookEdit"):
        target = inp.get("file_path") or inp.get("notebook_path") or ""
        head = f"About to write `{target}`." if target else "About to write."
        out["additionalContext"] = head + "\n" + rules_text(ground, [1, 3, 4, 6])
    elif tool == "Agent":
        kind = inp.get("subagent_type") or "general-purpose"
        model = inp.get("model")
        if kind == "general-purpose" and not model:
            out["permissionDecision"] = "deny"
            out["permissionDecisionReason"] = (
                "This Agent call carries no `model`, so it would run on the same model as you.\n"
                + sections.get("Subagent model", "")
            ).strip()
        else:
            note = [rules_text(ground, [6])]
            own = own_model_family(data.get("transcript_path", ""))
            if kind == "general-purpose" and model and own and model.lower() in own.lower():
                note.append("This subagent would run on the same model as you.\n" + sections.get("Subagent model", ""))
            out["additionalContext"] = "\n".join(note)
    else:
        return None
    return {"hookSpecificOutput": out}


def truncation_note(response_text):
    m = TRUNCATED_VIEW.search(response_text)
    if m:
        start, end, total = (int(x) for x in m.groups())
        if end < total:
            chunk = end - start + 1
            return (f"The host cut this Read at line {end} of {total}; {total - end} lines remain. "
                    f"Next call: Read the same file with offset={end + 1} limit={chunk}, and keep going until line {total}.")
        return None
    m = OUTPUT_SAVED.search(response_text)
    if m:
        return (f"The host cut this output and saved the whole of it to `{m.group(1)}`. "
                "Read that file to its last line (consecutive chunks if the size needs it) before using any of it.")
    m = TOKENS_EXCEEDED.search(response_text)
    if m:
        return (f"The host refused this Read: the file is about {m.group(1)} tokens, over the cap of {HOST_READ_TOKEN_CAP}. "
                "Read it in consecutive chunks: offset=1 with a limit that fits, then the next offset the reminder names.")
    return None


def response_text(data):
    for key in ("tool_response", "error", "tool_output"):
        if key in data:
            v = data[key]
            return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return ""


def post_tool_use(data, sections, ground, failed):
    notes = []
    cut = truncation_note(response_text(data))
    if cut:
        notes.append(cut)
        notes.append(rules_text(ground, [2]))
    if failed:
        notes.append(rules_text(ground, [5]))
    if not notes:
        return None
    return {"hookSpecificOutput": {
        "hookEventName": "PostToolUseFailure" if failed else "PostToolUse",
        "additionalContext": "\n".join(notes)}}


def turn_used_tools(transcript_path):
    """True when the assistant called a tool since the last human prompt."""
    try:
        with open(transcript_path, encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return False
    for line in reversed(lines):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        content = (d.get("message") or {}).get("content")
        if d.get("type") == "user":
            if isinstance(content, str):
                return False
            if isinstance(content, list) and not any(
                    isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
                return False
        elif d.get("type") == "assistant" and isinstance(content, list):
            if any(isinstance(b, dict) and b.get("type") == "tool_use" for b in content):
                return True
    return False


def stop(data, sections):
    if data.get("stop_hook_active"):
        return None
    if not turn_used_tools(data.get("transcript_path", "")):
        return None
    checklist = sections.get("Before ending a turn")
    if not checklist:
        return None
    return {"decision": "block", "reason": checklist}


def main():
    try:
        data = json.load(sys.stdin)
        sections, ground = load_rules()
        event = data.get("hook_event_name", "")
        if event == "PreToolUse":
            out = pre_tool_use(data, sections, ground)
        elif event == "PostToolUse":
            out = post_tool_use(data, sections, ground, failed=False)
        elif event == "PostToolUseFailure":
            out = post_tool_use(data, sections, ground, failed=True)
        elif event == "Stop":
            out = stop(data, sections)
        else:
            out = None
        if out:
            print(json.dumps(out, ensure_ascii=False))
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
