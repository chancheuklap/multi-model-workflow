# Plan: Restructure multi-model-workflow Plugin — Split orchestrate-workflow into Focused Skills

## Context

`orchestrate-workflow` is a 129-line god skill with 9 reference files that handles everything from entry-gate routing through Phase A/B/C execution, repair disposition, review dispatch, worktree management, and business reporting. During an end-to-end simulation of the Formal Orchestrate flow, 6 structural issues emerged:

1. **F1** — Review budget is a document, not an enforced counter
2. **F2** — Worktree merge conflicts have no protocol (who commits, who resolves, who cleans up)
3. **F3** — Review prompts grow monolithic because one skill owns all phases
4. **F4** — Final Review pure delta approach misses regression and cross-pack failures; needs augmented coverage
5. **F5** — `contract-boundary.md` contains AgentFlow-specific anchors (JSONB registry, Alembic trees, etc.)
6. **F6** — No detection of missing `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` environment variable

The user's directive: split `orchestrate-workflow` into focused skills chained like Superpowers (brainstorming → writing-plans → subagent-driven-development → finishing-a-development-branch), then fix all 6 issues within the new architecture.

## Before / After Skill Inventory

### Before (3 skills, 1 god)

```
orchestrate-discovery/         — Discovery phase (self-contained, good)
orchestrate-plan-writing/      — Plan writing (self-contained, good)
orchestrate-workflow/           — GOD SKILL: entry gate + Phase 0a + Phase 0b + Phase A + Phase B + Phase C + repair + review dispatch + budget + worktree + git
  references/ (9 files)
```

### After (8 workflow skills + shared references)

```
orchestrate-workflow/           — SLIM entry gate + Hard Gates + Resume Gate + 禁止 list + Git Checkpoint
orchestrate-discovery/          — Discovery phase (exists, minor update: add handoff verdict output)
orchestrate-design-review/      — Phase 0a: 2 Codex design reviews + disposition
orchestrate-plan-writing/       — Plan writing (exists, minor update: add handoff verdict output)
orchestrate-plan-review/        — Phase 0b: 3 Codex plan reviews + disposition
orchestrate-execution/          — Phase A: per-pack worker dispatch + pack review loop + worktree merge protocol
orchestrate-final-review/       — Phase B + C: augmented review (regression sweep + full intent coverage + cross-pack audit) + business report + branch finishing
orchestrate-direct-repair/      — Direct Repair: targeted fix + graded review
```

Each skill is self-contained with its own `references/` directory. Cross-cutting content (dispatch primitives, contract boundary, review budget, custom agents table, routing vocabulary) lives in `plugin/references/`. Each skill's SKILL.md declares which shared references it needs in a `## Shared References` section; the coordinator loads them on-demand when entering that skill, not eagerly at session start. This preserves the progressive loading established in commit `d9037c4`.

## Skill Chain and Handoff Rules

```
User input
    ↓
orchestrate-workflow (entry gate + Hard Gates + Resume Gate)
    ├─ Answer-only → respond, stop
    ├─ One-shot Review → review per user request, stop
    ├─ Direct Repair → orchestrate-direct-repair
    ├─ User Decision → ask one question, stop
    └─ Formal Orchestrate ↓
        ↓
orchestrate-discovery
    ↓ verdict: DISCOVERY_READY / DISCOVERY_NOT_NEEDED
orchestrate-design-review (Phase 0a)
    ↓ pass
[to-issues if needed] → orchestrate-plan-writing
    ↓ verdict: PLAN_CREATED
orchestrate-plan-review (Phase 0b)
    ↓ pass
orchestrate-execution (Phase A)
    ↓ all packs pass
orchestrate-final-review (Phase B + C)
    ↓ pass → business report → branch finishing → done

Backflow at any point:
  design/domain/UX gap → orchestrate-discovery
  issue gap → to-issues
  plan gap → orchestrate-plan-writing
  implementation gap from Phase B → orchestrate-execution

Upstream skill routing (via coordinator-tools.md Routing Vocabulary, not session-start):
  terminology / domain conflict → grill-with-docs
  missing feedback loop / reproduction → diagnose
  module map / call chain needed → zoom-out
  interface shape / UI direction proof → prototype
  bad seam / repeated repair → improve-codebase-architecture
  issue ready state unclear → triage
```

Chaining is driven by `session-start.sh` behavioral override rules for the orchestrate chain. Upstream skill routing is driven by `coordinator-tools.md` Routing Vocabulary, which each orchestrate skill loads on-demand. Each skill outputs a structured verdict; the coordinator reads it and invokes the next skill per the applicable rules.

## New Directory Layout

```
plugin/
├── .claude-plugin/plugin.json            (bump version 0.7.0 → 0.8.0)
├── agents/
│   ├── pack-executor.md                  (UPDATE: add "no git commit/merge/push" rule)
│   ├── complex-pack-executor.md          (UPDATE: same commit prohibition)
│   ├── root-cause-analyst.md             (unchanged)
│   ├── code-explorer.md                  (unchanged)
│   ├── complex-code-explorer.md          (unchanged)
│   └── docs-worker.md                    (unchanged)
├── hooks/
│   ├── hooks.json                        (UPDATE: add SubagentStop for codex:codex-rescue budget tracking)
│   ├── session-start.sh                  (REWRITE: new chaining rules + shared ref loading + env check)
│   └── track-review-budget.sh            (NEW: increment budget counter on codex:codex-rescue stop)
├── scripts/
│   └── guard-premature-push.sh           (unchanged)
├── references/                           (NEW: shared cross-cutting references)
│   ├── dispatch-primitives.md            (MOVED from orchestrate-workflow/references/, unchanged)
│   ├── contract-boundary.md              (MOVED + CLEANED: remove AgentFlow-specific anchors)
│   ├── review-budget.md                  (MOVED, formula unchanged; add budget lifecycle + env var propagation)
│   ├── coordinator-tools.md              (MOVED, trimmed: handoff status → session-start for orchestrate chain; KEEP full Routing Vocabulary including upstream skills + Upstream Skill 调用 table + durable brief + direction check)
│   └── custom-agents.md                  (NEW: extracted agents table + communication architecture)
├── skills/
│   ├── orchestrate-workflow/             (SLIMMED: entry gate + global constraints)
│   │   └── SKILL.md                      (~60 lines: entry gate table + Resume Gate + scope template + git checkpoint + Hard Gates + 禁止 list; Hard Gates and 禁止 also in session-start.sh as compaction-durable layer)
│   ├── orchestrate-discovery/            (EXISTS, minor update)
│   │   ├── references/
│   │   │   ├── design-document-contract.md
│   │   │   ├── discovery-checklist.md
│   │   │   └── discovery-input.md
│   │   └── SKILL.md
│   ├── orchestrate-design-review/        (NEW: Phase 0a)
│   │   ├── references/
│   │   │   └── design-review-angles.md   (content from old design-review.md)
│   │   └── SKILL.md
│   ├── orchestrate-plan-writing/         (EXISTS, minor update)
│   │   ├── references/
│   │   │   ├── plan-contract.md
│   │   │   └── plan-checklist.md
│   │   └── SKILL.md
│   ├── orchestrate-plan-review/          (NEW: Phase 0b)
│   │   ├── references/
│   │   │   └── plan-review-angles.md     (content from old plan-review.md)
│   │   └── SKILL.md
│   ├── orchestrate-execution/            (NEW: Phase A)
│   │   ├── references/
│   │   │   ├── pack-dispatch.md          (worker dispatch rules, extracted from old phase-a.md)
│   │   │   ├── pack-review.md            (per-pack codex review, extracted from old phase-a.md)
│   │   │   └── worktree-merge.md         (NEW: F2 merge conflict protocol)
│   │   └── SKILL.md
│   ├── orchestrate-final-review/         (NEW: Phase B + C)
│   │   ├── references/
│   │   │   ├── final-review-angles.md    (AUGMENTED: regression sweep + full intent coverage + cross-pack audit; preserves pack review deference)
│   │   │   └── business-report.md        (Phase C finishing, extracted from old final-review.md)
│   │   └── SKILL.md
│   └── orchestrate-direct-repair/        (NEW: extracted from orchestrate-workflow)
│       ├── references/
│       │   └── repair-grading.md         (content from old direct-repair.md)
│       └── SKILL.md
```

Files deleted after move:
- `skills/orchestrate-workflow/references/design-review.md` → content moved to `orchestrate-design-review/references/`
- `skills/orchestrate-workflow/references/plan-review.md` → content moved to `orchestrate-plan-review/references/`
- `skills/orchestrate-workflow/references/phase-a.md` → content split into `orchestrate-execution/references/`
- `skills/orchestrate-workflow/references/final-review.md` → content rewritten in `orchestrate-final-review/references/`
- `skills/orchestrate-workflow/references/direct-repair.md` → content moved to `orchestrate-direct-repair/references/`
- `skills/orchestrate-workflow/references/contract-boundary.md` → cleaned and moved to `plugin/references/`
- `skills/orchestrate-workflow/references/review-budget.md` → moved to `plugin/references/`
- `skills/orchestrate-workflow/references/coordinator-tools.md` → moved to `plugin/references/`
- `skills/orchestrate-workflow/references/dispatch-primitives.md` → moved to `plugin/references/`

## Finding Fixes in New Architecture

### F1: Hook-based Review Budget Counter

**Mechanism**: SubagentStop hook on `codex:codex-rescue` runs `track-review-budget.sh`, which increments a counter in `.claude/multi-model-workflow/budget-<run_id>.json`.

**Run ID**: Established when `orchestrate-workflow` entry gate selects Formal Orchestrate. The entry gate creates a budget file at `.claude/multi-model-workflow/budget-<run_id>.json` with a unique ID (timestamp-based, e.g., `formal-20260518-143022`).

**Run ID discovery** (solves cross-call propagation):

Environment variables don't persist across Bash calls in Claude Code. Instead, use an **active-run-id file**:

1. Entry gate creates `.claude/multi-model-workflow/budget-formal-20260518-143022.json` and writes `.claude/multi-model-workflow/active-run-id` containing the run ID.
2. `track-review-budget.sh` reads `active-run-id` to find the budget file path.
3. Each review skill also reads `active-run-id` to locate the budget file.
4. **Stale detection**: Entry gate checks if `active-run-id` points to a budget file updated within the last hour. If stale (>1h no update): overwrite. If fresh: warn user and ask before overwriting (likely another session or aborted run).

Single-active-run design. Parallel Formal Orchestrate runs are out of scope.

**Budget file schema**:
```json
{
  "run_id": "formal-20260518-143022",
  "budget_total": 24,
  "budget_used": 0,
  "pack_count": 4,
  "dispatches": []
}
```

**Budget file lifecycle**:
- **Created**: by `orchestrate-workflow` entry gate when Formal Orchestrate is selected.
- **Updated**: by `track-review-budget.sh` on each `codex:codex-rescue` SubagentStop; by `orchestrate-plan-review` when pack count is confirmed (updates `budget_total` and `pack_count`).
- **Deleted**: by `orchestrate-final-review` Phase C finishing (success path), or by coordinator when user explicitly aborts. Also deletes `active-run-id` and `scope-<run_id>.md`. Stale files (>1h no update) are cleaned by entry gate on next run.
- **Concurrency**: single-active-run with stale detection. Not designed for parallel Formal Orchestrate runs.

**Scope Contract persistence**:

Entry gate also writes `.claude/multi-model-workflow/scope-<run_id>.md` containing the Scope Contract (source artifacts, editable artifacts, read-only context, out of scope, issue recording target). This file serves one purpose: after context compaction, session-start.sh re-injects the "confirm Scope Contract is still current" rule, and the coordinator can re-read the persisted scope to verify it hasn't drifted — without needing the original entry gate context. Updated whenever scope changes (e.g., plan review adds packs, backflow changes source). Cleaned up with the budget file at Phase C finishing.

**Flow**:
1. `orchestrate-workflow` entry gate creates budget file with `budget_total = 2N + 16` (N = pack count from plan, or 0 if not yet known; updated by `orchestrate-plan-review` when pack count is confirmed). Writes `active-run-id`.
2. Each review skill reads `active-run-id` → opens budget file → checks budget. If `budget_used >= 0.8 * budget_total`, skill does a Direction Check before proceeding.
3. `track-review-budget.sh` (SubagentStop on `codex:codex-rescue`) reads `active-run-id` → increments `budget_used` and appends dispatch record.
4. At 100% budget, review skills stop and report to user.

**Hook matcher note**: Current `hooks.json` uses non-namespaced matchers (`pack-executor|complex-pack-executor`). Before implementation, verify that SubagentStop matcher supports the colon-namespaced format `codex:codex-rescue`. If not, use the non-namespaced form `codex-rescue` or whatever the hook system resolves to. Test this in Pack 2 step 16 before wiring up the budget counter.

**hooks.json addition**:
```json
{
  "matcher": "codex:codex-rescue",
  "hooks": [{
    "type": "command",
    "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/track-review-budget.sh\"",
    "timeout": 5
  }]
}
```

### F2: Worktree Merge Conflict Protocol

Lives in `orchestrate-execution/references/worktree-merge.md`. Key rules:

1. **Worker cannot commit.** `pack-executor.md` and `complex-pack-executor.md` get explicit rule: "Do not run git commit, git merge, or git push. Leave all changes unstaged. The coordinator will commit after review."
2. **Test failure → return to original worker.** SendMessage the worker inside its worktree with the failure details. Worker fixes and re-runs tests. If SendMessage unavailable, create new agent in the same worktree.
3. **Coordinator commits after pack review pass.** Coordinator enters the worktree directory, stages relevant files, commits with pack-scoped message.
4. **Coordinator merges worktree into main branch.** `git merge --no-ff <worktree-branch>`. If conflict: coordinator resolves (it has full context of all packs). Never ask the worker to resolve cross-pack conflicts.
5. **Coordinator cleans up worktree.** `git worktree remove <path>` after successful merge. Failed/abandoned worktrees also cleaned by coordinator.

### F3: Review Prompt Size (Solved by Architecture)

Each review skill now owns exactly one review phase:
- `orchestrate-design-review`: only design review angles (2 reviewers)
- `orchestrate-plan-review`: only plan review angles (3 reviewers)
- `orchestrate-execution`: only per-pack review (1 reviewer per pack)
- `orchestrate-final-review`: only final review angles (2 reviewers + optional release gate)

Prompts are naturally scoped because the skill's SKILL.md and references only contain its own phase's context. No more monolithic prompt assembled from 9 reference files.

### F4: Final Review = Augmented Delta (Not Pure Delta, Not Full Reversal)

**Problem**: Current `final-review.md` lines 14-23 take a pure delta approach: "Final Review does NOT re-audit what Pack Reviews already verified." This under-catches regression and cross-pack integration failures — pack reviews each see one slice, nobody sees the whole picture.

**Solution**: Augment the delta strategy instead of reversing it. Pack Reviews retain full value as per-pack quality gates. Final Review adds three layers that Pack Reviews structurally cannot provide:

New `orchestrate-final-review/references/final-review-angles.md` will:

1. **Regression sweep** (NEW): Read the FULL diff from starting commit. Run the full test suite. Check whether any pack's changes break another pack's behavior or existing functionality. This is the "fresh eyes on everything" layer.
2. **Design intent coverage** (AUGMENTED): Walk every verifiable intent from the design doc. For intents already verified by Pack Review, confirm the verification evidence is still valid post-merge (a 1-line check, not a re-audit). For intents that fall between packs (gap intents), do full verification.
3. **Cross-pack audit** (KEPT): Shared contract surface, migration ordering, import cycles, state races — unchanged from current design.

What Final Review does NOT do:
- Re-audit single-pack behavior that Pack Review already verified and that regression sweep confirms is intact
- Re-check helper placement, naming, or code quality within a single pack's owned files

**Pack Review residual value**: Pack Reviews remain the primary quality gate. They catch spec compliance and code quality issues at the smallest feedback loop. Final Review trusts their per-pack verdicts but verifies the composition is sound.

**Budget impact**: Formula stays `2N + 16`. Regression sweep adds prompt size (full diff) but not dispatch count. Direction Check may trigger more often for large changes, which is appropriate.

### F5: Clean contract-boundary.md

Move to `plugin/references/contract-boundary.md`. Remove the "AgentFlow Anchors" section (lines 39-48) which contains project-specific content:
- `src/shared/contracts/*.py` paths
- `JSONB_COLUMN_REGISTRY` / `LOCAL_JSON_COLUMN_REGISTRY`
- `migrations/gateway/versions` / `migrations/collection/versions`
- `src/shared/ports.py` / `scripts/dev/common/command_contract.py`
- Billing catalog references
- Local Agent Pydantic response rules
- `agents.overrides.md` directory rules

Keep the generic sections:
- Boundary Types (8 types — these are universal)
- Contract Anchors template (generic fields)
- Forbidden Shortcuts (universal anti-patterns, remove AgentFlow-specific examples)

Project-specific anchors belong in the project's own `CLAUDE.md` / `AGENTS.override.md`, not in the plugin.

### F6: SessionStart Detects Missing Environment Variable

Add to `session-start.sh`:
```bash
if [ -z "${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-}" ]; then
  echo "[multi-model-workflow] WARNING: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS is not set." >&2
  echo "  SendMessage to existing agents will not work. All repairs will require new agent spawns." >&2
  echo "  Set CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 for optimal multi-agent coordination." >&2
fi
```

This warns but does not block — the plugin still functions with new-agent-per-repair fallback.

### Content Rehoming Inventory (Slim Entry Gate)

Current `orchestrate-workflow/SKILL.md` contains sections that must survive the slim. Target locations:

| Content | Current Location | Target |
|---|---|---|
| Entry Gate table | SKILL.md lines 37-44 | KEEP in slim `orchestrate-workflow/SKILL.md`; add mid-stream entry: when user references existing artifact (design/plan/diff), identify latest passed phase from artifact state and route directly to next phase skill |
| Resume Gate | SKILL.md line 24 | KEEP in slim `orchestrate-workflow/SKILL.md`; two modes: (1) within-conversation resume from last passed gate, (2) cross-conversation resume by inspecting artifact state (design exists → Phase 0a; plan exists + Phase 0a passed → Phase 0b; packs partially done → Phase A continue) |
| Scope template (Step 3) | SKILL.md lines 25-31 | KEEP in slim `orchestrate-workflow/SKILL.md` |
| Git Checkpoint | SKILL.md lines 115-120 | KEEP in slim `orchestrate-workflow/SKILL.md` |
| Hard Gates | SKILL.md lines 107-113 | KEEP in slim `orchestrate-workflow/SKILL.md` |
| 禁止 list | SKILL.md lines 122-128 | KEEP in slim `orchestrate-workflow/SKILL.md` |
| Reference Map | SKILL.md lines 54-66 | REMOVE — replaced by session-start chaining rules + each skill's own SKILL.md |
| Custom Agents table | SKILL.md lines 69-79 | MOVE to `plugin/references/custom-agents.md` |
| 通信架构 table | SKILL.md lines 81-93 | MOVE to `plugin/references/custom-agents.md` (same file — agents + how they communicate) |
| 修复分流规则 | SKILL.md lines 96-104 | REMOVE from SKILL.md — `dispatch-primitives.md` is the single source of truth; phase-a.md and other references reference it, don't duplicate |
| Formal Orchestrate 流程 | SKILL.md lines 47-49 | REMOVE — replaced by session-start chaining rules |
| 调度方式 | SKILL.md lines 12-17 | MOVE to `plugin/references/dispatch-primitives.md` preamble |

**修复分流 single source of truth**: Currently duplicated across SKILL.md (lines 96-104), `phase-a.md` (lines 97-107), and `dispatch-primitives.md` (lines 82-100). After restructure, `dispatch-primitives.md` is the sole authority. `orchestrate-execution/SKILL.md` and other phase skills reference it; no inline copies.

### Shared Reference Loading (Inline, Not Declarative)

Claude Code skills don't have a declarative "needs these refs" mechanism — the coordinator reads files when instructions tell it to. Instead of a formal `## Shared References` section in every SKILL.md, each skill's prose says "before dispatching review, read `${CLAUDE_PLUGIN_ROOT}/references/dispatch-primitives.md`" inline at the point of use.

General pattern:
- Skills that dispatch reviewers mention `dispatch-primitives.md` + `review-budget.md` at their dispatch step
- Skills that dispatch workers (`orchestrate-execution`, `orchestrate-direct-repair`, repair routing in any phase) mention `custom-agents.md` at their worker selection step + `contract-boundary.md` when contract boundary is touched
- Skills that route to other phases or upstream skills mention `coordinator-tools.md` at their reception/routing step
- Discovery and plan-writing are self-contained and don't reference shared files

## Within-Skill Progressive Loading (SKILL.md as Flow Controller)

Each phase skill's SKILL.md is a numbered flow controller, not a flat description. It tells the coordinator which local reference to load at which step — references that aren't needed yet stay unread. This is the second level of progressive loading (first level: across skills, only load the phase skill you need; second level: within a skill, only load the reference you need at the current step).

### orchestrate-workflow (entry gate)

```
Step 1: Entry Gate classification (Answer-only / One-shot Review / Direct Repair / Formal Orchestrate / User Decision).
Step 2: Resume Gate — within-conversation: resume from last passed gate;
        cross-conversation: inspect artifact state (design exists → Phase 0a; plan + Phase 0a passed → Phase 0b; etc.).
Step 3: Write Scope Contract (source artifacts / editable artifacts / read-only context / out of scope / issue recording target).
        Persist Scope Contract to .claude/multi-model-workflow/scope-<run_id>.md for compaction recovery.
Step 4: Git Checkpoint — git status; create work branch if on main; identify scope-owned vs other dirty files.
Step 5: For Formal Orchestrate: create budget file + active-run-id (F1). Dispatch to orchestrate-discovery.
        For Direct Repair: dispatch to orchestrate-direct-repair.
```

### orchestrate-design-review (Phase 0a)

```
Step 1: Read design-review-angles.md → build dispatch prompt for 2 baseline codex-reviewers.
Step 2: Dispatch reviewers (read ${CLAUDE_PLUGIN_ROOT}/references/dispatch-primitives.md for Return Contract + Finding Shape;
        read ${CLAUDE_PLUGIN_ROOT}/references/review-budget.md for budget check).
Step 3: Receive results → disposition each finding per dispatch-primitives.md Reception Rules.
Step 4: Route per ${CLAUDE_PLUGIN_ROOT}/references/coordinator-tools.md Routing Vocabulary.
        design gap → orchestrate-discovery; pass → check issue hierarchy.
```

### orchestrate-plan-review (Phase 0b)

```
Step 1: Read plan-review-angles.md → build dispatch prompt for 3 baseline codex-reviewers.
Step 2: Dispatch reviewers (dispatch-primitives.md + review-budget.md; update budget_total and pack_count).
Step 3: Receive results → disposition each finding.
Step 4: Route per ${CLAUDE_PLUGIN_ROOT}/references/coordinator-tools.md Routing Vocabulary:
        design gap → orchestrate-discovery; issue gap → to-issues;
        plan gap → orchestrate-plan-writing; architecture friction → improve-codebase-architecture;
        module map / call chain needed → zoom-out; pass → orchestrate-execution.
```

### orchestrate-execution (Phase A)

```
Step 1: Read pack-dispatch.md → per-pack worker dispatch.
        (When contract boundary touched: also read ${CLAUDE_PLUGIN_ROOT}/references/contract-boundary.md.)
Step 2: Worker returns → read pack-review.md → dispatch 1 baseline codex-reviewer per pack
        (dispatch-primitives.md + review-budget.md at dispatch).
Step 3: Receive pack review → disposition → repair per dispatch-primitives.md 修复归属.
Step 4: For parallel packs: read worktree-merge.md → coordinator merges worktrees sequentially.
Step 5: All packs pass → route to orchestrate-final-review.
        For non-pass outcomes, route per ${CLAUDE_PLUGIN_ROOT}/references/coordinator-tools.md Routing Vocabulary:
        design/domain gap → orchestrate-discovery; architecture friction → improve-codebase-architecture;
        unknown root cause → root-cause-analyst / complex-code-explorer.
```

### orchestrate-final-review (Phase B + C)

```
Step 1: Read final-review-angles.md → build dispatch prompt for 2 baseline codex-reviewers
        (augmented: regression sweep + full intent coverage + cross-pack audit).
        (dispatch-primitives.md + review-budget.md at dispatch.)
Step 2: Receive results → disposition → repair per dispatch-primitives.md 修复归属.
        Route per ${CLAUDE_PLUGIN_ROOT}/references/coordinator-tools.md Routing Vocabulary:
        implementation gap → orchestrate-execution; design / context gap → orchestrate-discovery;
        plan gap → orchestrate-plan-writing; architecture friction → improve-codebase-architecture.
        If release gate triggered: read review-budget.md → dispatch codex-release-reviewer.
Step 3: Phase B passes → read business-report.md → assemble Phase C business report.
Step 4: Branch finishing (commit, clean up, report to user). Done.
```

### orchestrate-direct-repair

```
Step 1: Read repair-grading.md → determine review tier (skip / lightweight / full).
Step 2: Dispatch worker (dispatch-primitives.md at dispatch;
        contract-boundary.md only if contract boundary touched).
Step 3: Worker returns → apply review tier from Step 1.
        Full review: dispatch codex-reviewer (dispatch-primitives.md + review-budget.md).
Step 4: Receive review → disposition per dispatch-primitives.md Reception Rules.
        Route per ${CLAUDE_PLUGIN_ROOT}/references/coordinator-tools.md Routing Vocabulary.
        Done.
```

### orchestrate-discovery / orchestrate-plan-writing

Self-contained. No shared reference loading needed — their own `references/` directories hold all required context. These skills do not dispatch codex-reviewers.

## Session-Start Hook Rewrite

The new `session-start.sh` emits seven rule blocks (all re-injected on compact event via `startup|clear|compact` matcher):

**1. Environment check** (F6)

**2. Progressive reference loading instruction** (preserves `d9037c4` route-based splitting):
```
- Shared references live in ${CLAUDE_PLUGIN_ROOT}/references/. Do NOT load all eagerly.
  Each orchestrate skill says which references to read inline at the point of use (dispatch step, routing step, etc.).
  Read them when you reach that instruction, not when entering the skill.
```

**3. Entry routing rules** (preserve current trigger phrases verbatim):
```
- When the user confirms a direction after discussion, use orchestrate-discovery to produce or refine a design document, then orchestrate-plan-writing to write the plan.
- AS SOON AS a design document is produced or exists, immediately enter orchestrate-workflow (entry gate) — it routes to the correct phase skill from Phase 0a onward.
- When the user references any existing design doc (specs/) or plan (plans/) and asks to review / audit / advance / execute / continue / 推进 / 审查 / 落地 / 动手 / 走流程, use orchestrate-workflow (entry gate).
```

**4. Skill chaining rules** (orchestrate chain transitions):
```
- orchestrate-workflow selects Formal Orchestrate → orchestrate-discovery
- orchestrate-discovery returns DISCOVERY_READY → orchestrate-design-review
- orchestrate-design-review passes → check issue hierarchy; missing → to-issues → orchestrate-plan-writing
- orchestrate-plan-writing returns PLAN_CREATED → orchestrate-plan-review
- orchestrate-plan-review passes → orchestrate-execution
- orchestrate-execution: all packs pass → orchestrate-final-review
- orchestrate-final-review passes → business report → branch finishing → done
- orchestrate-workflow selects Direct Repair → orchestrate-direct-repair
- At any point: design/domain/UX gap → orchestrate-discovery; issue gap → to-issues; plan gap → orchestrate-plan-writing
```

**5. Upstream skill routing** (preserved from coordinator-tools.md Routing Vocabulary):
```
- diagnose, prototype, improve-codebase-architecture, zoom-out, triage, grill-with-docs, to-issues
  remain callable from any orchestrate skill via Skill tool. coordinator-tools.md is the single source of truth
  for upstream routing; session-start only handles orchestrate chain transitions.
```

**6. Compaction-durable constraints** (re-injected on compact event, survive long sessions):
```
- Before entering any phase skill: re-read .claude/multi-model-workflow/scope-<run_id>.md to confirm Scope Contract
  is still current (source artifacts, editable artifacts, out of scope haven't drifted since last phase).
  Run `git status --short --branch` to verify branch and dirty state match expectations.
- Hard Gates:
  · 没有验证证据，不得声称完成。
  · 没有用户明确指令，不得 merge / push / PR / discard / 写生产环境。
  · Formal Orchestrate 没有可 review 的 design document 时先进 Discovery，不跳到 plan / worker。
  · Phase 0a / Phase 0b / Phase B 不可跳过（除非 Entry Gate 选择了 Answer-only / One-shot Review / Direct Repair）。
  · upstream skill 结论必须写回 design / plan / bug brief，再继续当前节点。
- 禁止:
  · 跳过 Phase 0 或 Phase B。
  · 用技术语言向用户汇报。
  · 自己写生产代码（调度 worker）。
  · 每 task 一个 subagent（用 Task Pack）。
  · 超过循环上限不处理。
```

**7. Agent roles and dispatch rules**:
```
- Agent roles: pack-executor (Sonnet, normal coding), complex-pack-executor (Opus, high-risk coding), code-explorer (Sonnet, narrow investigation), complex-code-explorer (Opus, deep investigation), root-cause-analyst (Opus, unknown root cause + fix), docs-worker (Sonnet, documentation).
- ALL code reviews dispatched to Codex via codex:codex-rescue for independent cross-model opinion. No Claude-side reviewer agent exists.
- Parallel Task Pack execution uses isolation: "worktree" in Agent tool call to prevent file conflicts.
```

## Implementation Order

### Pack 1: Structural split (no behavior change)

1. Create `plugin/references/` directory
2. Move 4 reference files from `orchestrate-workflow/references/` to `plugin/references/` (dispatch-primitives, contract-boundary, review-budget, coordinator-tools)
3. Extract custom agents table + 通信架构 table from `orchestrate-workflow/SKILL.md` into `plugin/references/custom-agents.md`
4. Extract 调度方式 section from `orchestrate-workflow/SKILL.md` into `plugin/references/dispatch-primitives.md` preamble
5. Consolidate 修复分流规则 into `dispatch-primitives.md` as single source of truth; remove duplicates from SKILL.md and phase-a.md
6. Create `orchestrate-design-review/` skill (content from `orchestrate-workflow/references/design-review.md`); inline "read dispatch-primitives.md / review-budget.md / coordinator-tools.md" at dispatch and routing steps
7. Create `orchestrate-plan-review/` skill (content from `orchestrate-workflow/references/plan-review.md`); same inline pattern
8. Create `orchestrate-execution/` skill (content from `orchestrate-workflow/references/phase-a.md`); inline shared ref reads at dispatch, contract-boundary, and routing steps
9. Create `orchestrate-final-review/` skill (content from `orchestrate-workflow/references/final-review.md`, unchanged for now); inline shared ref reads
10. Create `orchestrate-direct-repair/` skill (content from `orchestrate-workflow/references/direct-repair.md`); inline shared ref reads
11. Slim `orchestrate-workflow/SKILL.md`: keep Entry Gate + Resume Gate + Scope + Git Checkpoint + Hard Gates + 禁止 list; remove Reference Map, Formal Orchestrate 流程, Custom Agents, 通信架构, 修复分流, 调度方式 (all rehomed above)
12. Delete moved reference files from `orchestrate-workflow/references/`
13. Update `session-start.sh`: preserve trigger phrases verbatim (推进/审查/落地/动手/走流程, specs/, plans/); add chaining rules + progressive loading instruction + upstream skill routing note; add Hard Gates and 禁止 as compaction-durable constraints (re-injected on compact event)
14. Trim `coordinator-tools.md`: move Handoff Status to session-start chaining; keep Routing Vocabulary + Upstream Skill 调用 + Durable Brief + Direction Check intact
15. Update `plugin.json` version to 0.8.0

### Pack 2: Finding fixes

16. **F5**: Clean `contract-boundary.md` — remove AgentFlow-specific anchors
17. **F4**: Augment `final-review-angles.md` — add regression sweep + full intent coverage check; keep pack review deference for per-pack behavior; remove pure delta language that skips regression
18. **F2**: Create `worktree-merge.md` in `orchestrate-execution/references/`; update `pack-executor.md` and `complex-pack-executor.md` with commit prohibition
19. **F1**: Verify SubagentStop matcher supports `codex:codex-rescue` format (test before wiring); create `track-review-budget.sh` hook using `active-run-id` file for run discovery; update `hooks.json` with SubagentStop; add budget init + `active-run-id` write to `orchestrate-workflow` entry gate; add budget check + stale cleanup to each review skill
20. **F6**: Add env var check to `session-start.sh`
21. **F3**: Verify each review skill's prompt is naturally scoped (audit pass — no code change expected)

### Pack 3: Documentation sync

22. Update `AGENTS.md` (plugin maintenance protocol) to reflect new skill inventory
23. Update `README.md` with new architecture overview

## Critical Files to Modify

| File | Action |
|---|---|
| `plugin/skills/orchestrate-workflow/SKILL.md` | Rewrite: slim to entry gate + Resume Gate + Hard Gates + 禁止 list + Git Checkpoint (~60 lines) |
| `plugin/skills/orchestrate-design-review/SKILL.md` | New |
| `plugin/skills/orchestrate-design-review/references/design-review-angles.md` | New (from old design-review.md) |
| `plugin/skills/orchestrate-plan-review/SKILL.md` | New |
| `plugin/skills/orchestrate-plan-review/references/plan-review-angles.md` | New (from old plan-review.md) |
| `plugin/skills/orchestrate-execution/SKILL.md` | New |
| `plugin/skills/orchestrate-execution/references/pack-dispatch.md` | New (from old phase-a.md) |
| `plugin/skills/orchestrate-execution/references/pack-review.md` | New (from old phase-a.md) |
| `plugin/skills/orchestrate-execution/references/worktree-merge.md` | New (F2) |
| `plugin/skills/orchestrate-final-review/SKILL.md` | New |
| `plugin/skills/orchestrate-final-review/references/final-review-angles.md` | New (AUGMENTED — F4: regression sweep + full intent coverage + cross-pack audit; preserves pack review value) |
| `plugin/skills/orchestrate-final-review/references/business-report.md` | New (from old final-review.md Phase C) |
| `plugin/skills/orchestrate-direct-repair/SKILL.md` | New |
| `plugin/skills/orchestrate-direct-repair/references/repair-grading.md` | New (from old direct-repair.md) |
| `plugin/references/dispatch-primitives.md` | Moved |
| `plugin/references/contract-boundary.md` | Moved + cleaned (F5) |
| `plugin/references/review-budget.md` | Moved |
| `plugin/references/coordinator-tools.md` | Moved + trimmed (handoff status → session-start); KEEP Routing Vocabulary + Upstream Skill 调用 + Durable Brief + Direction Check |
| `plugin/references/custom-agents.md` | New (extracted from SKILL.md) |
| `plugin/hooks/hooks.json` | Updated (add codex budget hook) |
| `plugin/hooks/session-start.sh` | Rewritten (chaining + env check) |
| `plugin/hooks/track-review-budget.sh` | New (F1) |
| `plugin/agents/pack-executor.md` | Updated (F2: no commit rule) |
| `plugin/agents/complex-pack-executor.md` | Updated (F2: no commit rule) |
| `plugin/.claude-plugin/plugin.json` | Version bump |
| `AGENTS.md` | Updated: new skill inventory |
| `README.md` | Updated: architecture overview |

## Verification

1. **Directory structure**: `find plugin/skills -name 'SKILL.md'` shows 8 skills (workflow, discovery, design-review, plan-writing, plan-review, execution, final-review, direct-repair)
2. **No orphan references**: all old `orchestrate-workflow/references/` files are either moved or their content is in new skill references
3. **Chaining completeness**: `grep -c 'orchestrate-' plugin/hooks/session-start.sh` confirms all 8 workflow skills appear in chaining rules
4. **F1 budget counter**: `cat plugin/hooks/hooks.json | grep codex-rescue` confirms SubagentStop hook exists; `cat plugin/hooks/track-review-budget.sh` confirms counter logic; verify matcher format works with namespaced `codex:codex-rescue`
5. **F2 commit prohibition**: `grep -l 'commit' plugin/agents/pack-executor.md plugin/agents/complex-pack-executor.md` confirms both agents have the rule
6. **F4 augmented delta**: `grep -c 'regression sweep\|full intent coverage\|cross-pack audit' plugin/skills/orchestrate-final-review/references/final-review-angles.md` confirms augmentation; `grep -c 'covered by pack review' ...` confirms pack review deference preserved for per-pack behavior
7. **F5 cleaned**: `grep -c 'JSONB_COLUMN_REGISTRY\|LOCAL_JSON_COLUMN_REGISTRY\|Alembic\|migrations/gateway' plugin/references/contract-boundary.md` returns 0
8. **F6 env check**: `grep 'CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS' plugin/hooks/session-start.sh` confirms detection
9. **Content rehoming**: slim `orchestrate-workflow/SKILL.md` retains Hard Gates + Resume Gate + 禁止 list + Git Checkpoint; `grep -c 'Hard Gate\|Resume Gate\|禁止' plugin/skills/orchestrate-workflow/SKILL.md` confirms
10. **Compaction durability**: `grep -c '不得声称完成\|不得 merge\|不可跳过\|跳过 Phase\|技术语言' plugin/hooks/session-start.sh` confirms Hard Gates + 禁止 present in session-start (re-injected on compact)
11. **Trigger phrases preserved**: `grep -c '推进\|审查\|落地\|动手\|走流程\|specs/\|plans/' plugin/hooks/session-start.sh` confirms all trigger phrases survive
12. **Repair routing single source**: `grep -c '修复归属\|修复分流' plugin/references/dispatch-primitives.md` > 0; same grep in `orchestrate-execution/SKILL.md` returns 0 (references dispatch-primitives, doesn't duplicate)
13. **Progressive loading**: session-start.sh says "Do NOT load all eagerly"; each skill mentions shared refs inline at point of use, not in a formal section
14. **Upstream skill routing preserved**: `grep -c 'grill-with-docs\|diagnose\|zoom-out\|prototype\|improve-codebase-architecture\|triage' plugin/references/coordinator-tools.md` confirms Routing Vocabulary + Upstream Skill 调用 table intact
15. **Budget discovery**: `grep 'active-run-id' plugin/hooks/track-review-budget.sh` confirms file-based run ID discovery; verify stale detection (>1h) in entry gate
16. **Within-skill progressive loading**: Each phase skill's SKILL.md has numbered steps with explicit "read X at step Y" instructions; `grep -c 'Step [0-9]' plugin/skills/orchestrate-{workflow,design-review,plan-review,execution,final-review,direct-repair}/SKILL.md` confirms flow controller structure in all 6 routing skills (discovery + plan-writing are self-contained)
17. **Scope/Git compaction durability**: `grep 'scope-.*\.md' plugin/hooks/session-start.sh` confirms persisted scope re-read is in session-start (survives compact); entry gate writes `scope-<run_id>.md` alongside budget file
18. **Role-play simulation**: Re-run Formal Orchestrate simulation against the new skill chain to confirm each phase invokes the correct skill and all 6 findings are addressed
