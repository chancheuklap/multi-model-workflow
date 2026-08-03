# 片段来源清单(下面第一区为程序化抽取且逐字未改;自维护区逐条写明改写理由。重渲染/校验跑 scripts/render_agent_prompts.py --check)

- `codex56-autonomy-persistence.md` sha256:900c391377633b51 — codex CLI 0.144.5 内嵌模型目录 gpt-5.6-sol instructions_template「Autonomy and persistence」节
- `codex56-worktree-safety.md` sha256:79fa2556eb5450a0 — 同上「File editing constraints」dirty worktree + destructive git 两段(不含 apply_patch 段)
- `codex52-root-cause.md` sha256:22c8353d31c1c015 — openai/codex codex-rs/core/gpt_5_2_prompt.md coding guidelines 单条
- `pi-subagents-tool-bridge.md` sha256:ace1f3d4b96dad3b — @tintinweb/pi-subagents dist/prompts.js append 模式 bridge 块原文
- `pi-subagents-tool-bridge-readonly.md` sha256:614217c0f2f38e21 — 同上,仅删 edit/write 两行(只读角色无这两个工具)
- `cc-act-when-ready.md` sha256:c47680e277549de7 — Piebald claude-code-system-prompts v2.1.212 system-prompt-act-when-ready.md
- `cc-action-safety-truthful-reporting.md` sha256:9c4c201a1fbc2362 — 同仓库 system-prompt-action-safety-and-truthful-reporting.md(取含"approval in one context"完整分支)
- `cc-no-compatibility-hacks.md` sha256:832bd3ad701dcc98 — 同仓库 doing-tasks no-compatibility-hacks
- `cc-no-unnecessary-additions.md` sha256:39b8bff8f4ead50a — 同仓库 doing-tasks no-unnecessary-additions
- `cc-no-unnecessary-error-handling.md` sha256:4ea30440058bb01d — 同仓库 doing-tasks no-unnecessary-error-handling
- `cursor-context-thoroughness.md` sha256:af1d36c7317054f6 — x1xhlol 提取 Cursor Agent Prompt 2.0 maximize_context_understanding 首块(工具无关部分)
- `cc-comment-no-what-no-task-context.md` sha256:206fc3c559016b5e — 同仓库 comment-what-and-task-context-avoidance

## MMW 自维护片段(非厂商逐字抽取,改动同步更新本清单)
- `mmw-supervisor-channel.zh.md` — 重角色向上举手协议(contact_supervisor 三用法 + 不举手边界),2026-07-19 随 nicobailon 运行时落地
- `cc-comment-why-only.md` sha256:17f055ba2c2a183d — 首句改写。原为 Piebald claude-code-system-prompts v2.1.212 comment-why-only-guidance 的 “Default to writing no comments”；Anthropic 《The new rules of context engineering for Claude 5 generation models》把该句明确列为需要取消的旧型 guardrail，官方新写法为 “Write code that reads like the surrounding code: match its comment density, naming, and idiom.”；2026-07-27 换成新写法并保留原有 WHY 判据作为退化分支

## 中文译文(2026-07-17 用户拍板:角色提示词全中文,精确翻译+适当润色;英文原文保留作对照源)
- `codex56-autonomy-persistence.zh.md` sha256:5432aa861db13998 — 译自 `codex56-autonomy-persistence.md`
- `codex56-worktree-safety.zh.md` sha256:07aa2692615f6082 — 译自 `codex56-worktree-safety.md`
- `codex52-root-cause.zh.md` sha256:1445082ec5f6b51c — 译自 `codex52-root-cause.md`
- `pi-subagents-tool-bridge.zh.md` sha256:4db69cd2db7ebb01 — 译自 `pi-subagents-tool-bridge.md`
- `pi-subagents-tool-bridge-readonly.zh.md` sha256:2f5b5bdcb9dc7759 — 译自 `pi-subagents-tool-bridge-readonly.md`
- `cc-act-when-ready.zh.md` sha256:31ef5c395e77b71d — 译自 `cc-act-when-ready.md`
- `cc-action-safety-truthful-reporting.zh.md` sha256:72da331794a9832c — 译自 `cc-action-safety-truthful-reporting.md`
- `cc-no-compatibility-hacks.zh.md` sha256:2381c4bbeb58fa6a — 译自 `cc-no-compatibility-hacks.md`
- `cc-no-unnecessary-additions.zh.md` sha256:1fd4c40e176a5eb7 — 译自 `cc-no-unnecessary-additions.md`
- `cc-no-unnecessary-error-handling.zh.md` sha256:000d141c2c6f720e — 译自 `cc-no-unnecessary-error-handling.md`
- `cc-comment-why-only.zh.md` sha256:b7649fc8279e91a8 — 译自 `cc-comment-why-only.md`(已同步首句改写)
- `cc-comment-no-what-no-task-context.zh.md` sha256:71e8c68695b0c50e — 译自 `cc-comment-no-what-no-task-context.md`
- `cursor-context-thoroughness.zh.md` sha256:d3bb777268956a82 — 译自 `cursor-context-thoroughness.md`
