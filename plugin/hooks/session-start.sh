#!/usr/bin/env bash
# multi-model-workflow: SessionStart hook
# Injects behavioral override rules that must be active BEFORE any skill triggers.
# Must exit 0 — never block session startup.

cat <<'RULES'
[multi-model-workflow] Behavioral override active:
- When superpowers:writing-plans completes and suggests superpowers:subagent-driven-development, substitute multi-model-workflow:execute-plan instead.
- When superpowers:brainstorming completes and the user confirms direction, use superpowers:writing-plans to write design + plan yourself (you have the full brainstorming context) — do not dispatch a sub-agent.
RULES

exit 0
