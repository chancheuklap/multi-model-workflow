#!/usr/bin/env python3
"""Claude Code hook: put the ground rule that applies right now in front of the model.

Not installed by mmw-v2/install.sh. To use it, symlink it to ~/.claude/hooks/rule-at-moment.py
by hand and register `python3 '~/.claude/hooks/rule-at-moment.py'` in ~/.claude/settings.json
for PreToolUse (matcher `Read|Grep|WebFetch|Bash|Write|Edit|NotebookEdit|Agent`), PostToolUse
and PostToolUseFailure. One invocation handles one event; the event name comes in on stdin
(`hook_event_name`).

The text it injects is never written here. It is cut out of ~/.claude/CLAUDE.md
(override with MMW_CLAUDE_MD) by heading and by item number:

  "## Ground rules"          numbered items 1..7

What each event gets:

  PreToolUse  Read                       rule 2, plus the file's line count, byte
                                         count and token estimate; with `offset`,
                                         how many lines remain
              Grep | WebFetch | Bash     rule 2
              Write | Edit | NotebookEdit rules 1, 3, 4, 6, 7
              Agent                      rule 6
  PostToolUse (any)                      when the result carries one of the host's
                                         own truncation markers and the file that
                                         marker names is real: rule 2 plus the next
                                         Read call to make
  PostToolUseFailure (any)               rule 5, plus the truncation check and the
                                         token-cap refusal

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
TRUNCATED_PATH = re.compile(r"view\s+—\s+(\S+?):\s+showing lines")
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
        out["additionalContext"] = head + "\n" + rules_text(ground, [1, 3, 4, 6, 7])
    elif tool == "Agent":
        out["additionalContext"] = rules_text(ground, [6])
    else:
        return None
    return {"hookSpecificOutput": out}


def real_file(path, lines=None):
    """True when path is a file on disk with, where lines is given, that many lines."""
    p = Path(path)
    if not p.is_file():
        return False
    if lines is None:
        return True
    try:
        with p.open("rb") as fh:
            return sum(1 for _ in fh) == lines
    except OSError:
        return False


def truncation_note(response_text, failed):
    m = TRUNCATED_VIEW.search(response_text)
    if m:
        start, end, total = (int(x) for x in m.groups())
        named = TRUNCATED_PATH.search(response_text)
        if named and not real_file(named.group(1), total):
            return None
        if end < total:
            chunk = end - start + 1
            return (f"The host cut this Read at line {end} of {total}; {total - end} lines remain. "
                    f"Next call: Read the same file with offset={end + 1} limit={chunk}, and keep going until line {total}.")
        return None
    m = OUTPUT_SAVED.search(response_text)
    if m:
        if not real_file(m.group(1)):
            return None
        return (f"The host cut this output and saved the whole of it to `{m.group(1)}`. "
                "Read that file to its last line (consecutive chunks if the size needs it) before using any of it.")
    m = TOKENS_EXCEEDED.search(response_text) if failed else None
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
    cut = truncation_note(response_text(data), failed)
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
        else:
            out = None
        if out:
            print(json.dumps(out, ensure_ascii=False))
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
