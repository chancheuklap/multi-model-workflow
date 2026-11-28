# Antigravity (AGY) lifecycle and runtime internals

Consult this file only when debugging failures, lock or `Stop` hook sweep behavior, live-terminal `--resume` reuse, or `--force` close.

## AGY App and `agy` CLI runtime boundary

- Keep the default `--mode auto` with `scripts/agy-delegate`, and reserve `--mode herdr` for active Herdr Core terminals.
- `scripts/agy-delegate` launches `agy` CLI under `~/.gemini/antigravity-cli/`, separate from AGY App (`~/.gemini/antigravity/`) and AGY IDE (`~/.gemini/antigravity-ide/`).
- Pass only `agy` CLI or `scripts/agy-delegate` conversation IDs to `--resume`, never a non-CLI session ID from AGY App or AGY IDE.
- Before `--resume`, `scripts/agy-delegate` inspects `~/.gemini/antigravity-cli/conversations/<id>.db` (`trajectory_metadata_blob`) and fails fast when `.agents/agents/` appears, so legacy 4x custom-agent conversations never resume at 4x billing. Start a fresh `1.00x` session instead.
- When reporting `agy` CLI delegates inside AGY App, cite the returned `transcript_path` instead of `conversation://<child-id>` links.
- `agy` CLI stores authentication and settings separately from AGY App. If `scripts/agy-delegate` fails with an authentication error inside a logged-in AGY App session, report that `agy` CLI needs re-authentication instead of retrying as a network error.
- When searching local Antigravity conversation history, such as in `recall`, inspect both `~/.gemini/antigravity/` and `~/.gemini/antigravity-cli/` when present.

## Four lifecycle classes

AGY child terminals use `ephemeral`, `gated`, or `session` under `scripts/agy-delegate`, while the `Main chat` and `Root coordinator` remain `top-level`.

- **`ephemeral`.** Stays visible while running, closes its Herdr terminal and Herdr Core record after returning a settled result, and preserves its on-disk transcript. When the operator views or peeks that terminal, closing defers until focus moves away unless the terminal is pinned.
- **`gated`.** Stays live after its turn for parent review or a bounded follow-up turn. Closes on an explicit `close` command, with a parent `Stop` hook fallback sweep that closes settled, consumed, unpinned, unfocused `done` or `idle` children.
- **`session`.** Survives across parent turns, `Hold` pauses, and hourly `Audit tick` runs until an explicit `close` at mission end, stuck replacement, operator `Stop`, `Pause safely`, or parent exit.
- **Nested delegates.** Nested `ephemeral` and `gated` delegates spawned by a `session` owner close under their own lifecycle classes without waiting for their `session`-tier parent to close.

## Default `--lifecycle auto` routing and overrides

Pass `--lifecycle auto` by default, or `--lifecycle ephemeral|gated|session` to override the inferred class. Passing an invalid `--lifecycle` value fails fast before launch. In headless mode, `--lifecycle` validates its value and exits on completion. When `--lifecycle` is `auto`, `scripts/agy-delegate` resolves the class in this order:

1. Explicit non-`auto` `--lifecycle <ephemeral|gated|session>` wins.
2. Live-terminal `--resume <conversation_id>` keeps the reused terminal's existing `agy_delegate_lifecycle` label.
3. Specialist hook or legacy `--agent` overrides apply next (`advisor` resolves to `gated`; `comment-sicko` resolves to `ephemeral`).
4. The resolved `modelRole` map applies next (`coder` resolves to `session`; `advisor`, `feature, refactoring`, `feature`, `refactoring`, `bug-fix`, `perf-issue`, and `hillclimb` resolve to `gated`; `verifier`, `reader`, `code review`, `judgment and prose`, `arena runners`, and `arena cross-judge pool` resolve to `ephemeral`).
5. Remaining calls fall back to the `--role` default (`mmw-agent` resolves to `gated`; `none` and other unrecognized roles resolve to `ephemeral`).

Pass `--lifecycle session` when a playbook needs cross-turn persistence for a non-`coder` role, such as a `Feature` multi-phase single owner. Pass `--lifecycle ephemeral` for a one-shot `mmw-agent` helper that needs no parent follow-up.

## Per-turn `turn_token` and settlement

On a clean Herdr turn, `scripts/agy-delegate` locks the terminal, writes `agy_delegate_settled=1` and a fresh `agy_delegate_turn_token`, and emits that value as `turn_token` in stdout JSON. The parent `Stop` hook sweep matches `agy_delegate_turn_token` in the parent transcript before closing a `gated` child. When no token label exists, it matches the terminal address or `agy_conversation_id` instead.

The `turn_token` field is `null` for headless runs, already-`finished` terminals, and clean settlements where `scripts/agy-delegate` skips token writing. It skips token writing when fresh `hc get` shows `working` or `blocked`, when the terminal lock times out, or when `hc label` fails.

## Live-terminal reuse on `--resume`

In Herdr interactive mode, `--resume <conversation_id>` acquires the conversation lock and inspects live direct children matching `agy_conversation_id=<conversation_id>`. Non-`not_found` inspection errors from `hc ls` or `hc get`, and lock timeouts, fail closed without spawning a duplicate terminal.

- `scripts/agy-delegate` fails fast non-zero as busy when any matching live child has `agy_delegate_settled=0` or a status other than `done` or `idle`. That busy rejection covers `working`, `blocked`, `booting`, and missing status, and names the terminal address and status instead of opening a duplicate.
- When a settled matching child meets any explicit `--model` or `--model-role` constraint, `scripts/agy-delegate` locks it and sends the follow-up prompt via `hc send`. It returns only the new turn output. If `hc send` fails, `scripts/agy-delegate` restores the child's prior labels before releasing the lock instead of leaving the child corrupted. Reused terminals keep their `agy_delegate_lifecycle` unless you pass a non-`auto` `--lifecycle` flag.
- When a settled live child fails an explicit `--model` or `--model-role` constraint, `scripts/agy-delegate` locks and closes the old child before cold-starting the new model. That replacement inherits the old `agy_delegate_lifecycle` under `--lifecycle auto`, or uses an explicit `--lifecycle` flag. If the old child is `herdr.pinned`, focused, busy, or cannot close, `scripts/agy-delegate` fails fast non-zero without spawning a replacement.
- If no live child matches, `scripts/agy-delegate` starts a fresh Herdr child terminal with `agy --conversation <id>`.

## Explicit close commands

Only the parent session (`HC_TERMINAL_ID`) closes its own direct children. Every close preserves the on-disk transcript and SQLite conversation history.

- **Close one child.** Run `scripts/agy-delegate close <terminal-or-conversation-id>` to close an unpinned, unfocused `done` or `idle` direct child, including an explicitly named `session` child, via `hc kill` and `hc rm`. It fails non-zero when the target is `working`, `blocked` (`Needs you`), or `herdr.pinned`. It exits zero with `deferred` after setting focus deferral when the operator is viewing or peeking that terminal.
- **Close all non-session children.** Run `scripts/agy-delegate close --all-mine` to close all eligible non-`session` direct children (`ephemeral`, `gated`, and focus-deferred) and reap `finished` child records. It skips `session`, `working`, `blocked`, and `herdr.pinned` children, and defers focused children.
- **Force-close.** Pass `--force` only for operator `Stop`, `Pause safely`, or stuck-agent replacement, including active `PR owner` sessions that may still be `working` or `blocked`. `scripts/agy-delegate close <target> --force` closes the named child unconditionally. `scripts/agy-delegate close --all-mine --force` closes all direct children, including `session`, `working`, `blocked`, and focused terminals, while preserving `herdr.pinned` terminals unless named directly.

## Failures and protection

Automatic cleanup and non-forced close commands never close a terminal that is `working`, post-boot `blocked`, or `herdr.pinned`. They defer closing when the operator views or peeks that terminal.

- Failure paths cover a non-zero exit, lost process, `error` status, model mismatch, explicit `--timeout`, and an `authTimeout` after a 15-second startup `auth` block. On failure, `scripts/agy-delegate` returns the error detail, terminal screen output, and `transcript_path`.
- Failure cleanup locks the terminal and re-checks fresh `hc get`. It skips killing and reports `terminal_closed: false` when fresh `hc get` shows `herdr.pinned`, when the terminal lock times out, or when `hc get` returns a non-`not_found` error.
- On `authTimeout`, it skips killing with `terminal_closed: false` when fresh `hc get` shows `working` or non-`auth` post-boot `blocked`.
- On `error` or model mismatch, it skips killing with `terminal_closed: false` when fresh `hc get` shows `working` or any `blocked`. Otherwise it kills and removes the failed child terminal immediately.
- Fallback spawning never runs while a failed terminal remains live. Retriable `# fallback:` attempts clean up each failed attempt terminal before trying the next model candidate, and an exhausted `# fallback:` chain fails non-zero.
