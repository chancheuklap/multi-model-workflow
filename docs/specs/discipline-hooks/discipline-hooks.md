---
slug: discipline-hooks
summary: 新增跨宿主 hook 注入层：开场纪律注入、subagent 注入、完成拦截三类事件，宿主缺口按能力降级，install.sh 学会安装第三类交付物
date: 2026-08-25
branch: discipline-hooks
spec_issue: 54
artifact_refs: []
---

# 跨宿主纪律注入层 spec

> 三份一组中的第二份（前有 landing-closeout，后有 landing-orchestrator）。架构决定见 ADR 0021；五宿主 hook 能力与输出形状均经本机实测取证（2026-08-24，取证过程见调研 artifact），蓝本 ponytail 的本地克隆在取证时逐文件阅读。

## Problem Statement

执行纪律（先读后写、反偷懒、反作弊、关卡未清不许收工）目前只能写在技能正文里，送达全靠 agent 自觉。有两个已被记录的失效方式：其一，在 Claude Code 上会话级注入的上下文不进 Task 派生的 subagent（ponytail 为此专门写了 SubagentStart hook，注释点名其 issue #252）——主会话有纪律、实际写代码的 subagent 没有；其二，会话想收工时没有任何兜底拦截，「说做完了就结束」畅通无阻。此外纪律文本一旦多处分发，承重句会在后续改写中静默漂移（ponytail 曾因此逐条钉死四条红线）。

## Solution

给 MMW 增加第三类交付物：hook 注入层。三类事件——开场纪律注入（会话开始时把纪律送进上下文）、subagent 启动注入（堵 #252 那个缺口）、完成拦截（工人会话想结束而票的关卡未清时顶回去）。一份共享 hook JSON 喂 Claude 与 Codex（Grok 会自动扫描兼容配置），Cursor 用它自己的 hooks 文件（合并安装、不覆盖既有条目），pi 写一个小扩展（它的注入口反而最强），Grok 的开场注入走规则文件降级。所有 hook 失败一律 fail-open。承重句用机械校验钉死。

## User Stories

1. As a 维护者, I want 纪律在会话开始时被自动注入而不依赖 agent 记得去读, so that 送达不再靠自觉
2. As a 工人 agent 的 subagent, I want 与父会话相同的纪律注入, so that 实际写代码的那层不是纪律盲区
3. As a 维护者, I want 工人会话在票的关卡未清时无法自然收工, so that 「说做完就走」被机制拦下
4. As a 维护者, I want 同一份纪律文本喂给五个宿主而不是五份手工副本, so that 改一处即处处生效
5. As a 维护者, I want 没有 hook 能力的宿主自动退到规则文件层, so that 技能正文保持五宿主同一份、按能力描述差异
6. As a 维护者, I want 全部 hook 失败时照常放行, so that 注入层的故障永远不会卡死会话
7. As a 维护者, I want install.sh 一条命令装齐 hook 层并在卸载时只清自己的条目, so that 与既有安装体验一致
8. As a 维护者, I want 安装 Cursor hook 时与既有条目合并, so that 本机已在运行的其它 hook 不被覆盖
9. As a 维护者, I want 纪律承重句被机械校验钉住, so that 后续任何改写弄丢关键措辞时校验先红
10. As a 维护者, I want 每条注入纪律的条目有唯一出处（指向纪律存档的章节）, so that 内容审计与替换有据

## Implementation Decisions

**产物清单（全部新建，蓝本为 ponytail 对应文件，存档路径见 Sources）。** ①共享 hook JSON 一份：注册开场、subagent、Stop 三类事件到三个 Node 脚本，格式同时被 Claude 与 Codex 加载（两家 schema 相同；Grok 文档声明跳过不认识的事件名并默认扫描 Claude 的全局配置）。②三个注入脚本：开场注入、subagent 注入（带可选的 agent 类型过滤）、完成拦截。③分流 runtime：按宿主环境特征分发输出 JSON 形状——ponytail 的分流函数只枚举了它接的四家（Copilot、Codex、Qoder、Claude），本层需按本机取证补 Cursor（camelCase 事件与 `additional_context` 响应）、Grok（Stop 的 `decision:block` 三形状）、pi 三家。④pi 扩展一个：注册 `before_agent_start` 返回追加了纪律的系统提示。⑤Grok 降级：规则文件装到 `$GROK_HOME/rules/` 下。全部脚本零第三方依赖、只用 Node 内置模块。

**注入内容与出处。** 注入的纪律文本按角色分块，每块每条标注存档章节出处（`landing-closeout` spec 目录的 `discipline-sources.md`）：工人块 = 反过度构建（第 1 章 ponytail 阶梯与红线）+ 反偷懒（第 2 章 unlazy v1 的禁止输出清单、停止条件、全量报数）；复验者块 = 反作弊（第 3 章 swarm-forge 护栏中的不自造代理指标、不改考卷）。每条纪律写成可执行动作而非描述性劝告（ponytail 的对照实验：同义改写只有可执行版有效）；条目入选与后续增删都要过探针实测门槛，实测时对照组必须显式隔离常驻注入（ponytail 的污染事故教训）。

**完成拦截的判定物。** Stop hook 只能读本地文件，而关卡在票正文里；因此 implement（landing-closeout spec）在开工时把票号与关卡快照写进 worktree 根的一个状态文件，勾选与证据同步其中。拦截逻辑抄 unlazy：状态文件存在且有未清关卡即顶回（输出该宿主的 block 形状），连续多次拦截而文件内容无变化则放行（防困死）；文件缺失、解析失败、超时一律放行（fail-open）。该状态文件同时是编排 spec 里存活判定的副作用信号之一。

**install.sh 扩展。** 沿用既有清单机制：每个目标位置留一份 `.mmw-hooks` 清单，装前按清单清理退役条目，遇到非 MMW 所有的同名内容报冲突并非零退出；Claude/Codex 的 settings 合并写入、Cursor 的 hooks 文件合并写入（本机该文件已有他方条目，覆盖即事故）；`--check` 模式照常只读比对。

**承重句机械校验。** 新脚本比照 ponytail 的副本校验器：一张不变量短语清单（首批：implement「开写之前先读」段的关键句、复验者铁律、四条安全红线、双条件判定句），逐字检查存在于其权威位置；挂进 `install.sh --check` 顺带执行。清单只判「短语逐字存在」这一机器可判事实，符合仓库机械校验边界。

## Testing Decisions

外部可观察行为：①每宿主一条冒烟——起一个会话（或 subagent），确认纪律标记行出现在上下文中；Grok 验规则文件被加载（`--rules` 派发路径在编排 spec 中另验）。②完成拦截用假状态文件做一正一反例：有未清关卡时收工被顶回、全清后放行、文件损坏时放行——runner 形态照 `mmw-v2/skills/<名>/tests/run.sh` 的既有写法（退出码说话、输出不接管道、把子 shell 吞错的四种字样当失败）。③承重句校验自身用「删一个字就红」的反例自证。④install.sh 的 hook 安装走 `MMW_V2_HOME` 临时根练手，不碰真家目录（仓库既有惯例）。

## Out of Scope

- 纪律内容本身的增删与措辞迭代（单源分配已定，变更走探针门槛，另行小改动）
- 编排循环对 hook 的消费（landing-orchestrator spec）
- Copilot、Qoder 等五宿主之外的宿主适配
- 对各宿主未来版本 hook 行为的兼容承诺（以装机实测为准）

## Sources

- ADR 0021（hook 层决定与四产物形态）；**五宿主 hook 能力矩阵：本目录附件 `host-hook-matrix.md`**（本机取证记录，含各宿主输出形状与取证对象路径）；背景综述另见调研 artifact <https://claude.ai/code/artifact/280359df-e0fb-445c-81c6-9bd6882ecd35>
- 蓝本：ponytail <https://github.com/DietrichGebert/ponytail>（@2ed6c52）的 `hooks/` 目录、`pi-extension/`、分流 runtime 与 `scripts/check-rule-copies.js`——实现时按该 commit 克隆取原件
- 完成拦截思想：unlazy <https://github.com/Leonxlnx/unlazy>（main @265fbd5）的 `scripts/stop-hook.mjs`
- 本机取证对象：五宿主 CLI 与配置目录（Claude/Codex 共享 schema、Grok 的兼容扫描与三形状、Cursor 的 hooks 文件、pi 的扩展事件）

## Further Notes

pi 没有结束拦截；它的开场注入事件对 subagent 同样生效（本机扩展测试可证），因此 pi 上不存在 subagent 纪律盲区，只缺收工兜底；Grok 的开场类事件全部被动，其 Stop/SubagentStop 拦截是它唯一的注入口——这两处缺口都按能力语言写进技能与安装文档，不点宿主名做分支。ponytail 的 Windows 会话冻死事故（其 issue #443）转化为本层的硬规则：任何 hook 脚本必须带超时与 stdin 容错，失败即放行。
