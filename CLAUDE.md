# CLAUDE.md

> 本文管这个项目怎么做。跨项目的通用规范在全局 `~/.claude/CLAUDE.md`,本文只写项目特有的。

## 这个项目在做什么

`plugin2/` = 重建中的多模型开发编排 plugin。**目标**:做成能落地、被用户长期持续使用的商业化 plugin——让用户在**设计 / 计划阶段与主线程对齐(HITL 集中在此)**,在**执行阶段(落地 / 审)放权自主跑**,从而多线程工作、不从头盯到尾。

**验收标准**:第二个零上下文 agent 能照 plugin 独立跑通,不靠我临场解释。

## 边界

- **活跃**:`plugin2/`(重建,下面规则管它)+ `docs/plugin2/`(设计文档 / OVERVIEW,**不随插件发布**)
- **旧版**:`plugin/`(被 plugin2 替换;除非明确指令别改。终态把 `marketplace.json` 的 source 切到 plugin2)
- **独立 skill/agent 系统**:`skills/` + `agents/`(权威说明在 `AGENTS.md`)
- **禁区**(明确指令才动):`.agents/`(Codex skill)、`codex/`(Codex agent/hook/sync)、`archive/`(归档)

## 全貌 + 工作流权威

- plugin2 架构总览:`docs/plugin2/OVERVIEW.md`(一张主图 + 三层结构 + 七阶段)。改 plugin2 前先读。OVERVIEW 是**全貌不是流水账**。
- 工作流权威:`~/Documents/multi model workflow.pdf`——日常工作流的源,plugin2 照它的节点和箭头建。

## Skill 创建法则(改 plugin2 的 skill / reference 必须照这 11 条)

1. **SKILL 纯路由**:只做断点恢复 + 选路 + 指到该读哪份 reference,**不内联方法论**。
2. **reference 整份指引,无碎片跳转**:agent 被指去**读一份完整 reference**,不"读 SKILL 某段"也不"读 reference 某节"。禁 `§N` / `见上见下` / `见 X.md 的 Y 节` / `详见 X.md 附录`。需要的内容放进读者要读的那份里。
3. **不读无关**:每路径(small-change/develop/bug/merge)、每阶段一份干净完整文档;共用步骤(建 worktree、契约、回执)在各份里**重复写**,由 `build/build.sh` + `build/fragments/*` 单源注入——读者只读一份,重复不算冗余。
4. **不写废话**:runtime 指南只写"干什么 + 跑什么命令",不写"为什么这么设计"(理由进 `docs/plugin2`),不解释确定逻辑。
5. **确定的归脚本 / 命令**:机械步骤做成 `mmw` 命令或 workflow 脚本,文档只说"判断完跑哪个、填什么参数就跑",agent 快进快出**不手搓**。两个方向就两个脚本(如 investigate-internal / external)。
6. **mmw 不必每份重定义**:agent 永远先经 orchestrate SKILL 进来、那时已知 `mmw`,reference 直接 `mmw X` 用即可。
7. **每一步都是 plugin 告诉的、且正确**。"plugin 没告诉我却要做"的动作 = 缺口,补进 plugin(如 checkpoint 展示格式要在文档里定死),别临场发挥。
8. **路由分叉 / HITL 闸 / 给方案归 orchestrate + flow**,不归阶段方法论 skill(如 propose 阶段)。两条路用引擎现成出口:`pass`→advance,`needs-redirection`→回上游。
9. 照 **PDF** 建。
10. 设计文档放 `docs/plugin2/`,**不进可发布的 `plugin2/`**。
11. **修在 worktree 分支,完事 `--no-ff` 合回 main**,不在 main / worktree 两头跳改(会读到旧码)。

## PDF 工作流(plugin2 要实现的端到端)

四开口(新设计 / 优化改造 / bug / 合并)→ **investigate**(内部仓库 + 外部方案,两个独立 workflow,取证不判定)→ **propose 给方案**(综合现状亮 2-3 方案,HITL:选一个进 design / 全否回上游)→ **design**(domain 对齐 + 设计审 + to-issue 切片)→ **plan**(单 / 多计划,跨计划合同骨架,fan out plan-writer,计划审)→ **Codex 落地**(主线程开 worktree 分配给 Codex,CLI,固定 prompt 严防过度设计 / 兜底 / 思考,返回后主线程做完整性 + 设计一致性检查)→ **final review**。

- **HITL 集中在设计 / 计划阶段**;进了计划 / 落地默认无人值守,不轻易停下问。
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
- 改了 `build/fragments/*.md` 或带锚点的 skill → 跑 `bash plugin2/build/build.sh --apply` 再 `--check`(锚点内手改会被覆盖)。
- merge / push / 部署是红线,要人批。

## 常用命令(plugin2)

```bash
# 统一 CLI(读完 skill 直接用)
bash plugin2/scripts/mmw.sh help          # 看全表:where|handoff|task|loop|review|codex
bash plugin2/scripts/mmw.sh where          # 我在哪阶段 / 下一步读啥干啥交啥

# 全量测试
for t in plugin2/scripts/tests/test_*.sh; do bash "$t" || break; done
bash plugin2/build/tests/test_build.sh

# 构建(共用片段注入各路径 reference)
bash plugin2/build/build.sh --check        # 片段改了没 apply 会报 DRIFT
bash plugin2/build/build.sh --apply

# JSON 格式
python3 -m json.tool plugin2/state-schema/routes.json >/dev/null
```

> 接线(`plugin2/.claude-plugin/plugin.json` + `hooks.json` + `agents/` + marketplace 切源)尚未做;做完后版本号需 `plugin.json` 与 `marketplace.json` 两处同步。
