#!/usr/bin/env python3
"""The shape every refusal in this pipeline takes.

A refusal that only says what went wrong invites an autonomous agent to improvise, and
improvisation is expensive and not reproducible. On 2026-09-05 three workers each got a
correct, honest "port held by another checkout" and each invented a different response:
one waited indefinitely, one built a retry loop, one killed the incumbent. The three
answers differed because nothing told them what to do.

So a refusal is three parts, in this order:

1. what happened, with a fact the reader can check (a pid, a path, a number);
2. why, in one clause;
3. what to do next — one command that can be pasted, or the sentence that says to report
   the ticket blocked and stop.

This file is the shape of one refusal message. Whether a gate should refuse at all,
and how to tell a gate that checked from a gate that said nothing, is
`docs/adr/0008-silence-is-never-a-pass.md` in the multi-model-workflow repository.

`REASON_LIMIT` is measured, not chosen: Grok Build clips a deny reason at 256 characters
and spends 13 of them on a prefix of its own (2026-08-29). Part 3 is the part that must
survive, so `refusal()` trims part 1 rather than part 3.
"""

from __future__ import annotations

REASON_LIMIT = 256

# The sentence a worker gets when there is no command that would help. It is the whole
# of part 3 on its own: an agent that reads it needs no other knowledge.
REPORT_BLOCKED = ("Report the ticket blocked and stop: do not wait, do not retry in a "
                  "loop, do not change the environment, do not touch another run.")


def refusal(what: str, why: str, next_step: str, limit: int = REASON_LIMIT) -> str:
    """The three parts joined, trimmed to `limit` from the front.

    `next_step` and `why` are kept whole; `what` gives up its tail first, because the
    reader can always look up a fact and cannot guess an instruction.
    """
    what, why, next_step = what.strip(), why.strip(), next_step.strip()
    if not next_step:
        raise ValueError("a refusal without a next step is not a refusal, it is a report")
    tail = f" {why} {next_step}" if why else f" {next_step}"
    room = limit - len(tail)
    if room < 1:
        # Nothing can be trimmed far enough; the caller wrote parts 2 and 3 too long.
        return (why + " " + next_step)[:limit].strip()
    if len(what) > room:
        what = what[: max(1, room - 1)].rstrip() + "…"
    return (what + tail).strip()


def within_limit(text: str, limit: int = REASON_LIMIT) -> bool:
    return len(text) <= limit
