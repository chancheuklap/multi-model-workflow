# plugin2 现状报告(systematic 优化 · investigate · 2026-06-29)

> investigate-internal(5 topic / 6 agent)产出,主线程已亲验承重事实。**取证不判定**,方案留 propose/design。路径相对仓库根。

## A. 接线 / 可安装性(plugin2 根本没装成插件)

- **无 `plugin2/.claude-plugin/plugin.json`**(目录都不存在)→ Claude Code 识别不了 plugin2。`plugin/.claude-plugin/plugin.json:1` 是参照(name/description/version/author/repo/license/keywords)。
- **无 `plugin2/hooks/hooks.json`** → 三个 hook(`guard-loop`/`guard-redline`/`record-step`)全是死脚本,各自注释声明要挂 SubagentStop / PreToolUse(Bash) / PostToolUse(commit),但没挂。`plugin/hooks/hooks.json:1` 是接线模板。
- **无 `plugin2/agents/`** → `plan-writer`(`plan-flow.md:20` `subagent_type:"plan-writer"`)派不出来;定义现躺在仓库根 `agents/plan-writer.md`,没进 plugin2。(build 改派 Codex、investigate 用内联 `agent()`,所以**只缺 plan-writer 这一个** agent;旧 plugin 的 pack-executor 等不需要。)
- `marketplace.json:17` source 仍指 `./plugin`、version 5.2.1,没切 plugin2。`build/build.sh` 只注入片段,不生成这三块。

## B. 外部 skill 依赖(可分发性)

design 阶段引的 `to-issues` / `domain-modeling` / `prototype` 都是 `~/.claude/skills` 全局 skill,**不在 plugin2**(`skills/` 只有 orchestrate/write-design-doc/write-plan-doc)。`discussion.md:29,84`、`write-design-doc/SKILL.md:29` 引用它们。作为可分发插件,这是未声明的宿主依赖。

## C. 落点不一致(多源,会接不上)

- **design 三种写法**:`prepare.sh:65,80` `docs/design/$slug`(无 `.md` 无日期);`routes.json:25` + `write-design-doc/SKILL.md:31` `docs/design/<slug>.md`;`discussion.md:34` `docs/design/<YYYY-MM-DD>-<slug>.md`(**slug 已含日期,这里又加一遍 = 双日期**)。
- **issues 两种**:`prepare.sh:65` `docs/issues/<slug>`;`write-design-doc/SKILL.md:29` `docs/issues/<YYYY-MM-DD>-<slug>/`。
- direction / context 落点前后一致(propose / investigate 没问题)。

## D. 断点续传深度(build 内层 loop 续不回)

- `loop-state` 的 step 只存 id/desc/commit,**无 plan 路径、无 worktree 路径**(`loop.sh:64-66`);plan→worktree 映射无处持久化。
- `task.json` 单 `worktree_path`(主 worktree);build 给各 plan 开的子 worktree 不进 task.json(`prepare.sh:64`、`codex-worker.sh:85-87`)。
- `codex-session` 每 dispatch `printf >` 覆盖写,只能续最后一次;dispatch 中途崩则 session 没落盘只能重派(`codex-worker.sh:49,58-61`)。
- **无 in-flight 标记**:step 在 Claude 亲验前一直 pending,resume 看不出某 plan 已派 Codex / 可能已在子 worktree 提交(`loop.sh:66`、`build.md:34`)。
- **`contract-gate` init 覆盖抹 execution 进度**:`loop.sh:43-47` cmd_init 无条件 `jq -n '{...fresh...}' > loop-state.json`,起③合同门时把 execution 的 steps/decisions 抹掉(git 提交还在,但 state 丢了)。
- `step.status=blocked` 在 schema 容许(`loop-state.schema.json:23`)但 `loop.sh` 只有 step add/done,**无置 blocked 的命令** → blocked 步落不了盘。
- `where` 只读 task.json,**从不读 loop-state**(`flow.sh:196-240`);无内层断点恢复程序(怎么重建 plan→worktree、重新发现已派子 worktree),build.md 只写正向流程。

## E. 三原则残留(craft,上轮我只修了一半)

- **write-design-doc/SKILL.md 收尾段仍内联方法论**(`:27-34` 拆 issue 细则 + 四条结论词分支 + ①设计审 flow 说明),**且与 `design-self-check.md:20` 重复**写了一遍 ①审+结论词处置。SKILL 没做到纯路由。
- **write-plan-doc/SKILL.md 前置 + 收尾内联**,同样与 `plan-self-check.md` 末节重复。
- Hard Gate 在 `write-design-doc/SKILL.md` 与 `discussion.md` 各写一遍(重复)。
- **跨文档片段跳转仍在**:`review/plan-impl.md` + `review/final.md`「禁用捷径:见 quartet.md 附录」指向 `quartet.md` 末节附录;`design-self-check.md:3`「见末节」;design/plan-self-check「见编排的审核 loop」无路径行号。
- why 废话(medium):`plan-flow.md`「省一次派发往返」「逼它认真读代码」「不是 TBD」;`design-doc-template.md` 锚点占位三行注释辩解。

## F. PDF 对照(多数兑现,少数缺脚本支撑)

- domain-modeling / mockup / to-issue 折叠进 design 内部(非独立阶段)——设计取向,可接受。
- **`prepare.sh:51` 不 scaffold `docs/mockups`**(design-doc-template 写 mockup 落 `docs/mockups/<slug>/`,但脚本没建该目录)。
- **`merge.md:26` 要求禁 `--squash`,但 `guard-redline.sh` 只通配拦 `git merge` 要批准,不单独阻断 `--squash`**——这条只有口头(CLAUDE.md 硬规则也写了)。
- plan 阶段不走 afk loop(`develop.md:6` HITL 集中 propose/design/plan,进 build 才放权)——按设计。
- merge 兑现最完整(`merge.md` 引 PDF 业务冲突理念 + `prepare.sh:139` team + guard-redline 红线)。

## 旁路(已 spinoff)

- `.DS_Store` 在 plugin2 根(out-of-scope)。
- `guard-redline.sh:11` 通配 grep 拦 merge,可能与旧 plugin 同源裸 grep 误拦(needs-evaluation,未验)。

## Open questions(留 propose/design 拍)

- plugin.json 字段集 / version / name 复用旧版(multi-model-workflow)还是新起?
- 外部 skill(to-issues/domain-modeling/prototype)设计为依赖宿主全局,还是 vendor 进包?
- 落点权威约定取哪种(test_prepare 固化了无后缀无日期形态)?
- tdd-executor 是否需要 plugin2 内 agent .md(现只作 Codex 选模型标签,未见 subagent_type 派发点)。
