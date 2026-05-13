#!/usr/bin/env bash
# multi-model-workflow: SessionStart hook
# Injects behavioral override rules + active plan detection.
# Must exit 0 — never block session startup.

# ── Behavioral override (always active) ──────────────────────────
# This rule must be in the main session's context BEFORE any skill triggers.
# The skill description handles "when user explicitly says execute the plan";
# this hook handles the implicit handoff that happens mid-workflow.

cat <<'RULES'
[multi-model-workflow] Behavioral override active:
- When superpowers:writing-plans completes and suggests superpowers:subagent-driven-development, substitute multi-model-workflow:execute-plan instead.
- When superpowers:brainstorming completes and the user confirms direction, dispatch plan-architect (via Agent tool) to write design + plan — do not write the plan yourself.
RULES

# ── Active plan detection ────────────────────────────────────────
PLAN_DIR="docs/superpowers/plans"
if [ -d "$PLAN_DIR" ]; then
    PLANS=$(find "$PLAN_DIR" -name "*.md" -type f 2>/dev/null | sort -r)
    if [ -n "$PLANS" ]; then
        # Check for unchecked tasks (active plans)
        HAS_UNCHECKED=false
        for p in $PLANS; do
            if grep -q '^\s*- \[ \]' "$p" 2>/dev/null; then
                HAS_UNCHECKED=true
                break
            fi
        done

        if [ "$HAS_UNCHECKED" = true ]; then
            echo ""
            echo "[multi-model-workflow] Unfinished plan detected:"
            for p in $PLANS; do
                UNCHECKED=$(grep -c '^\s*- \[ \]' "$p" 2>/dev/null || echo 0)
                CHECKED=$(grep -c '^\s*- \[x\]' "$p" 2>/dev/null || echo 0)
                if [ "$UNCHECKED" -gt 0 ]; then
                    TITLE=$(grep -m1 '^#' "$p" 2>/dev/null | sed 's/^#\+ //')
                    echo "  - $p (${CHECKED} done / ${UNCHECKED} remaining)${TITLE:+ — $TITLE}"
                fi
            done
            echo ""
            echo "Invoke multi-model-workflow:execute-plan to continue implementation."
        fi
    fi
fi

exit 0
