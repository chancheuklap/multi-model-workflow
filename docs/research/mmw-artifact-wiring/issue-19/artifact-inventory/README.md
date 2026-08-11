# research：MMW 产出和使用的产物完整清单

## 这次要回答的问题

MMW 实际产出和使用的产物，完整清单是什么？对每一类产物查明：谁生产它、谁读取它、当前落在哪个路径、路径里的名字由什么决定、它进不进 Git。

来源：Wayfinder decision ticket #19，map 是 #18「MMW 产物归纳与接线合同」。

## 查证范围

- 仓库 commit `b3d924ce9db88a7380dbcc13ad615aaa014454f9`，2026-08-11。
- `mmw/skills-src/` 全部技能源及其链接的 reference，排除 `mmw-setup/`（`AGENTS.md` 规定它只是旧背景材料）。
- `mmw/cli/` 全部命令与 `mmw/cli/adapters/`、`mmw/release/`、`mmw/mcp/`、`mmw/codex/`。
- 根 `.mmw.json`、`mmw/cli/mmw.default.json`、`.gitignore`。
- issue tracker 上承载的产物：map、decision ticket、spec issue、tracer bullet ticket、agent brief。
- GitHub Wiki 页面与导航。

三个取证角度：技能源侧、CLI 与配置侧、非 Git 与 tracker 侧。三份 `investigator` 报告的关键断言由主 agent 逐条打开位置核对。

## 结论摘要

1. **产物共 27 类**，见 `report.md` 第 1 节。其中长期留在仓库的只有：领域文档、ADR、prototype 资产、research、用户选择保留的 evidence、`.out-of-scope/` 记录。
2. **名字来源只有两个，而且互不统一**：任务 slug 管 spec、plan、evidence、审查记录、Wiki 页、任务 worktree；产物目录管 prototype、research、scratch、共同理解记录。`mmw-wayfinder/closing.md:41` 把两者作为两个独立值交给下游，两个值可以不同。
3. **已确认四处落点冲突**：共同理解记录在 Wayfinder 下丢掉上层目录；界面 evidence 落在产物目录之外，收尾技能为它写了补偿逻辑；派发四栏 task 的落点没有统一规定，本次 research 实测就落错了位置；`docs/research/...[/issue-<编号>]/` 那个可选层不是冲突。
4. **spec 与 plan 不长期留在仓库里**。`mmw-closing/SKILL.md:88` 在收尾时删除 `docs/specs/<slug>/` 与 `docs/plans/<slug>/`，长期副本在 GitHub Wiki。
5. **`.mmw.json` 的五项产物路径无消费方，而且 `mmw init` 会主动删除它们**（`init.sh:58-63`）。技能正文写死这五个路径。
6. **`mmw domain` 是现有唯一一处「由命令回答落点」的实现**，只覆盖领域文档和 ADR。`domain path` 返回形态、绝对路径、下一步指令三列。
7. **`mmw init` 不创建任何产物目录**，也不创建 Context Map。
8. **三项产物在已查范围内无消费方**：`docs/evidence/<任务 slug>/`、`.dispatch/` 的四栏 task 与报告、临时目录里的 handoff 与架构候选报告。

## 本目录的文件

| 文件 | 内容 |
| --- | --- |
| `README.md` | 本文件，research 索引 |
| `report.md` | 完整结论，八节，每条附精确文件与行号 |

## 下游怎么用

- decision ticket #21「每类 MMW 产物的落点与路径形状」：用 `report.md` 第 1 节的产物清单作为要定落点的完整对象集合，用第 3 节的冲突清单作为必须解决的具体项。
- decision ticket #22「产物目录与任务 slug 合并还是保留两个」：用第 2 节。它给出两个名字各自管哪些产物，以及两者在何处被作为独立值传递。
- decision ticket #24「落点合同存放在哪里，`.mmw.json` 的 `paths` 是什么角色」：用第 4 节和第 5 节。
- decision ticket #25「历史产物迁移命令的形态与边界」：用第 4 节判断哪些产物长期留在仓库、哪些本来就会被删除；spec 与 plan 会被收尾删除这一点改变迁移对象的范围。
- decision ticket #26「新归纳合同下机械校验能判定什么」：用第 7 节。无消费方的三项是候选校验对象，但要注意本次没有取得结构候选。

## 没查清楚的部分

- **`docs/evidence/`、`.dispatch/` 与临时目录报告的「无消费方」判定，只覆盖技能源正文加 `mmw/` 下源码的文本范围。** Serena 对 `mmw/cli/lib/context_docs.py` 返回「该路径被忽略」，Graphify 查询被宿主取消，因此没有取得结构候选。这三项不能作为全仓库反向引用的完整结论。要把它们当作机械校验的依据前，先按 `/mmw-retrieval` 修好检索工具，再取一次结构候选。
- `mmw-install/SKILL.md:31-41` 说 `mmw init` 会创建「全部配置」，但没有列出精确文件路径。技能源侧无法据此补全清单；本次的 `mmw init` 产物清单来自 `init.sh` 源码。
- `mmw toolchain install --yes` 的输出路径由规则表的 `install` 命令决定，没有固定落点。本次未逐条展开规则表。
