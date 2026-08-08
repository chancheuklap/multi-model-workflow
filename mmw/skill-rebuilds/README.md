# skill-rebuilds

MMW 的重建区。这里装两样东西，作用完全不同：

| 位置 | 是什么 | 会不会进发布面 |
| --- | --- | --- |
| `candidate/` | **一整套 MMW 的候选副本**：技能、CLI、Codex runtime、MCP 安装面、Pi package 与源码安装入口 | 会。验完之后整体替换现役 |
| `<上游技能名>/` | 每个技能的上游翻译基线、翻译审计、和这一轮改了什么的台账 | 不会。它们是**依据**，不是产物 |

## `candidate/` 是什么

它是最终 `mmw/` 发布根的候选改动，在 review 期间独立演进。现役发布面不动。未放入 `candidate/` 的文件继续使用现役基线；正式验证时把 candidate 覆盖到一份完整的 `mmw/` 副本上。

**为什么要合成一棵完整的树**，而不是每个技能各存各的候选：技能之间靠 `[...](../mmw-start/x.md)` 这样的相对引用互相指，候选散在各目录时这些引用打不开，只能靠「想象它最终在 `mmw/skills/` 里的位置」来判断对不对。合成一棵树之后，引用真的能解析，接线检查从想象变成可执行——`check-wiring.py` 就是干这个的。

树里的 29 个技能分三种来历，改动自由度不同：

- **已经重建过的**（`mmw-domain-modeling`、`mmw-grilling`、`mmw-improve-codebase-architecture`、`mmw-prototype`、`mmw-research`、`mmw-to-spec`、`mmw-wayfinder`、`wait-what`）：合同已经改过，对应 `<上游技能名>/README.md` 记着改了什么。
- **有上游、复核过保真的**：原样搬进来的现役技能。它们不需要重建，搬进来是为了让这棵树完整、能整体接线。
- **MMW 原创的**（`mmw-planner`、`mmw-to-plan`、`mmw-closing`、`mmw-release`、`mmw-retrieval`、`mmw-verifying-agent-output`）：上游没有对应物，判据只能是 MMW 自己的一致性和这棵树里的移交合同。

## 在这里怎么干活

1. **只改 `candidate/`。** 现役 `mmw/skills/` 和 `mmw/cli/` 在整体替换之前一律不动。
2. **发布合同一起改。** 技能、CLI、宿主 runtime、manifest 与安装入口共同组成发布面。只改一处会留下断开的合同。
3. **每轮的理由写进 `<上游技能名>/README.md`**，不写进候选正文。候选正文是给将来执行它的 agent 看的，不是给复核这一轮的人看的。MMW 原创技能没有上游目录，理由写进提交信息。
4. **改完跑 `python3 mmw/skill-rebuilds/check-wiring.py`。** 它只判机器能直接判定的四类：相对链接打不开、技能名不存在、启动占位符的角色或组不认识、宿主动作名不认识。方法论对不对、编排合不合理，它不管，也不该让它管。

## 什么时候整体替换现役

把 `candidate/` 中的每个路径覆盖到正式 `mmw/` 发布根，然后按根 `TESTING.md` 跑整段、同步 `AGENTS.md` 里列的五处版本号、更新 `mmw-skill-map.html`。

在那之前，候选区的任何东西都不参与物化，也不改变任何宿主的运行行为。

## 发布时连带的合同更新（候选替换现役的同一轮做，不提前）

候选做了几个正确但与现行合同冲突的决定。整体替换现役时，这些必须同步落地，否则文档与实物立刻互相矛盾：

1. **路径合同翻转**：候选技能硬编码产物路径（`docs/specs` 等），候选 CLI 已删 `mmw path`/`mmw skill-path`，`.mmw.json` 的 `paths` 只剩 CLI 自己消费的四个键。根 `AGENTS.md`「技能不硬编码这些值；通过 `mmw` 对应子命令读取」一句要改写。
2. **宿主边界规则改写**：候选对宿主差异采用两种正统写法——派发类动作用 `[[mmw-launch:…]]` 占位块（逐宿主机械不同且多技能复用）；其余宿主能力（发布 HTML、对话内渲染、浏览器走查）用按**能力**分支的条件自然语言，在所有宿主上原样成立。根 `AGENTS.md`「宿主边界」的禁令要改写成「禁止按宿主名分支」，并把这条双轨认定写进去。
3. **五道审**：候选把「合并集成审」并入 ⑤ final 终审（集成调查拆回 `/mmw-integrate`）。`docs/context/review.md` 仍定义六道审，替换时用 `/mmw-domain-modeling` 更新该 leaf。
4. **`mmw-improve-codebase-architecture` 保持 model-invoked**：上游有 `disable-model-invocation: true`；候选去掉它是有意的——`/mmw-diagnosing-bugs` 确认缺 seam 时要能移交到本技能，按 `writing-for-agents/SKILL-MECHANICS.md` 的机制这要求 model-invoked。
5. **`handoff` 与 `writing-for-agents` 正文保持英文**：writing-for-agents 的方法论（leading word 等）依赖英文 pretraining priors，翻译会削弱效果；handoff 随其惯例。这是决定，不是漏译。
6. **`mmw-triage` 不再要求 agent brief 携带 research 索引**：候选两侧（triage 与 to-spec 分诊入口）一致收窄，链路闭合。
7. **`mmw-start` 只允许用户调用**：Claude Code 使用 `disable-model-invocation: true`；Codex 使用 `agents/openai.yaml` 禁止隐式调用；Pi 不识别 Claude Code 的字段，所以物化时从技能索引移出，并生成同名用户命令。下游缺少任务上下文时只报告缺失并停止，不回跳 `mmw-start`。
8. **模型档属于已安装 runtime**：目标仓库的 `.mmw.json` 不再保存模型。源码安装流程从 `cli/mmw.default.json` 为各宿主物化模型选择。同一个目标仓库可由多个宿主共用。
9. **本机安装统一从源码仓库发起**：`mmw/install.sh` 先构建稳定 runtime，再安装 Codex、Claude Code、Pi、headless Codex 方法技能和 Pi/Cursor MCP。`mmw init` 只配置目标仓库。
