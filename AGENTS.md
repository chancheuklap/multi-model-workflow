# AGENTS.md

> 本文管这个项目怎么做,只写项目特有的;跨项目通用规范在各宿主全局规则文件。

## 这个项目在做什么

`plugin/` = 正式启用的多模型开发编排 plugin。**目标**:做成能落地、被用户长期持续使用的商业化 plugin——让用户在**讨论 / 设计阶段与主线程对齐(HITL 集中在 propose/design)**,从**计划阶段起放权自主跑**(计划审是模型闸、不问人),从而多线程工作、不从头盯到尾。

`plugin/` 只面向 Claude Code。**Codex 不是独立 plugin,是 Claude Code plugin 里的一个工人**(写计划 / 落地 / 审查),只装 plugin 内那几个软链 skill(worktree-build/plan/review)就够用。

**验收标准**:第二个零上下文 agent 能照 plugin 独立跑通,不靠我临场解释。

## 边界

- **活跃**:`plugin/`(正式启用;Claude marketplace source 指它)
- **禁区**(明确指令才动):`codex/`(Codex agent/hook/sync)、`archive/`(归档 v1)

## 全貌 + 工作流权威

- 工作流权威:`~/Documents/multi model workflow.pdf`——日常工作流的源,plugin 照它的节点和箭头建。
- plugin 的行为真相 = 代码 + `plugin/skills/**/references` + tests,不再维护独立架构设计文档;改 plugin 前先读 `plugin/skills/orchestrate/SKILL.md` 与相关 references/脚本。

## Skill 创建法则(改 plugin 的 skill / reference 必须照这 11 条)

1. **SKILL 纯路由**:只做断点恢复 + 选路 + 指到该读哪份 reference,**不内联方法论**。
2. **reference 整份指引,无碎片跳转**:agent 被指去**读一份完整 reference**,不"读 SKILL 某段"也不"读 reference 某节"。禁 `§N` / `见上见下` / `见 X.md 的 Y 节` / `详见 X.md 附录`。需要的内容放进读者要读的那份里。
3. **不读无关**:每路径(small-change/develop/bug/merge)、每阶段一份干净完整文档;共用步骤(建 worktree、契约、回执)在各份里**重复写**,由 `build/build.sh` + `build/fragments/*` 单源注入——读者只读一份,重复不算冗余。
4. **不写废话**:runtime 指南只写"干什么 + 跑什么命令",不写"为什么这么设计"(理由留在 commit message),不解释确定逻辑。
5. **确定的归脚本 / 命令**:机械步骤做成 `mmw` 命令或 workflow 脚本,文档只说"判断完跑哪个、填什么参数就跑",agent 快进快出**不手搓**。两个方向就两个脚本(如 investigate-internal / external)。
6. **mmw 不必每份重定义**:agent 永远先经 orchestrate SKILL 进来、那时已知 `mmw`,reference 直接 `mmw X` 用即可。
7. **每一步都是 plugin 告诉的、且正确**。"plugin 没告诉我却要做"的动作 = 缺口,补进 plugin(如 checkpoint 展示格式要在文档里定死),别临场发挥。
8. **路由分叉 / HITL 闸 / 给方案归 orchestrate + flow**,不归阶段方法论 skill(如 propose 阶段)。两条路用引擎现成出口:`pass`→advance,`needs-redirection`→回上游。
9. 照 **PDF** 建。
10. **不维护独立设计文档**:一次性评估/设计材料用完即删不入库;长期约束写进本文件或 references。
11. **修在 worktree 分支,完事 `--no-ff` 合回 main**,不在 main / worktree 两头跳改(会读到旧码)。

## PDF 工作流(plugin 要实现的端到端)

四开口(新设计 / 优化改造 / bug / 合并)→ **investigate**(内部仓库 + 外部方案,Workflow 取证不判定)→ **propose 给方案**(综合现状亮 2-3 方案,HITL)→ **design**(domain 对齐 + 设计审 + to-issue 切片)→ **plan**(单 / 多计划,跨计划合同骨架,fan out Codex 写计划工人 `mmw worker plan-dispatch`,计划审)→ **写码工人落地**(`mmw worker dispatch`,Codex CLI)→ **final review**(Codex + 会话内 code-reviewer sub-agent)。

- **HITL 集中在 propose / design 阶段**;进了计划 / 落地默认无人值守,不轻易停下问。
- 断点续传:阶段级 + 内层 loop。
- merge:解 git 文本冲突之外的**业务意图 / 功能设计冲突**。
- 又稳又快:确定的用脚本固定,流程不绕不卡。

## 执行纪律(本项目强调,补全局规范)

- **不作弊**:演练就真跑 plugin,不照文档脑补;"plugin 告诉我的"必须真是它当场报的。
- **子代理不是信源**:它给的 `file:line` / 计数 / 存在性,写进交付物或汇报前亲验(grep / Read / 跑)。
- **不静默兜底**:脚本失败必须留痕(fail-closed),不吞异常 / 不填默认伪装成功;合法降级也要结构化告警。
- **跟着 plugin 走**,不被 workflow / 工具带偏。

## 硬规则

- `git merge --squash` 禁,必须 `--no-ff`。
- Worker(worktree 内运行)不改 `docs/`,只有 Coordinator(主线程)能改。
- 改了 `build/fragments/*.md` 或带锚点的 skill → 跑 `bash plugin/build/build.sh --apply` 再 `--check`(锚点内手改会被覆盖)。
- push / `gh pr merge` / 部署是红线,要人批;**本地 `git merge`(含进 main)不拦**——可逆、不出站,真正红线是它之后的 push。

## 常用命令(plugin)

```bash
# 统一 CLI(读完 skill 直接用)
bash plugin/scripts/mmw.sh help          # where|handoff|step|spinoff|task|loop|review|worker(codex 别名)|progress
bash plugin/scripts/mmw.sh where          # 我在哪阶段 / 下一步读啥干啥交啥

# 全量测试
for t in plugin/scripts/tests/test_*.sh; do bash "$t" || break; done
bash plugin/build/tests/test_build.sh

# 构建(共用片段注入各路径 reference)
bash plugin/build/build.sh --check        # 片段改了没 apply 会报 DRIFT
bash plugin/build/build.sh --apply

# JSON 格式
python3 -m json.tool plugin/state-schema/routes.json >/dev/null
```

> 接线:`plugin/.claude-plugin/plugin.json` + 根 `.claude-plugin/marketplace.json` source 指 `./plugin`。hooks 只接 Claude Code 的 `Bash` matcher,带 `if` 前筛。改版本号同步两处 JSON。
