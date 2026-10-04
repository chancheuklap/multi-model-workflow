# scripts/: how a script is written

Read `../../README.md` first: it holds the method every component follows. This file covers the programs in a skill's `scripts/` directory. It applies to this directory, which belongs to the mode, and to the `scripts/` directory of any other skill.

The models to imitate: `mmw-v3/upstream-pstack/skills/poteto-mode/scripts/worktree-audit.sh` (a small read-only program) and `mmw-v3/upstream-pstack/skills/poteto-mode/scripts/orch/` (a larger one with tests).

## What a script is for

The part of the work that comes out the same every time and that a program can do or check. The agent runs it and reads its output; judgement stays with the agent.

## When a new script is warranted

- **An instruction is about to be written a second time** (`principle-encode-lessons-in-structure`): "If the fix is structural, only use the structural fix. The instruction is the symptom."
- **The work is not done at a glance** (`principle-build-the-lever`): "The tool is the artifact a reviewer can rerun."
- **A repeated mistake can be made impossible** (the `correct` skill's order: architecture, then types, then a lint or CI check whose error names the fix, then a test; prose last). A check is proven by making it fail on a real past mistake.
- **Not for a decision that needs judgement.** That stays in prose: written prominently, with an example of the failure.

In the same change: the step or trigger that runs it gives the exact command.

## The shape of the file

- A header comment: what the program does, and what it never does ("Never deletes anything; deletion stays a human-gated step in the playbook").
- Ordinary code under `CODING_STANDARDS.md` at the repository root.
- Tests beside the larger programs.

## Sources in MMW v2

v2's programs already follow "scripts are tools; judgement belongs to the main agent" (ADR `0009`): `dispatch.sh`, `relay.py`, `watchdog.py`, `turn-guard.py`, `tool-guard.py`, `verify-ticket.py` and the rest. A rule that one of them already enforces is not written again as prose; the mode or a playbook names the program in one line at most.
