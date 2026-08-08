# skill-rebuilds

MMW 的重建区。这里装两样东西，作用完全不同：

| 位置 | 是什么 | 会不会进发布面 |
| --- | --- | --- |
| `candidate/` | **一整套 MMW 的候选副本**：`skills/` 29 个技能 + `cli/` 完整 CLI | 会。验完之后整体替换现役 |
| `<上游技能名>/` | 每个技能的上游翻译基线、翻译审计、和这一轮改了什么的台账 | 不会。它们是**依据**，不是产物 |

## `candidate/` 是什么

它是 `mmw/skills/` 加 `mmw/cli/` 的完整副本，在 review 期间独立演进。现役两边都不动。

**为什么要合成一棵完整的树**，而不是每个技能各存各的候选：技能之间靠 `[...](../mmw-start/x.md)` 这样的相对引用互相指，候选散在各目录时这些引用打不开，只能靠「想象它最终在 `mmw/skills/` 里的位置」来判断对不对。合成一棵树之后，引用真的能解析，接线检查从想象变成可执行——`check-wiring.py` 就是干这个的。

树里的 29 个技能分三种来历，改动自由度不同：

- **已经重建过的**（`mmw-domain-modeling`、`mmw-grilling`、`mmw-improve-codebase-architecture`、`mmw-prototype`、`mmw-research`、`mmw-to-spec`、`mmw-wayfinder`、`wait-what`）：合同已经改过，对应 `<上游技能名>/README.md` 记着改了什么。
- **有上游、复核过保真的**：原样搬进来的现役技能。它们不需要重建，搬进来是为了让这棵树完整、能整体接线。
- **MMW 原创的**（`mmw-planner`、`mmw-to-plan`、`mmw-closing`、`mmw-release`、`mmw-retrieval`、`mmw-verifying-agent-output`）：上游没有对应物，判据只能是 MMW 自己的一致性和这棵树里的移交合同。

## 在这里怎么干活

1. **只改 `candidate/`。** 现役 `mmw/skills/` 和 `mmw/cli/` 在整体替换之前一律不动。
2. **两半一起改。** `candidate/skills/` 和 `candidate/cli/` 是同一个发布面的两半——技能正文精简掉的参数来源和约束，落点常常是 CLI 的帮助文本。只改一半会留下对不上的另一半。
3. **每轮的理由写进 `<上游技能名>/README.md`**，不写进候选正文。候选正文是给将来执行它的 agent 看的，不是给复核这一轮的人看的。MMW 原创技能没有上游目录，理由写进提交信息。
4. **改完跑 `python3 mmw/skill-rebuilds/check-wiring.py`。** 它只判机器能直接判定的四类：相对链接打不开、技能名不存在、启动占位符的角色或组不认识、宿主动作名不认识。方法论对不对、编排合不合理，它不管，也不该让它管。

## 什么时候整体替换现役

`candidate/skills/` 和 `candidate/cli/` 一起替换 `mmw/skills/` 和 `mmw/cli/`，然后按根 `TESTING.md` 跑整段、同步 `AGENTS.md` 里列的五处版本号、更新 `mmw-skill-map.html`。

在那之前，候选区的任何东西都不参与物化，也不改变任何宿主的运行行为。
