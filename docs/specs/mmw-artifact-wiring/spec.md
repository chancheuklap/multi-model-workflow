---
slug: mmw-artifact-wiring
summary: 为 MMW 全部产物定义唯一的路径形状与产物引用合同，让生产产物的技能按合同命名和归档，读取产物的技能按合同找到产物
date: 2026-08-11
branch: mmw-artifact-wiring
spec_issue: 36
artifact_refs:
  - category: research
    name: mmw-artifact-wiring
    issue: 19
    sub: artifact-inventory
  - category: research
    name: mmw-artifact-wiring
    issue: 20
    sub: aidlc-v2-artifact-wiring
  - category: research
    name: mmw-artifact-wiring
    issue: 30
    sub: aidlc-decision-audit
---

# MMW 产物归纳与接线合同 spec

> 这份 spec 来自 Wayfinder map [MMW 产物归纳与接线合同](https://github.com/chancheuklap/multi-model-workflow/issues/18)，工作名 `mmw-artifact-wiring`。它综合了这张 map 下 17 张 decision ticket 的结论，以及由这些结论产生的 14 份 ADR（`docs/adr/0001` 到 `docs/adr/0014`）。
>
> 本 spec 实际使用的 research：
>
> - `docs/research/mmw-artifact-wiring/issue-19/artifact-inventory/README.md`——MMW 产出和使用的产物完整清单。
> - `docs/research/mmw-artifact-wiring/issue-20/aidlc-v2-artifact-wiring/README.md`——`awslabs/aidlc-workflows` v2 的阶段间产物传递机制。
> - `docs/research/mmw-artifact-wiring/issue-30/aidlc-decision-audit/README.md`——前九个决定与 aidlc-workflows v2 的逐节对照复核。
>
> 本 spec 没有使用 prototype 输入。这项 effort 没有做过 prototype。

## Problem Statement

用户在多个仓库里使用 MMW。他描述的问题是三件互相关联的事：MMW 的产物在仓库里没有整齐归纳；生产产物的技能不能让 agent 顺畅且正确地命名和归档；读取产物的技能不能让 agent 顺畅且正确地读取。三件事的共同目的是让 agent 在做某一项工作时拿到足够完整和正确的上下文。

当前状况分四个层面。

**一、没有一条规则说明路径由哪几段构成。** MMW 有 27 类产物，每一类的路径各写各的：research 是 `docs/research/<产物目录>/<主题>/`，审查记录是 `.reviews/<任务 slug>-plan.md`，派发报告是 `.dispatch/<角色>-<task 基名>.md`。一个零上下文的 agent 要写出正确路径，得记住 27 条互不相同的规则。已经查实四处落点不一致，它们是同一个原因的四个表现。

**二、同一件事在仓库里有两个名字。** spec、plan、evidence 和审查记录用任务 slug，prototype、research 和过程材料用产物目录。两个值可以不同，因此同一次交付的产物会散进两个目录。

**三、路径靠手抄传递，漏写没有任何机制发现。** 一份 research 的路径从生产它的那一步被手抄到实现它的 `worker`，中间经过 decision ticket 结论评论、map 的 `Decisions so far`、spec issue 正文、spec、tracer bullet ticket、plan 和四栏 task，共七跳。任何一跳漏写，下游就拿不到那份 research，而且不会有任何检查报错。

**四、这项 effort 自己撞上了同一个问题的两个实例。** 第一个：两张 research ticket 先解，结论保存在仓库里，后面七张 grilling ticket 中只有两张的结论提到过那两份 research；用户在多个会话里被问到本可以由 research 结论回答的问题，而他没有读过那两份报告。第二个：map 正文的决定索引被并发会话整份替换掉两次，两次都靠人工核对行数才发现。

## Solution

MMW 定下一条产物归纳合同，由四件事构成。

**一条路径形状。** 全部产物用同一条公式 `<类别根>/<名字段>/[<范围段>/]<类别内细分>`。agent 只需要知道四件事，不需要记 27 条规则。

**一个名字。** 两个名字合并成一个，叫**工作名**。它在建任务分支时由 CLI 取得并保存，技能跑一条命令读出来，不再各自判断入口。

**一条命令回答落点。** 技能正文不再写路径字面值，改为写类别名和 `mmw artifact path`。取值数据集中在一份文件里，路径规则只在一个进程里执行。

**一种传递形态。** 技能之间不传路径，传**产物引用**——类别、工作名、范围段和类别内细分四项。产物引用写进固定结构（文件头元数据块、issue 正文的固定标题节、四栏 task 的「读」栏），因此可以逐条解析验证。下游拿到产物引用之后自己跑 `mmw artifact path` 解析成路径。

在这四件事之上，另有四项支撑机制：decision ticket 自己声明必读材料，让上游结论传得到下游；长期产物的索引由命令当场算出，读的动作本身就是重建；map 正文的决定索引由 CLI 追加，并发写不再丢行；当场取名的产物在写第一个文件之前查一次重。

## Current State

以下事实支撑本次决定，并会随代码变化。

**产物清单与命名分布**（出处 `docs/research/mmw-artifact-wiring/issue-19/artifact-inventory/README.md`）：MMW 共 27 类产物；长期留在仓库的只有六类；命名只有任务 slug 与产物目录两个来源，两者互不统一；`.mmw.json` 的 `specs`、`plans`、`prototypes`、`research`、`evidence` 五项没有消费方，而且 `mmw init` 已经在主动删除它们（`mmw/cli/lib/init.sh:61-62`）。

**技能源里的路径字面值处数**（本次在 `mmw/skills-src/` 下逐项统计，排除 `mmw-setup/`）：

| 字面值 | 行数 |
| --- | --- |
| `.out-of-scope/` | 29 |
| `.scratch/` | 28 |
| `docs/specs/` | 24 |
| `docs/adr/` | 18 |
| `docs/plans/` | 17 |
| `docs/context/` | 14 |
| `.reviews/` | 14 |
| `docs/prototypes/` | 7 |
| `docs/research/` | 6 |
| `docs/evidence/` | 5 |
| `.dispatch/` | 5 |
| `<产物目录>` 占位符 | 27 |

30 个技能中有 20 个包含上列任意一项。

**CLI 当前形态**：`mmw` 有 `dispatch`、`agents`、`skills`、`task`、`result`、`issue`、`wiki`、`domain`、`graph`、`mcp`、`release`、`doctor`、`init` 十三个子命令，没有 `artifact`。`mmw/cli/lib/issue.sh` 只有 create、claim、link、children、frontier 五个动作，没有编辑 issue 正文的动作，也没有给已存在 issue 设置父 issue 的动作。`mmw doctor` 当前没有任何测试覆盖（`grep -n "doctor" mmw/test.sh mmw/cli/tests/*.sh` 零命中，由 decision ticket #26 核实）。

**测试当前形态**：`mmw/test.sh` 调用 14 份测试，其中 `mmw/cli/tests/` 下有 `guardrails.sh`、`test_issue.sh`、`test_wiki.sh`、`test_domain.sh`、`test_init.sh`、`test_skill_refs.sh` 六份 bash 测试。

**GitHub 的两项实测结论**（decision ticket #35 当场实测）：对 `PATCH /repos/{owner}/{repo}/issues/{n}` 带 `If-Match` 头返回 400，错误原文 `"Conditional request headers are not allowed in unsafe requests unless supported by the endpoint"`；同一请求去掉该头返回 200。GraphQL 的 `userContentEdits` 能取得 issue 正文的完整编辑历史，每个版本带 `editedAt`、`editor` 和当时的完整正文。

**MMW 源码仓库与目标仓库同一套落点**：`mmw init` 不复制任何 leaf 到目标仓库。它的领域上下文那一步是 `mmw_init_domain_context`，只调用 `mmw_domain_sync all` 往 `AGENTS.md`、`CONTEXT-MAP.md` 和 `CLAUDE.md` 三处写规则块，不写 leaf 内容。所以 `docs/context/artifact-location.md` 只存在于 MMW 源码仓库，不能充当技能在目标仓库里查落点的那一处。

## User Stories

### 写出正确的落点

1. 作为一个刚接手一项工作的 agent，我希望只要知道产物类别和工作名就能得到正确路径，以便不用记住每一类产物各自的规则。
2. 作为一个 agent，我希望路径由一条命令回答，以便技能正文改动时我不会拿到过期的路径示例。
3. 作为一个 agent，我希望这条命令在我给出认不出的类别名时列出全部合法类别名，以便我立刻知道正确写法，而不是去试别的拼法。
4. 作为一个 agent，我希望这条命令在我问一个不写文件的产物类别时告诉我这类产物不落盘，以便我不去创建一个不该存在的文件。
5. 作为一个 agent，我希望这条命令在我问一个不套路径形状的产物类别时告诉我该问哪条命令，以便我不误以为是自己拼错了类别名。
6. 作为一个 agent，我希望这条命令永远不回退到某个默认路径，以便我的错误当场暴露，而不是在别处写出一个错位的产物。
7. 作为一个 agent，我希望查询路径不产生任何副作用，以便我只是问一下 spec 在哪的时候不会在仓库里留下一个空目录。
8. 作为一个 agent，我希望命令默认输出仓库相对路径，以便我把它写进 issue 评论、spec 和交回报告时不会带上只在本机成立的绝对路径。
9. 作为一个 agent，我希望在已经绑定的任务工作树里可以不写工作名，以便我处理当前这次交付的产物时少一个出错点。
10. 作为一个 agent，我希望读别的交付的产物时必须显式给出工作名，以便我不会误把别人的产物当成自己的。
11. 作为一个 agent，我希望不带参数运行时能看到全部类别名和参数说明，以便我在技能正文之外也有一处可查。
12. 作为一个 agent，我希望命令逐段校验我给出的类别内细分，以便不合法的字符在写入文件之前就被挡住。

### 一个名字贯穿一次交付

13. 作为一个 agent，我希望一次交付的全部产物共用一个名字，以便同一次工作的 research、prototype 和 spec 落在同一个目录下，互相找得到。
14. 作为一个 agent，我希望工作名由一条命令读出，以便我不用判断自己是从哪个技能入口进来的。
15. 作为一个开发者，我希望工作名与任务分支名是两个值，以便一项 Wayfinder effort 的多条任务分支仍然共用一个产物目录。
16. 作为一个开发者，我希望工作名不带改动类型前缀，以便同一件事的产物不会因为改动类型变化而被拆到两个目录。
17. 作为一个 agent，我希望在不是任务工作树的地方要写仓库文件时被要求先建任务工作树，以便一次讨论的共同理解记录和它谈出的 spec 不会落在两个目录里。
18. 作为一个在 monorepo 里工作的开发者，我希望项目标识写进工作名而不是新增一层路径，以便路径形状保持四段不变。

### 找到自己需要的产物

19. 作为一个 agent，我希望上游用产物引用点名我该读的产物，以便我不必从一条可能已经过期的路径字面值去猜。
20. 作为一个 agent，我希望产物引用写在固定结构里而不是散文里，以便机器能逐条解析它。
21. 作为一个 agent，我希望上游即使没有产物要传也写出那一节并写「无」，以便我能分辨「上游说没有」和「上游忘了写」。
22. 作为一个 agent，我希望点名的粒度到产物索引为止，以便我能沿着索引读它列出的文件，而不需要上游把每个文件都抄一遍。
23. 作为一个 agent，我希望在读不到该有的那一节时停下报缺，以便我不会靠猜继续往下做。
24. 作为一个开发者，我希望有一条命令能校验仓库里 spec 与 plan 声明的产物引用是否都解析得到，以便漏写在提交之前被发现。
25. 作为一个开发者，我希望这条校验只校声明层，不校某一次运行的文件有没有落到磁盘，以便被跳过的上游不会造成必然失败的检查。

### 上游的结论传得到下游

26. 作为一个认领 decision ticket 的 agent，我希望这张 ticket 自己写着必须读哪几件材料，以便我不会漏掉已经查清楚的事实又跑去问用户。
27. 作为用户，我希望 agent 在提问之前先看被点名的材料里有没有答案，以便我不必回答一个已经有更好答案的问题。
28. 作为一个建 decision ticket 的 agent，我希望我能写下当时已知的材料，而认领它的 agent 在开工前补进后来产生的材料，以便这份声明在 fog 逐步驱散的过程中仍然有效。
29. 作为一个补全必读材料声明的 agent，我希望有一条命令列出这项 effort 名下已有的产物，以便我从清单里挑，而不凭记忆。
30. 作为用户，我希望结论里逐条写明每项必读材料用上了没有，以便我看得出哪一项被跳过以及为什么。
31. 作为一个打开一份长 research 报告的 agent，我希望索引里有一份逐节说明各节内容的地图，以便我在十二节里找得到自己要的那一节。
32. 作为一个 agent，我希望这份章节地图只指路不限定我读哪几节，以便它不会裁剪掉我本该看到的内容。

### 长期产物的清单

33. 作为一个 agent，我希望有一条命令列出这个仓库全部 ADR 的编号、标题、日期和改写关系，以便我按 `AGENTS.md` 的要求挑出与本次范围相关的那几份，而不是只看得到一串文件名。
34. 作为一个 agent，我希望这份清单是命令当场算出的，以便它永远不会因为有人忘了重建而过期。
35. 作为一个不使用 agent 的人，我希望仓库里有一份清单文件，以便我在网页上打开 `docs/adr/` 时看得到内容而不是只看到文件名。
36. 作为一个开发者，我希望这条命令只在算出的内容与文件不同时才写文件，以便它跑完之后我的工作区通常是干净的。
37. 作为一个 agent，我希望 spec 索引与 ADR 索引是同一种形态，以便我不需要为两类产物记两套做法。

### map 的决定索引不丢行

38. 作为一个解完 decision ticket 的 agent，我希望有一条命令把我这一行追加进 map 正文，以便我不用自己拼整份正文写回。
39. 作为一个 agent，我希望这条命令在写回之后比对上一版的全部行，以便别人的行被我顶掉时命令自己发现。
40. 作为一个 agent，我希望命令发现丢行时自己重做，以便我不需要人工介入。
41. 作为一个 agent，我希望重做用尽次数之后命令非零退出，以便失败不会被静默吞掉。
42. 作为用户，我希望这条命令的小节标题是参数而不是为 map 写死，以便将来出现第二个并发编辑点时命令现成可用。

### 撞名挡得住

43. 作为一个正要保存 research 的 agent，我希望在写第一个文件之前发现这个名字已经被占用，以便同一次交付里上一份 research 不会被我写没。
44. 作为一个 agent，我希望发现撞名之后重新取一个承载差别的名字，以便两份产物的名字各自说明它答的是哪个问题。
45. 作为一个 agent，我希望只有当场取名的类别才查重，以便固定文件名和由分配器给号的类别不做无用的检查。
46. 作为用户，我希望撞名由 agent 自动处理，以便我不必为一个取名问题被打断。

### 废除不再需要的东西

47. 作为一个开发者，我希望 spec 与 plan 长期留在仓库里，以便它们与代码在同一条 Git 历史上，能通过提交和 PR 关联到实现。
48. 作为一个开发者，我希望不再需要维护 Wiki 归档，以便同一份内容不会有两个长期落点和一条同步规则。
49. 作为一个 agent，我希望四栏 task 与角色报告不写文件，以便我不必记住两个用完即弃的中间物各自的落点。
50. 作为一个开发者，我希望 `.mmw.json` 只保留真正可配置的四项，以便配置文件里不再有已经没有消费方的项。
51. 作为一个改过 `.mmw.json` 的人，我希望 `mmw doctor` 报出已经退役的配置项，以便我知道自己配的东西为什么不生效。
52. 作为一个在有历史产物的仓库里工作的开发者，我希望 `mmw doctor` 列出新合同下不该存在的路径，以便我知道要人工处理什么。
53. 作为一个开发者，我希望这些报告不改变 `mmw doctor` 的退出码，以便我不会为了让它通过而去删东西。

### 机械校验守住边界

54. 作为一个维护 MMW 的开发者，我希望技能源里出现「类别根加占位符」的写法时测试变红，以便路径字面值不会重新爬回技能正文。
55. 作为一个维护 MMW 的开发者，我希望技能源里出现工作目录根的默认取值时测试变红，以便可配置的取值不会被写死。
56. 作为一个维护 MMW 的开发者，我希望机械校验不用豁免清单撑着，以便它保持是一条可解释的规则而不是一张例外表。
57. 作为一个维护 MMW 的开发者，我希望产物质量、方法选择和完成度不进机械校验，以便计数和列表形状不会冒充成检查。

## Implementation Decisions

### 1. 路径形状

全部产物使用一条路径形状：

```
<类别根>/<名字段>/[<范围段>/]<类别内细分>
```

| 段 | 由什么决定 |
| --- | --- |
| 类别根 | 产物类别。一个类别根只放一类产物 |
| 名字段 | 工作名。全部产物只有这一个名字位置 |
| 范围段 | 只有 Wayfinder decision ticket 有，值是 `issue-<编号>` |
| 类别内细分 | 类别自己的规则。一律用目录，不用文件名前缀 |

四段共用一条**安全路径段**规则：单个路径段，首字符是字母或数字，其余只能是字母、数字、点、下划线、连字符，不含斜杠，一律小写。「一律小写」是本次新增的一条——macOS 默认文件系统不区分大小写而 Linux 区分，混用会在两台机器上表现不同。

subagent 派发不产生自己的落点。subagent 在派它的那个任务的工作树里工作，写出的产物用同一套形状；名字段和范围段由派发方在四栏 task 的正文里给出。

### 2. 产物落点数据

取值数据集中在新建的 `mmw/cli/artifacts.json`。每个类别一条记录，字段如下：

| 字段 | 取值 | 用途 |
| --- | --- | --- |
| `root` | 路径字符串，或 `.mmw.json` 的 `paths` 键名 | 类别根 |
| `root_kind` | `fixed` 或 `workdir` | `fixed` 是固定类别根，目标仓库不可改；`workdir` 是工作目录根，取值读目标仓库配置 |
| `has_name` | 布尔 | 这一类带不带名字段。ADR、leaf、否决记录是仓库级产物，不带 |
| `allows_scope` | 布尔 | 这一类允不允许范围段 |
| `sub_naming` | `ad-hoc`、`fixed-file`、`allocated` 或 `one-per-concept` | 类别内细分的取名方式。`ad-hoc` 是当场取名，只有它要在写文件之前查重 |
| `sub_fixed` | 字符串数组 | 这一类允许的类别内细分取值。只有一个值时 `--sub` 可以缺省，命令直接用它。空数组表示取值由调用方给 |
| `sub_pattern` | 正则，可选 | 取值带日期或序号时用它校验，例如集成记录的 `integration-<日期>` |
| `status` | `active`、`no-file`、`not-shaped`、`external` 或 `tracker` | 见下方两张表 |
| `answered_by` | 命令名，仅 `not-shaped` 有 | 这一类由哪条命令回答 |

`sub_fixed` 与 `sub_pattern` 是本 spec 在 ① spec 审之后补上的两个字段。只有 `sub_naming` 的话，数据只说得出「这一类是固定文件名」，说不出那个名字是什么，`mmw artifact path spec` 就得在代码里再写死一次 `spec.md`，产物落点数据也就当不成唯一事实来源。

类别名用英文小写标识符。九个 `active` 类别：

| 类别名 | 类别根 | `root_kind` | `has_name` | `allows_scope` | `sub_naming` |
| --- | --- | --- | --- | --- | --- |
| `spec` | `docs/specs/` | `fixed` | 是 | 否 | `fixed-file` |
| `plan` | `docs/plans/` | `fixed` | 是 | 否 | `allocated` |
| `prototype` | `docs/prototypes/` | `fixed` | 是 | 是 | `ad-hoc` |
| `research` | `docs/research/` | `fixed` | 是 | 是 | `ad-hoc` |
| `adr` | `docs/adr/` | `fixed` | 否 | 否 | `allocated` |
| `context` | `docs/context/` | `fixed` | 否 | 否 | `one-per-concept` |
| `context-map` | 仓库根 | `fixed` | 否 | 否 | `fixed-file` |
| `out-of-scope` | `.out-of-scope/` | `fixed` | 否 | 否 | `one-per-concept` |
| `scratch` | `paths.scratch` | `workdir` | 是 | 是 | `fixed-file` |
| `review` | `paths.reviews` | `workdir` | 是 | 否 | `fixed-file` |

`context-map` 与 `context` 是两个类别，不是一个。领域文档把 Context Map（`docs/context/project-context.md:11`）与 leaf（同文件:15）定义为两个概念，而 `context` 类别的类别根是 `docs/context/`，它回答不了仓库根上的 `CONTEXT-MAP.md`。

各类别的 `sub_fixed` 与 `sub_pattern`：

| 类别名 | `sub_fixed` | `sub_pattern` |
| --- | --- | --- |
| `spec` | `["spec.md"]` | 无 |
| `context-map` | `["CONTEXT-MAP.md"]` | 无 |
| `review` | `["understanding.md", "spec.md", "plan.md", "final.md"]` | `^integration-\d{4}-\d{2}-\d{2}(-\d+)?\.md$`，用于集成记录 |
| `scratch` | `["understanding.md", "evidence", "questionnaire", "wizard", "diagnosis", "architecture-review", "dispatch", "outbox"]`，只约束第一层 | 无。第二层由技能自由取，按安全路径段校验 |
| `plan` | `[]` | `^\d{2}-[a-z0-9][a-z0-9._-]*\.md$`，两位编号加 ticket 短名 |
| `adr` | `[]` | `^\d{4}-[a-z0-9][a-z0-9._-]*\.md$`，或 Wayfinder 期间的 `^draft-\d+-[a-z0-9][a-z0-9._-]*\.md$` |
| `prototype`、`research`、`context`、`out-of-scope` | `[]` | 无。取值由调用方给，按安全路径段校验 |

`sub_fixed` 只有一个值时，`--sub` 可以缺省，命令直接用那个值。这是 `mmw artifact path spec --name X` 能返回 `docs/specs/X/spec.md` 的依据。

**`context-map` 的类别根是仓库根，在数据里写成空字符串。** 上表那一格写「仓库根」是给人读的说法，数据里的 `root` 取 `""`。拼接时空字符串不产生目录段，`mmw artifact path context-map` 的相对路径输出就是 `CONTEXT-MAP.md`，不带前导斜杠也不带 `./`。落点字面值校验解析固定类别根清单时跳过空 `root`：仓库根不构成可扫描的目录前缀，把空值当前缀会让正则匹配到任意占位符。

`scratch` 标 `fixed-file` 是一处需要说明的判断。它的第一层细分是固定的一组名字（`understanding.md`、`evidence/`、`questionnaire/`、`wizard/`、`diagnosis/`、`architecture-review/`、`dispatch/`、`outbox/`），第二层才由技能当场取。标 `ad-hoc` 会让每一次 scratch 查询都输出查重提醒，而 `0011-artifact-reference-collision.md` 查实真正会撞的只有 research 主题名与 prototype 变体组两处。取舍是：scratch 的第二层撞名不做查重，代价由「scratch 不进 Git、任务结束清理」兜住——撞名波及不到任何长期产物。

`status` 不是 `active` 的类别也必须列在这份数据里，否则 agent 拿到「认不出的类别名」这个回应会以为是自己拼错了，转而去试别的写法：

| 类别名 | `status` | 回应 |
| --- | --- | --- |
| `task`（四栏 task） | `no-file` | 这类产物不写文件，正文经标准输入传给 `mmw dispatch` |
| `agent-report`（角色报告） | `no-file` | 这类产物不写文件，正文走 subagent 的标准输出 |
| `release-state`、`release-artifact`、`delivery-record` | `not-shaped` | 由 `mmw release` 回答 |
| `graph` | `not-shaped` | 由 `mmw graph` 回答 |
| `worktree` | `not-shaped` | 由 `mmw task` 回答 |
| `handoff` | `external` | 这一类落在操作系统临时目录，不在仓库里 |
| `explanation`（`/wait-what` 的解释 HTML） | `external` | 这一类的位置由用户指定 |
| `map`、`decision-ticket`、`conclusion-comment`、`handback-comment`、`spec-issue`、`tracer-ticket`、`agent-brief` | `tracker` | 这一类落在 issue tracker 上，不占仓库路径，用 `gh issue view <编号>` 访问 |

`external` 与 `tracker` 是本 spec 在 ① spec 审之后补上的两种 `status`。少了它们，agent 问 handoff、解释 HTML 或任何一种 tracker 产物时会得到「认不出的类别名」，而这正是这份数据要消除的那种失败——它会让 agent 以为是自己拼错了类别名，转而去试别的写法。`answered_by` 只能填命令名，表达不了「操作系统临时目录」和「用户指定位置」，所以这两类各用自己的 `status` 而不是塞进 `not-shaped`。

### 3. 逐类落点

长期留在仓库：

| 产物 | 落点 |
| --- | --- |
| Context Map、leaf | `CONTEXT-MAP.md`、`docs/context/<context>.md` |
| ADR | `docs/adr/<四位编号>-<短名>.md`。Wayfinder 期间先写 `docs/adr/draft-<ticket 编号>-<短名>.md` |
| prototype 资产 | `docs/prototypes/<工作名>/[issue-<编号>/]`，内部保持现状 |
| research | `docs/research/<工作名>/[issue-<编号>/]<主题>/`，内部保持现状 |
| spec | `docs/specs/<工作名>/spec.md` |
| spec 索引副本 | `docs/specs/README.md` |
| ADR 索引副本 | `docs/adr/README.md` |
| plan | `docs/plans/<工作名>/<两位编号>-<ticket 短名>.md` |
| 否决记录 | `.out-of-scope/<概念>.md` |

不进 Git，任务结束清理：

| 产物 | 落点 |
| --- | --- |
| 共同理解记录 | `<scratch 根>/<工作名>/[issue-<编号>/]understanding.md` |
| 界面验收证据 | `<scratch 根>/<工作名>/[issue-<编号>/]evidence/` |
| questionnaire | `<scratch 根>/<工作名>/[issue-<编号>/]questionnaire/<主题>.md` |
| wizard 脚本 | `<scratch 根>/<工作名>/[issue-<编号>/]wizard/<流程>.sh` |
| bug 诊断材料 | `<scratch 根>/<工作名>/[issue-<编号>/]diagnosis/<短名>/` |
| 架构候选报告 | `<scratch 根>/<工作名>/[issue-<编号>/]architecture-review/<时间戳>.html` |
| 派发进度日志 | `<scratch 根>/<工作名>/[issue-<编号>/]dispatch/<角色>-<时间戳>.log` |
| 待发出的正文 | `<scratch 根>/<工作名>/[issue-<编号>/]outbox/<文件名>` |
| 审查记录 | `<reviews 根>/<工作名>/<哪一道>.md`，`<哪一道>` 取 `understanding`、`spec`、`plan`、`final` |
| 集成记录 | `<reviews 根>/<工作名>/integration-<日期>.md`，同一天第二轮在日期后加序号 |

`outbox/` 是第 19 节改写技能源落点时补上的第八个细分。`mmw issue create --body-file` 与 `gh issue comment --body-file` 都要一个真实文件，所以 spec issue 正文、tracer bullet ticket 正文、map 正文和 decision ticket 的结论评论正文必须先落盘。改写前它们直接写在 `<scratch 根>/<工作名>/` 第一层；第一层收成固定清单之后，这四类文件在原有七个细分里没有落处。借用 `evidence/` 会让读技能的 agent 把待发出的 issue 正文当成界面验收证据。

不套路径形状：出包状态 `<release 根>/release-state.json`、出包阶段产物 `<release 根>/release-artifacts/a<序号>-<stage>/`、交付记录 `<release 根>/delivered/<产品名>.json`、结构图谱 `graphify-out/`、任务工作树 `<worktrees 根>/<任务分支 slug>`。它们跨任务存在，身份由产品名、attempt 序号或分支名决定。

两个例外：handoff 文档留在操作系统临时目录，它用于当前工作区不可用时接续会话；`/wait-what` 的解释 HTML 由用户指定位置。

落在 issue tracker、不占仓库路径：map、decision ticket、结论评论、spec issue、tracer bullet ticket、agent brief。

**落点锚定工作名，不锚定生产它的技能。** 一次交付有多条任务分支，按生产者归类会把同一次交付的 research、prototype 和 spec 散进多个目录。

### 4. `mmw artifact path`

新增子命令 `mmw artifact`，第一个动作是 `path`：

```
mmw artifact path <类别> [--name <工作名>] [--issue <编号>] [--sub <类别内细分>] [--absolute]
```

| 项 | 行为 |
| --- | --- |
| 输出 | 默认仓库相对路径，`--absolute` 输出绝对路径 |
| 副作用 | 没有。只回答路径，不建目录 |
| `--name` 缺省 | 读 `mmw task state` 的工作名。不在任务工作树、或读不到工作名时报错退出，不回退默认值 |
| `--issue` | 值是纯编号，命令拼成 `issue-<编号>`。类别的 `allows_scope` 为假时给了它就报错 |
| `--sub` | 命令按安全路径段规则逐段校验 |
| 无参运行 | 输出用法，打成两列表：左列类别名，右列 leaf 定义的中文术语 |

三种失败各自不同，都不回退默认值：

| 输入 | 回应 |
| --- | --- |
| 认不出的类别名 | 报错，列出全部合法类别名 |
| `status` 是 `no-file` 的类别 | 报错，说明这类产物不写文件 |
| `status` 是 `not-shaped` 的类别 | 报错，指出由 `answered_by` 记的那条命令回答 |
| `status` 是 `external` 的类别 | 报错，说明这一类落在仓库外，并写出它在哪（操作系统临时目录，或由用户指定） |
| `status` 是 `tracker` 的类别 | 报错，说明这一类落在 issue tracker 上，用 `gh issue view <编号>` 访问 |
| `--sub` 不在 `sub_fixed` 里，也不匹配 `sub_pattern` | 报错，列出这一类允许的取值或模式 |

类别的 `sub_naming` 是 `ad-hoc` 时，命令在路径之后另起一行输出查重提醒，内容是「这一类的名字当场取，写第一个文件之前先列一次父目录」。提醒走标准错误，不进标准输出，以便调用方直接把标准输出当路径用。

### 5. 工作名

工作名是一次工作的全部产物共用的名字，也就是填进名字段的值。它与任务分支名是两个值：工作名标识产物归哪次交付，任务分支名标识改动在哪条线上。一次交付可以有多条任务分支，但只有一个工作名。

| 项 | 决定 |
| --- | --- |
| 在哪取 | 建任务分支时。`mmw task new` 与 `mmw task bind` 增加工作名参数 |
| 存在哪 | 由 CLI 保存在任务工作树的绑定信息里，`mmw task state` 增加工作名输出位 |
| 怎么读 | 技能跑一条 `mmw task state`，不再各自判断入口 |
| 边界 | 一次交付。从默认分支新开任务工作树时必须给新值；带 `--from` 从已有任务工作树分叉时继承父分支的值 |
| 形态 | 不带 `feat-`、`fix-`、`refactor-` 这类改动类型前缀。同一件事的改动类型会变，前缀会把同一件事的产物拆到两个目录 |
| 两次交付取到同一个值 | 加区分词，不加序号 |
| monorepo | 不新增项目段。项目标识写进工作名 |

`mmw task state` 返回 `local` 或 `outside` 时没有地方存工作名。因此任何要往仓库写文件的技能，发现这两种返回值时先建任务工作树并定工作名，再开始工作。不保留「用临时名字只写 scratch」的做法——那条路会让一次讨论的共同理解记录和它谈出的 spec 落在两个目录里。

**已经存在的任务工作树怎么补上工作名。** 当前 `mmw_task_state` 完全从 Git 推导状态，没有任何地方保存工作名。改造落地的那一刻，本机上每一棵已绑定的任务工作树都读不出工作名，而 `mmw task state` 是 `/mmw-integrate`、`/mmw-release`、`/mmw-closing`、`/mmw-implement`、`/mmw-to-plan` 五个技能的前置门。补法是在已绑定的树上重跑 `mmw task bind <当前任务分支名> <目标原文> --name <工作名>`：它写入绑定信息，不建分支也不动提交。读不出工作名时的诊断信息要点名这条命令和当前分支名，让 agent 直接照着跑。不做静默默认值，也不用分支名当替代——工作名和任务分支名是两个值，猜出来的那个会把产物写到错的目录。

**只读角色在主检出上派发时算不出落点。** `mmw dispatch` 不给 `--cwd` 时工作目录就是当前检出（`mmw/cli/mmw:282`），技能源里有六处 `none` 模式的派发走这条路。主检出上 `mmw task state` 返回 `local`，落点命令必然失败。决定是：**派发进度日志算不出落点时不写日志，派发照常进行**，命令把这一句写到标准错误。理由是日志是诊断材料，不是派发的前置条件；让整次派发因为算不出一个日志目录而失败，代价大于收益。这不是静默默认值——它不回退到某个猜出来的路径，而是明确不写并说明原因。

### 6. 产物引用

技能之间传产物引用，不传路径字面值。产物引用由四项构成：

| 项 | 说明 |
| --- | --- |
| 类别 | `mmw artifact path` 的类别名 |
| 工作名 | 缺省时是当前交付的工作名 |
| 范围段 | 只有 Wayfinder decision ticket 有，写纯编号 |
| 类别内细分 | 没有细分的类别不写 |

举例，这项 effort 的 aidlc research 是：类别 `research`、工作名 `mmw-artifact-wiring`、范围段 `20`、类别内细分 `aidlc-v2-artifact-wiring`。

**声明写在固定结构里，不写在散文里。** 五个位置：

| 位置 | 写在哪 |
| --- | --- |
| spec 文件 | 文件头元数据块的 `artifact_refs` 字段 |
| plan 文件 | 文件头元数据块的 `artifact_refs` 字段 |
| spec issue 正文 | `## 产物引用` 一节 |
| tracer bullet ticket 正文 | `## 产物引用` 一节 |
| 派 `worker` 的四栏 task | 「读」栏 |

生产方一律写出这一节，没有内容写「无」。这样下游能分辨「上游说没有」和「上游忘了写」。

**书写形态按落点分两种，都不使用路径字面值。**

spec 与 plan 的元数据块是 YAML，用映射列表：

```yaml
artifact_refs:
  - category: research
    name: mmw-artifact-wiring
    issue: 20
    sub: aidlc-v2-artifact-wiring
```

issue 正文的 `## 产物引用` 节、必读材料声明和四栏 task 的「读」栏是 Markdown，用一条一行的键值形态：

```
- category=research name=mmw-artifact-wiring issue=20 sub=aidlc-v2-artifact-wiring
```

键名与 YAML 那一种、与命令参数三者一致。类别不需要 `issue` 或 `sub` 时不写那个键。tracker 产物（decision ticket 的结论评论）写 issue 编号，形态是 `- issue=33 结论评论`——它落在 tracker 上，没有类别与工作名。

「无」的写法也固定：YAML 里是空列表 `artifact_refs: []`，Markdown 里是该节下单独一行 `无`。两种都表示上游明确说没有，与「上游忘了写这一节」区分得开。

选键值形态而不是自然语言短语，是因为它读起来不像路径、写起来不会各写各的，而且将来要机器逐条解析时不用再改一遍全部生产方。

**解析发生在下游。** 拿到产物引用的那一方自己跑 `mmw artifact path`。MMW 没有引擎那一层能在上游解析好再注入下游上下文，所以拿到产物引用的下游必须能运行这条命令。

**点名的粒度到产物索引为止。** 上游点名一件产物，粒度到那份 `README.md`；索引显式列出的文件允许沿着读。禁止的事一条不减：不列目录、不读上级目录、不读索引没列的文件、不读落选变体。判据从「这条路径是不是 task 抄来的」改为「这条路径是不是本次点名那件产物的索引列出的」。

### 7. 元数据块

三类文件的文件头写 YAML 元数据块。

**spec**（六个字段）：

```yaml
---
slug: <工作名>
summary: <一句话说明这份 spec 交付什么>
date: <YYYY-MM-DD>
branch: <任务分支名>
spec_issue: <spec issue 编号>
artifact_refs:
  - category: research
    name: mmw-artifact-wiring
    issue: 20
    sub: aidlc-v2-artifact-wiring
---
```

**plan**（两个字段）：`ticket` 记对应 tracer bullet ticket 的 GitHub issue 编号，`artifact_refs` 形状同上。plan 文件名里的两位编号是拆 ticket 时的顺序编号，不是 issue 编号。

**ADR**（两个字段）：

```yaml
---
date: <YYYY-MM-DD>
amends: [3, 7]
---
```

`amends` 列这份 ADR 改写了哪几份 ADR 的编号，没有改写写 `[]`。ADR 元数据块不重复编号与标题：编号取自文件名，标题取自一级标题。同一项事实存两处会不一致，而这两项从文件本身就读得到。「被谁改写」由索引命令从各份的 `amends` 反向算出，不写第二个字段。

`artifact_refs` 的四个键与命令参数一一对应：`category` 对类别、`name` 对 `--name`、`issue` 对 `--issue`、`sub` 对 `--sub`。`issue` 与 `sub` 在类别不需要时不写。不使用把四项拼成一串的紧凑写法——那种写法看起来像路径，会诱导人当路径用。

**`name` 在元数据块与 issue 正文里必填，不允许缺省。** 命令行的 `--name` 可以缺省（由命令读 `mmw task state`），但那是一次性求值；元数据块与 issue 正文是持久化的声明，一年后可能在另一次交付的任务工作树里被读取，那时缺省会解析成读取者的工作名而不是写下它的那次交付。`mmw artifact check` 是仓库级的，它读全部 spec 与 plan，那时根本没有「当前工作名」可言。ADR `0007` 定的缺省规则只涵盖命令行参数，本 spec 把这条边界写明。

### 8. tracker 正文的固定标题

tracker 正文中被下游按位置读取的节必须固定标题。生产方规定字面，读取方引用同一字面。

| 对象 | 固定标题的节 |
| --- | --- |
| map 正文 | `## Destination`、`## 工作名`、`## 分支`、`## Notes`、`## Decisions so far`、`## Not yet specified`、`## Out of scope` |
| decision ticket 正文 | `## Question`、`## 必读材料声明` |
| 结论评论 | `## 答案`、`## 产物引用`、`## 材料使用记录` |
| 交回评论 | `## 交回` |
| spec issue 正文 | `## 工作名`、`## 输入出处`、`## 产物引用` |
| tracer bullet ticket 正文 | `## 产物引用` |

**中英文混用按一条规则收口**：上游 wayfinder 技能定义的节标题保留上游字面（`Destination`、`Notes`、`Decisions so far`、`Not yet specified`、`Out of scope`、`Question`），MMW 自己新增的节用中文。改上游字面要先走 `upstream-skill-fidelity`，收益不足以抵消那道流程。

**结论评论与交回评论各有一个固定标识**，写在评论正文第一行，用 HTML 注释：

| 评论 | 标识 |
| --- | --- |
| 结论评论 | `<!-- mmw:conclusion -->` |
| 交回评论 | `<!-- mmw:handback -->` |

用 HTML 注释是因为它在 GitHub 页面上不显示，不干扰人阅读，而 `gh issue view <编号> --json comments` 取回的是原始正文，标识在里面，可以精确定位。补充说明性质的评论不给标识，它们没有消费方。

不给标识时两类评论只能靠语义或位置找：结论评论现在靠「写结论的那条」（`mmw-to-spec/SKILL.md:22`），交回评论靠「最后一条评论」（`mmw-wayfinder/closing.md:9` 与 `walking.md:92`），而 `walking.md:75` 本身就允许别的会话往同一张 ticket 追加评论。交回评论里的分支名、HEAD SHA 和基点 SHA 三个值是 `mmw result verify` 与 `mmw result integrate` 的输入，取错就是在错的基点上合并代码。这三个值写在 `## 交回` 一节里，每个值一行，行首是固定的中文字段名。

map 正文的 `## 产物目录` 改名为 `## 工作名`。spec issue 正文的 `## 工作名` 与 `## 输入出处` 是本次补上的两条断链：`mmw-closing/SKILL.md:96` 按节读前者而 `/mmw-to-spec` 从没写过，`mmw-to-tickets/SKILL.md:24` 按节读后者而 `/mmw-to-spec` 没承诺有这一节。这两节的生产方是 `/mmw-to-spec`，跟 `## 产物引用` 一起在发布 spec issue 那一步写出，同属一份 plan 的改动。

**结论评论那一节从「资产精确路径」改名为 `## 产物引用`，内容也跟着换。** 原来那一节写的是仓库路径字面，与本 spec 的核心合同直接矛盾——必读材料声明指向结论评论只传 issue 编号，下游按编号打开评论，结果拿回来的还是路径。改成产物引用之后，这条链上的每一跳都不再传路径，下游用 `mmw artifact path` 解析。另一个理由是术语：`docs/context/artifact-location.md:45` 把「精确路径」列在产物引用条目的 `_Avoid_` 里，而这是要写进 tracker 的固定字面。

spec 的路径字面要求出现在 spec issue 正文里，但不固定成节：`mmw-start/resuming.md:22` 拿它当搜索词反查 issue，要的是字符串存在。搜索词随文件名改动，从 `docs/specs/<工作名>/<工作名>.md` 改成 `docs/specs/<工作名>/spec.md`。

### 9. `mmw artifact index`——长期产物的清单

```
mmw artifact index <类别>
```

类别取 `adr` 或 `spec`。命令扫描该类别下各文件的元数据块，当场算出清单并输出到标准输出。**agent 一律读命令输出**；仓库里的 `docs/adr/README.md` 与 `docs/specs/README.md` 是同一次运行顺手写下的副本，供不运行命令的读者阅读，不是权威。

没有一个需要谁记得去跑的重建动作——读的动作本身就是重建。这是本次决定的核心：MMW 装在别人的仓库里，那边没有 `bash mmw/test.sh`，而 `mmw doctor` 要人主动跑，所以任何「事后发现索引过期」的机制都发现不了。

| 项 | 决定 |
| --- | --- |
| 写文件的条件 | 只在算出的内容与文件现有内容不同时才写。绝大多数时刻两者一致，命令跑完工作区不脏 |
| 比较方式 | 逐字节比较算出的完整正文与文件现有正文。不比时间戳，不比行数 |
| 副作用 | 有写副作用。这与 `mmw artifact path` 无副作用不矛盾，是两条命令 |
| `adr` 清单字段 | 编号（取自文件名）、标题（取自一级标题）、日期、改写了哪几份、被哪几份改写 |
| `spec` 清单字段 | 工作名、`summary`、日期、任务分支名、spec issue 编号。收录全部 spec，包括尚未完成的 |
| 副本正文格式 | 一级标题加一张表，每份产物一行，表头的字段与清单字段一致。副本开头写一行说明它由 `mmw artifact index <类别>` 生成 |
| 副本不可写时 | 跳过写入，只输出清单，并在标准错误写一行说明跳过了。退出码仍是 0 |

**只读角色跑这条命令是允许的，这一点要写明。** `AGENTS.md` 要求每个 agent 读 ADR 之前先跑 `mmw artifact index adr`，而 `mmw/skills-src/mmw-reviewer/SKILL.md:32` 要求审查者「不碰工作区、暂存区、`HEAD` 或任何分支」。两条规则直接矛盾：副本过期时这条命令会改工作区。处置分两层：

- 命令层：副本不可写时自动降级成只输出，只读文件系统里不再失败。
- 合同层：`mmw-reviewer` 的「只读」一节和派只读 task 时的约束栏都写明——跑 `mmw artifact index` 属于允许动作，它可能更新索引副本，那不算修改被审产物。

不给这条命令加只读开关。ADR `0010` 否决过「命令默认写文件，另给一个只读开关」，理由是多一个要 agent 记住的参数，而「要人记住」正是那个决定否掉的机制。把这处矛盾写进合同、让命令按环境自动降级，不需要任何人记住参数。

plan 不做索引。没有任何技能会问「这个仓库里有哪些 plan」；`worker` 从 tracer bullet ticket 进入，ticket 里写着产物引用，这条路不经过索引。research 与 prototype 不做索引，它们由上游点名。`.out-of-scope/` 不做索引，`/mmw-triage` 分诊时整个目录读一遍。领域文档已有 `CONTEXT-MAP.md`。

`AGENTS.md` 里「读取 `docs/adr/` 下与本次范围相关的 ADR」改写为：

> 先运行 `mmw artifact index adr` 取得 ADR 清单，再读其中与本次范围相关的那几份。

这句话位于 `MMW-DOMAIN-CONTEXT` 管理段，由 `mmw domain sync` 写入，接口是现成的。spec 索引不需要等价钩子，它的消费方是 `/mmw-to-spec` 与 `/mmw-start` 的技能正文。

### 10. `mmw artifact check`——声明层解析校验

```
mmw artifact check
```

读当前仓库全部 spec 与 plan 的元数据块，取出每一条 `artifact_refs`，逐条按 `mmw artifact path` 的规则解析。解析不到就非零退出，并逐条列出解析失败的那些。

**历史文件与新文件靠 `artifact_refs` 这个键本身区分。** ADR `0008` 决定历史产物人工处理，`agentflow` 保留着 50 个没有新元数据块的旧 plan 目录。这条命令按三种情况分别处理：

| 情况 | 判定 | 行为 |
| --- | --- | --- |
| 文件没有元数据块，或元数据块里没有 `artifact_refs` 键 | 历史文件 | 报告一行，不计入失败 |
| 有 `artifact_refs` 键，值是空列表 | 新文件，上游明确说没有产物要传 | 通过 |
| 有 `artifact_refs` 键，某个条目解析不到 | 新文件写错了 | 失败 |

这条判据成立的依据是：生产方技能被规定一律写出这一节，没有内容写「无」，也就是空列表。所以「有这个键」等价于「这份文件由新合同下的技能生产」。严格失败会阻断保留历史 plan 的仓库；一律跳过缺键又会放过新文件漏写——按键本身分流，两种失效都不发生。

**只校声明层，不校磁盘。** 它检查的是「这条产物引用的类别名合法、各段是安全路径段、这个类别允许这些段」，不检查「这条路径指向的文件此刻存在」。被跳过的上游不该造成必然失败的检查——用户可能选择不保存那次 research。

调用点是生产方自己：`/mmw-to-spec` 写完 spec 后跑一次，`/mmw-to-plan` 写完 plan 后跑一次。它同时进 `mmw/test.sh`，在一次性仓库上验证命令本身的行为。

**明确放弃反向校验**：产物目录里存在、而下游声明写「无」，不做机械校验。机器判得出产物存在，判不出它与这次工作相关；这道校验会用「存在」冒充「相关」。这类漏写由 ① spec 审和 ② plan 审发现，是本次接受的代价。

### 11. `mmw artifact list`——这次交付名下已有什么

```
mmw artifact list [--name <工作名>] [--map <map 编号>]
```

列出这次交付名下已经保存的产物，给必读材料声明的补全那一步用：认领 decision ticket 的会话从清单里挑，不凭记忆。

| 来源 | 列什么 |
| --- | --- |
| 仓库 | `docs/research/<工作名>/` 与 `docs/prototypes/<工作名>/` 下的全部产物，各自输出成产物引用四项 |
| tracker | 给了 `--map` 时，该 map 下已关闭 decision ticket 的编号与标题 |

`--name` 缺省时读 `mmw task state` 的工作名，规则与 `mmw artifact path` 一致。不给 `--map` 时只列仓库那一半，不报错——普通交付没有 map。

判断「这张 ticket 要读哪几份」仍然是人和 agent 的判断，命令只提供候选，不做筛选。

### 12. `mmw issue append`——map 决定索引的并发写

```
mmw issue append <issue 编号> --section "<小节标题>" --line "<要追加的内容>"
```

五步在一条命令内完成：

1. 读最新正文，记为 V1。
2. 在指定小节的末尾插入这一行，得到 V2。
3. 写回 V2。
4. 短暂等待。
5. 再读一次，得到 V3。检查**两项**：V1 的全部行都在 V3 里，**并且**自己新增的那一行也在 V3 里。任一项不成立，回到第 1 步重做。

**两项都要查，缺一项都发现不了丢行。** 只查「自己那一行在不在」，发现不了自己顶掉别人；只查「V1 的全部行都在」，发现不了自己被别人顶掉。下面这个时序里，两个会话各自只查一项都会通过，而 A 的行已经没了：

```
t1  A 读 → S              t2  B 读 → S
t3  A 写 → S+a
t4  A 读回 S+a：S 的全部行都在 → 通过
t5  B 写 → S+b            ← a 在这一步消失
t6  B 读回 S+b：S 的全部行都在 → 通过
```

加上第 4 步的等待和第 5 步的第二项检查之后，A 在 t6 之后读回，发现自己那一行不在，于是重做：重读得到 `S+b`，写回 `S+b+a`，两行都在。B 那边同样跑这五步，它读回时 `b` 在、`S` 全在，通过。最终两行都保住。

**这一处修正了 ADR `0014` 的判据描述。** 那份 ADR 写的是「比对的对象是上一版的行集合，不是『自己那一行在不在』」，把两项写成了二选一。按上面的时序，单独任何一项都无效。ADR 的意图（追加不丢行）不变，实现形状在本 spec 改正；实现这份 spec 时一并给 ADR `0014` 补一条 Consequence 记录这次修正。

| 项 | 决定 |
| --- | --- |
| 小节定位 | 按 Markdown 二级标题精确匹配 `--section` 给的字面。找不到该小节时非零退出，不创建它 |
| 插入位置 | 该小节最后一个非空行之后，下一个二级标题之前 |
| 比对结果 | 两项检查任一不成立就从第 1 步重做 |
| 等待时长 | 第 4 步等 2 秒。它要盖住的是另一个会话「读到写」的那一小段，不是它的思考时间 |
| 重做上限 | 3 次。用尽仍不一致就非零退出，并输出缺失的那几行原文，不静默 |
| 是否为 map 写死 | 不写死。小节标题是参数，将来出现第二个并发编辑点时命令现成 |

规则这一层只规定 map 正文这一处必须用它：技能源里现在没有第二处二次编辑 issue 正文的地方，`mmw issue create` 出现在 `mmw-to-spec`、`charting` 与 `mmw-to-tickets` 三处，都是建立时写一次。

竞态窗口从「agent 读到写之间的思考时间」缩到「另一个会话在我第 5 步读回之后才写」这一种。它不为零：如果 B 在 A 的第 5 步检查通过之后才写回，A 已经退出，不会再发现。要彻底消除只能靠乐观锁或串行化，**乐观锁这条路已被实测排除**，不是实现难度问题——GitHub 对 issue 更新的 endpoint 不接受条件请求头；串行化要一个统一写入的进程，MMW 的每个会话是独立进程，没有那一层。剩下的这个窗口是本次接受的代价。

丢行真的发生时，用 GraphQL 的 `userContentEdits` 事后查——它给出每个版本的 `editedAt`、`editor` 和当时的完整正文，比对相邻两版能看出哪几行消失。它是调查手段，不加成例行检查：命令自带写后验证之后，为剩下那几百毫秒单独架一道要人主动跑的检查，正是本次否决过的那一类机制。

### 13. `mmw issue set-parent`——给已存在的 issue 设置父 issue

```
mmw issue set-parent <子 issue 编号> --parent <父 issue 编号>
```

spec 发布后，带 agent brief 的原 issue 关闭并挂到 spec issue 底下。现有 `mmw issue create --parent` 只能在建立时指定父 issue，这个动作补上「给已存在的 issue 设置父 issue」。它走与 `create --parent` 相同的 sub-issues 端点，端点没开时直接失败，不退回文本约定。

### 14. decision ticket 的必读材料声明

decision ticket 正文从「只写 `Question`」改成两节：

```markdown
## Question

<这张 ticket 要解决的决定或调查问题>

## 必读材料声明

- <产物引用四项，或 issue 编号>
```

| 项 | 决定 |
| --- | --- |
| 谁写 | 建 ticket 的会话写当时已知的；认领它的会话在开工前补进 blocker 关闭后新产生的材料 |
| 怎么补 | 认领之后跑 `mmw artifact list --name <工作名> --map <map 编号>` 取候选清单，从清单里挑 |
| 条目形态 | 仓库产物写产物引用四项；tracker 产物（结论评论）写 issue 编号——结论评论落在 tracker，不占仓库路径 |
| 为什么不现算 | 从 map 的 `Decisions so far` 与已关闭 ticket 现算，只能算出「这项 effort 里所有已关闭的 ticket」。「这张 ticket 该读哪几件」是写的人的判断，从 map 上算不出来 |
| 为什么不一次写死 | `charting.md` 是第 4 步建 ticket、第 5 步才跑 research，建立时上游还没跑，一次写死必然是空的 |

**wayfinder 交接表四行全改。** 那张表在 `mmw/skills-src/mmw-wayfinder/walking.md` 第 46 至 51 行：第 46 行是表头，第 47 行是分隔行，第 48 行是 `wayfinder:grilling`，第 49 至 51 行依次是 prototype、research 和 task。grilling 那一行现在只有「调用 `/mmw-grilling`」六个字，另外三行各传三样。

四行一律改成传五样：`Question`、必读材料声明里的**全部**条目、工作名、范围段。必读材料声明有两类条目，两类都要传——仓库产物传产物引用，tracker 产物传 issue 编号。只传产物引用的话，前置 decision ticket 的结论评论仍然到不了下游，而那正是这次要修的接线失效本身。范围段 `issue-<编号>` 由调用方传，不由下游自己定——`mmw/skills-src/mmw-grilling/SKILL.md:62` 那条「解决 Wayfinder 的 decision ticket 时用 `issue-<编号>`」的自定规则删掉，因为下游判断不了自己的调用来源。这条自定规则正是当前两处路径规则对不上的原因：`SKILL.md:62` 展开成 `.scratch/issue-<编号>/understanding.md`，而 `walking.md:42` 规定的是 `.scratch/<工作名>/issue-<编号>/`。

**`/mmw-grilling` 的「取得事实」一节增加一步**：提问之前先看被点名的材料里是不是已经有答案。这一步归 MMW 接线，不是语义漂移——上游原句是 `"don't ask the user for anything you could look up yourself"`，先看已有材料是这条要求的更省的执行方式。

**结论评论增加 `## 材料使用记录` 一节**，逐条写每项必读材料用上了没有、没用上的理由。痕迹由这一节承担：读过不产生痕迹，所以「读过那份 research」不能当判据，「这一节写出来了」才能。机器判得出那一节在不在，判不出材料有没有真的被使用，所以这一项不进机械校验。

**材料缺失分两种**：生产它的 ticket 按设计没跑、或用户当时选择不保存 research，属于预期缺失，继续；声明了、生产方也跑过、却找不到，停下问用户，不编造内容。

### 15. research 索引的章节指引

`mmw/skills-src/mmw-research/MAIN.md:106` 现在规定 research 索引必写「下游怎么用」，写法是由写 research 的一方点名哪几张 decision ticket 该读哪几节。这一节降级成**章节指引**：逐节说明 research 报告各节讲什么，不写 decision ticket 编号，不写「只该读哪几节」。

两条方向并存，各管一层：必读材料声明是产物级合同，章节指引是报告内部的地图。两边不一致时以必读材料声明为准。

降级的理由是它当合同用时会裁剪视野，而且已经发生过：`issue-20` 的 research 索引给 decision ticket #21 点名「第 1、2、3、4 节」，#21 因此没有读第 8 节 `"The registry is computed, not written."`；#27 与 #23 随后各自决定把索引写成仓库文件，直到 #30 对照复核才发现，再开 #31 去解。它还只能点到写下它那一刻已经存在的 ticket——`issue-20` 写下时 #30 到 #35 都不存在，而 #30 用了那份报告的十二节。

不删掉这一层的理由是必读材料声明是人写的，漏写时没有任何机制发现；decision ticket 没有 ① spec 审和 ② plan 审这两道兜底。章节指引写在产物那一侧，agent 打开报告就看得到。

prototype 的 `README.md` 不加这一节。它本身就是索引，列变体 key、页面 URL、目录和接线文件与资产的对应关系，再加一节是把同一件事写两遍。

书写格式：一个二级标题 `## 章节指引`，下面一张两列表，左列节号与节标题，右列一句话说明这一节讲什么。

### 16. 撞名

类别内细分由生产它的技能当场取名时，两件产物可能取到同一个名字，四项全部相同，解析出同一条路径，后写的那一件把先写的顶掉。

**处置：生产它的技能在写第一个文件之前列一次目标路径的父目录。** 目标已经存在就重新取一个承载差别的名字；取不出来时加序号兜底。全程不问用户，也不报告。

| 项 | 决定 |
| --- | --- |
| 判定范围 | 按性质判定，不按类别名枚举。`sub_naming` 是 `ad-hoc` 的类别才查 |
| 重新取名之前 | 先读已存在那件产物的索引，确认这次要答的确实是另一个问题。产出的是 `artifact-inventory` 与 `artifact-consumers` 这种名字，不是 `artifact-inventory` 与 `artifact-inventory-2` |
| 没有索引文件的类别 | 读那个目录下的全部文件名与各文件的一级标题 |
| 序号兜底形状 | 在原名后加连字符与两位序号，从 `-02` 起 |
| 跨交付取到同一个类别内细分 | 不管。产物引用第二项是工作名，路径自带命名空间 |
| 并发会话 | 靠 Git 的 add/add 合并冲突暴露，不另加机制 |

真正会撞的只有两处：同一次交付里两次 research 取到同一个主题名；同一棵 prototype 树里两个变体组取到同一个问题 slug。其余类别不会撞——spec 是固定文件名，plan 的两位编号由 `/mmw-to-tickets` 成批分配，ADR 编号由 `mmw domain adr-next` 分配，leaf 与否决记录是一概念一文件，审查记录是四道关卡固定名。

agent 靠两层知道要查重：`mmw artifact path` 对 `ad-hoc` 类别输出的那行提醒，以及技能正文在取名那一步写的一句。只做第二层会把「哪些类别要查重」复制进每份技能正文；只做第一层会漏掉不跑命令直接拼路径的 agent。

**这一条不进机械校验。** 机器看得见「这条路径已存在」，看不见「上一次那件产物是不是同一件事」；把「路径已存在」当成撞名去报错，会让每一次正常的新一轮迭代都红。代价是一个不跑命令、也不看技能正文的 agent 仍然会把别人的 research 写没。

### 17. 废除项

| 废除的东西 | 处置 |
| --- | --- |
| Wiki 归档 | `mmw/cli/lib/wiki.sh` 整份作废，`mmw` 主入口的 `wiki` 子命令与用法说明移除。`/mmw-closing` 不再写 Wiki |
| `docs/evidence/` | 类别根取消。界面验收证据留在 scratch 中；用户要求长期保留时由用户指定位置 |
| `.dispatch/` | 目录取消。四栏 task 与角色报告都不写文件 |
| `.mmw.json` 的五项 | `specs`、`plans`、`prototypes`、`research`、`evidence` 删除。`paths` 只保留 `scratch`、`reviews`、`release`、`worktrees` |
| spec 收尾删除 | `/mmw-closing` 现有七步中的前六步作废，只剩清理当前任务的过程材料。技能保留，继续作为「这条分支就绪待集成」的判定点 |

**四栏 task 与角色报告不写文件。** 判据是能在提示词或标准输入里传完的一律不写文件。`mmw dispatch` 的 `--task <文件>` 改成从标准输入或 `--task-text` 接收正文；`mmw/cli/adapters/claude-code.sh` 去掉 `codex exec` 的 `-o "$report"`。依据是这两份文件都没有必须落盘的读者：四栏 task 的正文最终被 adapter 用 `jq --rawfile` 读进 params，subagent 从不打开那个文件；角色报告的内容同时走标准输出，主 agent 从后台 Bash 的输出里已经拿到一份。

派发进度日志仍然落盘，因为进程结束后它是唯一的诊断材料。它的文件名原来取自 task 文件基名，现在没有这个基名了，改成 `<角色>-<时间戳>.log`，落点补上名字段与范围段。

**放弃的东西要说清楚**：派发出问题时，没有一份文件记录「主 agent 到底派了什么」。四栏 task 原本可以当派发凭据用。另外，去掉 `-o` 建立在「后台 Bash 输出被截断这个顾虑目前没有证据」之上，不是建立在「已确认不会截断」之上。真出现截断，那是宿主输出通道的问题。

`mmw init` 写进 `.gitignore` 的六项减为五项，去掉 `.dispatch/`。

### 18. `mmw doctor` 的只读报告

`mmw doctor` 增加两组只读报告，都不动文件，**都不改变退出码**。一个装好的 MMW，在有历史产物的仓库里仍然是装好的；让它因为历史产物而失败，会让人为了让它通过去删东西。

第一组，历史产物（三项，判据是这条路径在新合同下不该存在，机器能直接判定）：

| 报什么 | 依据 |
| --- | --- |
| `docs/evidence/` 存在 | 这个类别根已取消 |
| `.dispatch/` 存在 | 四栏 task 与角色报告不落盘 |
| `docs/specs/<X>/<X>.md` 存在 | 新的 spec 文件名是 `spec.md` |

**不报** `docs/plans/` 与 `docs/research/` 下名字段的取值。机器判定不了某个目录名是旧的任务 slug 还是新的工作名，报它就是用列表形状伪装成机械校验。也不报过程材料与审查记录内部的细分差异：这两个类别根仍然存在，而且它们的内容本来就在任务结束时清理。

第二组，遗留配置：`.mmw.json` 里发现 `specs`、`plans`、`prototypes`、`research`、`evidence` 任意一项时各报一行，指出它们已经退役。`.mmw.json` 是人手改过的文件，静默删除会让改过它的人不知道自己配的东西为什么没生效。

`mmw doctor` 当前没有任何测试覆盖。这两组报告连同 `mmw doctor` 的既有输出一并纳入新建的测试。

### 19. 技能源改写

30 个技能中有 20 个受影响。改写分五类：

| 类别 | 改法 | 处数 |
| --- | --- | --- |
| 类别根字面值加占位符 | 换成 `mmw artifact path` 完整命令行 | `docs/specs/` 24、`docs/plans/` 17、`docs/adr/` 18、`docs/context/` 14、`docs/prototypes/` 7、`docs/research/` 6、`.out-of-scope/` 29 行中带占位符的那些 |
| 工作目录根默认取值 | 一律换成命令或术语 | `.scratch/` 28 行、`.reviews/` 14 行 |
| `<产物目录>` 占位符 | 换成工作名，取值读 `mmw task state` | 27 处 |
| 各自的取名规则 | 删除，改为读工作名 | `mmw-prototype/SKILL.md:26-34`、`mmw-research/MAIN.md:14-16`、`mmw-grilling/SKILL.md:62`、`mmw-wayfinder/charting.md:19` |
| 入口分支判断 | 删除，改为一条命令 | `mmw-to-spec/SKILL.md:26-40` 整张五行表、`wizard/SKILL.md:52`、`to-questionnaire/SKILL.md:28`、`mmw-diagnosing-bugs/SKILL.md:27` |

固定类别根不带占位符地单独出现时不改。`mmw-triage` 有 20 行以上写着「读 `.out-of-scope/*.md`」这类句子，`mmw-to-spec`、`mmw-closing`、`mmw-reviewer`、`mmw-improve-codebase-architecture` 各有一行写着「读 `docs/adr/` 下相关的 ADR」——这些不带名字段，路径本身就是常量，改写它们换不来正确性。其中 `mmw-triage/examples.md` 是上游材料，改它要先走 `upstream-skill-fidelity`。

另有六行工作目录根不带占位符的现有写法要改，因为工作目录根写死默认值本身就是错的：`wizard/SKILL.md:55`、`to-questionnaire/SKILL.md:31`、`mmw-diagnosing-bugs/SKILL.md:30` 三处同一句「`.scratch/` 在 `.gitignore` 里」，以及 `mmw-closing/SKILL.md:104,106`、`mmw-start/resuming.md:13`。改法是换用领域文档的术语「scratch 根」和「reviews 根」。

逐技能的其余改动：

- `mmw-start/SKILL.md:53-75` 的类型前缀表保留，但只管任务分支名；「一个 slug 贯穿四处」这句话作废。
- `mmw-start/resuming.md` 的「有没有归档」检查项，由查 Wiki 页面改为查仓库路径；`resuming.md:22` 的搜索词改成 `docs/specs/<工作名>/spec.md`；`resuming.md:24` 按 `docs/plans/<工作名>/` 找 plan 的路径改为跑命令。
- `mmw-closing/SKILL.md:96-106` 为「两个 slug 不同」写的补偿逻辑删除，`.dispatch/` 清理规则删除。
- `mmw-implement/worker-brief.md:11-12` 改为只点名产物，文件清单由索引给。
- `mmw-wayfinder/SKILL.md:89` 与 `walking.md:69` 两条手工自检删掉，换成一句「用 `mmw issue append`，不要自己拼整份正文写回」。留着它们等于让 agent 手工再做一遍命令已经做的事，而且做的是被证明无效的那一种。
- `mmw-wayfinder/SKILL.md` 的 ticket 模板、`charting.md` 第 4 步、`walking.md` 第 5 步三处，ticket 正文规则从「只写 `Question`」改成两节；`walking.md` 第 2 步 claim 之后增加「补全必读材料声明」一步。
- 全部派发动作块跟着 `mmw dispatch` 的接口变更改。

**技能源改完重跑 `mmw skills materialize`。** 各宿主技能产物跟着更新，这是全部动作。

### 20. 领域文档改动

- `docs/context/artifact-location.md` 的九行类别根表删除，leaf 只留术语定义和指向 `mmw/cli/artifacts.json` 的权威引用。理由是同一份数据不存两处。
- `docs/context/release-and-closure.md` 删除「Wiki 页面」这个术语。它现在的定义是「`/mmw-closing` 写入的长期 spec 与 plan 页面」（第 35 至 37 行），而 ADR `0001` 已经废除 Wiki 归档、`/mmw-closing` 不再写 Wiki。decision ticket #27 的结论评论明确写着「留在这里备查，由下游 spec 一并处理」；decision ticket #21 当时没有顺手改它，理由是一次会话的领域文档改动只涉及自己那张 ticket 的决定。不删的话，技能源与领域模型会给出相反的合同。
- `CONTEXT-MAP.md` 的「出包与收尾」一行 Owns 去掉「Wiki 页面」。
- `docs/context/artifact-location.md` 补一条术语，指工作名重复这件事。leaf 现在把「重名」列在「撞名」的 `_Avoid_` 里，而撞名的定义只涵盖当场取名的类别内细分，工作名重复不在其中，也没有自己的名字——本 spec 只能用描述性说法绕开。这个缺口由实现阶段用 `/mmw-domain-modeling` 补上。
- `AGENTS.md` 的「唯一事实来源」第 2 条点名 `mmw/cli/artifacts.json`，并增加一段说明产物落点由 `mmw artifact path` 回答、技能正文不写路径字面值、`.mmw.json` 的 `paths` 只保留四项。
- `AGENTS.md` 的领域上下文一段，「读取 `docs/adr/`」改为先跑 `mmw artifact index adr`。
- 本仓库现有 14 份 ADR 补写元数据块。ADR 索引取自元数据块，不补写就生成不出内容。`amends` 字段按已知的改写关系填：`0008` 改写 `0003`，`0010` 改写 `0001` 与 `0007`，`0007` 改写 `0001`。

## Failure Paths

| 失败情况 | 触发条件 | 负责处理的边界 | 用户观察到的结果 | 系统行为 |
| --- | --- | --- | --- | --- |
| 认不出的类别名 | `mmw artifact path` 收到不在产物落点数据里的类别名 | `mmw artifact path` | 报错并列出全部合法类别名 | 非零退出，不输出任何路径 |
| 问了不写文件的类别 | 类别的 `status` 是 `no-file` | `mmw artifact path` | 报错并说明这类产物不写文件、正文怎么传 | 非零退出 |
| 问了不套路径形状的类别 | 类别的 `status` 是 `not-shaped` | `mmw artifact path` | 报错并指出该问哪条命令 | 非零退出 |
| 读不到工作名 | `--name` 缺省，而 `mmw task state` 返回 `local` 或 `outside` | `mmw artifact path` | 报错并说明要先建任务工作树 | 非零退出，不回退默认值 |
| 类别不允许范围段却给了 | 类别的 `allows_scope` 为假，命令行带 `--issue` | `mmw artifact path` | 报错并指出这一类没有范围段 | 非零退出 |
| 类别内细分不是安全路径段 | `--sub` 的任意一段含大写字母、斜杠或非法首字符 | `mmw artifact path` | 报错并指出违反哪一条字符规则 | 非零退出 |
| 产物引用解析不到 | spec 或 plan 元数据块里的 `artifact_refs` 有条目解析失败 | `mmw artifact check` | 逐条列出解析失败的条目和失败原因 | 非零退出 |
| 下游读不到该有的那一节 | 上游没写 `## 产物引用` 或元数据块缺 `artifact_refs` | 下游技能的行为规则 | agent 停下报缺，说明缺哪一节、上游是谁 | 不猜，不静默继续 |
| 被点名的材料找不到 | 必读材料声明里的条目解析出路径，但那个位置没有内容 | 认领 decision ticket 的技能 | 区分两种：生产它的 ticket 按设计没跑、或用户选择不保存，属预期缺失，继续；声明了、生产方也跑过、却找不到，停下问用户 | 预期缺失继续；异常缺失停下，不编造内容 |
| map 正文追加时丢行 | 并发会话在命令执行窗口内写回了另一版正文 | `mmw issue append` | 命令自己重做，至多 3 次 | 重做仍不一致则非零退出并输出缺失行原文 |
| 指定的小节不存在 | `--section` 给的标题在 issue 正文里找不到 | `mmw issue append` | 报错并列出正文里实际有哪些二级标题 | 非零退出，不创建那个小节 |
| 撞名 | 当场取名的类别，目标路径的父目录里已经有这个名字 | 生产它的技能 | 无。不问用户，也不报告 | 读已存在那件产物的索引，重新取一个承载差别的名字；取不出来加 `-02` 起的序号 |
| 并发会话撞名 | 两个任务工作树各写一件产物，两者解析出同一条路径 | Git | 合回时 add/add 冲突 | 由集成的会话按 `/mmw-integrate` 处理 |
| 技能源写回路径字面值 | 技能源出现类别根加占位符，或工作目录根的默认取值 | `mmw/cli/tests/test_skill_paths.sh` | 测试变红并指出文件与行号 | `bash mmw/test.sh` 非零退出 |
| 仓库里有历史产物 | `docs/evidence/`、`.dispatch/` 或 `docs/specs/<X>/<X>.md` 存在 | `mmw doctor` | 各报一行 | **不改变退出码**，不动文件 |
| `.mmw.json` 有退役配置 | 配置里有已删除的五项之一 | `mmw doctor` | 各报一行，指出它已退役 | **不改变退出码** |

## Testing Decisions

好测试只测外部行为，不测实现细节。这次交付的外部行为是「agent 敲一条命令得到什么」和「技能源文本里有没有路径字面值」。测试在一次性仓库上跑真命令，与 `mmw/cli/tests/` 现有六份 bash 测试的做法一致：断言命令拒绝了什么、拒绝之后破坏有没有发生、给定输入返回什么。

用户已确认的 seam：

| Seam | 验证的外部行为 | 选择这一层的原因 |
| --- | --- | --- |
| `mmw` CLI 命令行接口 | `mmw artifact path` 的输出与各种失败、无副作用；`mmw issue append` 在并发下不丢行；`mmw artifact index` 当场算出、只在内容变化时写、副本不可写时降级；`mmw artifact check` 的解析校验与历史文件分流；`mmw artifact list` 的清单；`mmw task state` 输出工作名；`mmw issue set-parent`；`mmw dispatch` 新接口下 task 正文的完整传递与既有护栏；`mmw doctor` 的两组只读报告与退出码不变 | 这就是 agent 实际敲的那一层。在命令行验证等于验证真实使用方式。已有测试形态现成，不用新建脚手架 |
| 技能源 Markdown 文本 | 类别根字面值后紧跟 `<…>` 占位符段就失败；工作目录根的默认取值出现即失败 | 技能源是纯文本，没有可执行接口。两条正则规则是可解析的语法事实 |

两个 seam 都通过 `bash mmw/test.sh` 这一个入口跑，不新增入口。

测试文件的归位：

| 文件 | 动作 | 装什么 |
| --- | --- | --- |
| `mmw/cli/tests/test_artifact.sh` | 新建 | `mmw/cli/artifacts.json` 的结构完整性、安全路径段规则、`mmw artifact path` 的三种失败与无副作用、`index`、`check`、`list` 三个动作的行为 |
| `mmw/cli/tests/test_skill_paths.sh` | 新建 | 两条正则规则。字面值清单从 `mmw/cli/artifacts.json` 与 `mmw/cli/mmw.default.json` 解析，测试里不手抄第二份。排除两处：`mmw/skills-src/mmw-setup/` 与 `mmw/skills-src/mmw-triage/examples.md` |

**扫描范围为什么排除那两处。** `mmw-setup/` 是旧背景材料，`AGENTS.md` 规定扫描技能正文时排除它。`mmw-triage/examples.md` 是上游材料，本 spec 的 Out of Scope 规定不改它的路径写法，改它要先走 `upstream-skill-fidelity`。它第 54 行写着 `` `.out-of-scope/<概念>.md` ``，正是规则一要判失败的形态。三件事同时成立就无解：规则一必红、不许改那一行、不许加豁免清单。出路只有把这份文件排出扫描范围——它与排除 `mmw-setup/` 是同一类动作，按文件来源排除，不是按命中内容开豁免。判据是这份文件由上游拥有，不由 MMW 的落点合同拥有。这两处排除写死在测试里，不接受配置项，也不随命中数量增删。
| `mmw/cli/tests/test_issue.sh` | 延伸 | `mmw issue append` 的四步、丢行重做、重做上限、小节不存在；`mmw issue set-parent` |
| `mmw/cli/tests/test_skill_refs.sh` | 延伸 | 第四类引用增加：技能正文里出现的类别名参数值必须在产物落点数据里认得出 |
| `mmw/cli/tests/test_init.sh` | 延伸 | `.mmw.json` 的 `paths` 只剩四项；`.gitignore` 五项不含 `.dispatch/`；`mmw doctor` 的两组报告与退出码不变 |
| `mmw/cli/tests/guardrails.sh` | 改 | 五处 `dispatch worker --task "$task"`（314、316、318、324、328 行）改成新接口。这五条用例测的是护栏（`--cwd` 不是 git 工作树、是主检出、工作区不干净），护栏语义不变，只换 task 正文的传法 |
| `mmw/cli/tests/guardrails.sh` | 延伸 | 增加一条：多行 task 正文经标准输入或 `--task-text` 穿过 adapter 之后，subagent 收到的正文与传入的一字不差。这是接口变更后唯一能发现「正文在传递中被截断或转义错」的地方 |
| `mmw/cli/tests/test_wiki.sh` | 删除 | 被测的三个子命令退役 |
| `mmw/test.sh` | 改 | 去掉 `test_wiki.sh` 那一行，加 `test_artifact.sh` 与 `test_skill_paths.sh` 两行 |

`test_skill_paths.sh` 不并进 `test_skill_refs.sh`。后者的合同是「引用指得到东西」，前者的合同是「落点只由命令回答」；两个合同放同一份文件里，将来删掉其中一个会连累另一个。

**校验有一个已知的洞**：固定类别根不带占位符地单独出现时不失败。这是有意留下的，不是遗漏。将来有人在技能源里写下 `docs/specs/` 而不跟占位符，测试不会红。零例外方案要靠豁免清单撑着，而按 `AGENTS.md`，靠豁免清单撑着的校验不算机械校验。

**明确不校验的事**：产物归类是否正确、类别内细分取名是否恰当、落点有没有消费方、字面值处数、方法选择、目标仓库里实际存在的产物是否符合路径形状。最后一项由 `mmw doctor` 只读报告，它不是提交前的机械校验。产物引用的反向校验（产物存在而下游写「无」）也不做——机器判得出存在，判不出相关。

### 与 aidlc-workflows v2 五项机械校验的逐项对照

decision ticket #30 的结论把这项对照交给了 spec 阶段。五项的出处是 `docs/research/mmw-artifact-wiring/issue-30/aidlc-decision-audit/report.md` 第 4 节第三处，原始清单在 `docs/research/mmw-artifact-wiring/issue-20/aidlc-v2-artifact-wiring/report.md` 第 11 节。

| aidlc 的那一项 | 本次处置 | 理由与 MMW 的对应物 |
| --- | --- | --- |
| 1. 阶段定义的引用校验（`Graph references`） | **照搬** | 两处对应：`mmw artifact check` 校 spec 与 plan 元数据块里的产物引用；`test_skill_refs.sh` 校技能之间的四类引用。两处都只校声明层 |
| 2. sensor 对给定 target 的存在性与形状校验 | **不照搬** | MMW 没有 aidlc 那种由引擎驱动、带 target 的 sensor。产物在目标仓库里存不存在是运行时状态，ADR `0009` 明确把它列入不校验，改由 `mmw doctor` 只读报告 |
| 3. 上游存在性读取，只用于过滤（`filtered to artifacts that exist on disk`） | **照搬** | 两处对应：`mmw artifact check` 只校声明层不校磁盘；必读材料声明的缺失分成预期与异常两种，预期缺失继续。理由与 aidlc 相同——被跳过的上游不该产生必然失败的检查 |
| 4. per-unit 阶段的完成度检查 | **否决** | 完成度是产物质量判断。`AGENTS.md` 禁止用计数、列表形状或固定阈值伪装成机械校验，ADR `0009` 把完成度列入不校验。这一项进来就得靠计数撑着 |
| 5. 阶段源文件的 `Outputs:` 文本校验 | **照搬形态，校的内容不同** | 对应物是新建的 `test_skill_paths.sh`：同样是对源文本做正则校验。aidlc 校的是阶段声明了什么产出，MMW 校的是技能正文有没有写路径字面值——MMW 的技能不声明产出，产出由类别决定，所以没有可校的产出声明 |

具体测试写法由 `/mmw-tdd` 和 `TESTING.md` 规定。

## Contract Boundaries

| 合同 | 归属方 | 提供方 | 消费方 | 形态与验证 |
| --- | --- | --- | --- | --- |
| 产物落点数据 | MMW 源码仓库 | `mmw/cli/artifacts.json` | `mmw artifact` 全部动作、`test_skill_paths.sh`、`test_skill_refs.sh` | JSON。结构完整性由 `test_artifact.sh` 验证 |
| `.mmw.json` 的 `paths` | 目标仓库 | 目标仓库自己的配置 | `mmw artifact path` 解析工作目录根 | 只保留 `scratch`、`reviews`、`release`、`worktrees` 四个键。多出的键由 `mmw doctor` 报告 |
| spec 元数据块 | `/mmw-to-spec` | spec 文件头 | `mmw artifact index spec`、`mmw artifact check`、`/mmw-start` | YAML。六个字段，`artifact_refs` 由 `mmw artifact check` 逐条解析 |
| plan 元数据块 | `/mmw-to-plan` | plan 文件头 | `mmw artifact check`、`worker` | YAML。两个字段 |
| ADR 元数据块 | `/mmw-domain-modeling` | ADR 文件头 | `mmw artifact index adr` | YAML。两个字段，编号取自文件名，标题取自一级标题 |
| tracker 正文的固定标题 | 各生产方技能 | map、decision ticket、spec issue、tracer bullet ticket | 按节读取的下游技能 | Markdown 二级标题，字面见 Implementation Decisions 第 8 节 |
| `mmw dispatch` 的 task 接口 | MMW CLI | 主 agent | 各宿主 adapter | 从标准输入或 `--task-text` 接收正文。这是一次**破坏性接口变更**，全部派发动作块必须同批改完 |

**迁移要求**：`.mmw.json` 五项的删除由 `mmw init` 处理，它已经在做（`mmw/cli/lib/init.sh:61-62`）。其余历史产物不做迁移命令，人工处理，清单由 `mmw doctor` 随时跑出来。

## Cross-Plan Contract Anchors

这一节给 11 份 plan 划分共享文件的归属，并写明谁给谁提供接口。它不改 `## Contract Boundaries`，那一节定的是产品合同，这一节定的是 plan 之间的施工边界。plan 编号见各张 ticket 正文的 `## Plan` 一节。

### 文件归属

多数文件只有一份 plan 会碰。下面八处会被多份 plan 同时碰，因此**归属划到分区**而不是整个文件——文件级归属在这几处太粗，会让别的 plan 无法完成自己的验收。碰同一个文件的 plan 只许改自己分区内的行。

| 共享文件 | 分区归属 |
| --- | --- |
| CLI 主入口 `mmw/cli/mmw` | 一行一个子命令。01 加 `artifact` 分发行与用法段；02 改 `task` 的用法段与参数解析；05 加 `issue` 的两个新动作的用法段；06 改 `dispatch` 的用法段与参数解析；09 删 `wiki` 分发行与用法段。谁都不重排别人的行 |
| 测试入口 `mmw/test.sh` | 一行一份测试。01 加产物落点测试那一行；09 删 Wiki 测试那一行；11 加落点字面值测试那一行 |
| 产物落点实现 `mmw/cli/lib/artifact.sh` | 一个 `artifact` 动作一个分区。01 建文件并独占 `path`；02 只改 `path` 的缺省工作名读取；03 加 `index`；04 加 `check`；08 加 `list`。谁都不改别人的动作行为 |
| 产物落点测试 `mmw/cli/tests/test_artifact.sh` | 一个动作一段用例。01 建文件并独占 `path` 用例；02 加缺省工作名用例；03 加 `index` 用例；04 加 `check` 用例；08 加 `list` 用例 |
| 护栏测试 `mmw/cli/tests/guardrails.sh` | 02 只改 task 分区的断言；06 只改 dispatch 分区的五处 `--task` 调用。两段互不重叠。另有一类行两边都没覆盖：别的分区在 setup 里调用 `mmw task new` 或 `mmw task bind` 建树。这类行归 02——它们要改是因为 02 让 `--name` 在无父工作名时必填。02 只补建树参数，不动那些用例的断言语义。落地时实测到的是第 436 行 |
| `AGENTS.md` | 03 改读取 ADR 那一句（随受管种子物化）；10 改唯一事实来源一段与领域上下文一段。09 不改这份文件——提交检查一段没有 Wiki 内容 |
| wayfinder 技能源（四个文件） | 08 独占交接表、ticket 正文模板、认领步骤和 map 正文小节标题；07 只改这四个文件里其余位置的落点字面值；06 只改其中的派发动作块。**交接表那几行归 08**，07 不碰——那几行既是落点又是接线，划给谁都行，划给 08 是因为它要重写整行的语义 |
| 其余技能源 | 03 加元数据块要求与只读例外；04 加产物引用声明、传递与校验命令行；06 只改派发动作块；07 改落点字面值、取名规则和入口分支判断；08 改对谈技能的取得事实一节与调查技能的索引那一节；09 删各处 Wiki 语义。六者的行互不重叠 |
| 收尾与恢复两份技能源 | `mmw-closing/SKILL.md` 与 `mmw-start/resuming.md` **整份归 09**，07 不碰。09 要完整重写这两份文件的流程，重写时直接用新的落点命令形态。这两处的落点行同时是 Wiki 流程步骤，两份 plan 各改一半会在集成时整段冲突，先落地的那一方被后一方覆盖 |

同一个技能文件被三份 plan 碰的两处，各自分区如下：`mmw-to-spec/SKILL.md` 由 03 规定六字段取值与回填 `spec_issue`，04 加两种声明、`## 工作名` 与 `## 输入出处` 两节的生产、`mmw artifact check` 调用行与 `mmw issue set-parent` 调用行，07 改落点字面值、取名规则与入口分支判断；`mmw-to-plan/SKILL.md` 由 03 验证 plan 的两字段，04 传递产物引用并运行校验，07 改落点字面值。

被两份 plan 碰的五处：`mmw-planner/references/self-check.md` 由 03 加元数据块就绪门，04 加产物引用声明自检；`mmw-review/SKILL.md` 由 03 加只读例外，07 改落点字面值；`mmw-implement/SKILL.md` 由 04 加产物引用传递、09 删 Wiki 归档那一行，07 改落点字面值；`mmw-implement/worker-brief.md` 由 04 加产物引用解析要求，07 改落点字面值；`mmw-start/SKILL.md` 由 09 删「Wiki 写一次」那一句，07 改落点字面值。`mmw-research/MAIN.md` 与 `mmw-grilling/SKILL.md` 的 07 与 08 分区已经写在上表的「其余技能源」一行里。

独占归属，没有分区问题的：产物落点数据归 01；任务状态实现归 02；14 份 ADR 与索引副本归 03；issue 实现归 05；宿主适配器与派发物化归 06；初始化实现归 09；领域文档 leaf 与 Context Map 归 10；查引用测试与落点字面值测试归 11。

### 跨 plan 接口

| 提供方 | 消费方 | 接口 | 字段 |
| --- | --- | --- | --- |
| 01 | 02、03、04、06、07、08、09、10、11 | 产物落点数据的记录结构与 `mmw artifact path` 的调用形态 | `mmw/cli/artifacts.json` 顶层是按类别名取值的对象，类别名不在记录内重复。每条记录十个字段：`term`、`root`、`root_kind`、`has_name`、`allows_scope`、`sub_naming`、`sub_fixed`、`sub_pattern`、`status`、`answered_by`。调用形态是 `mmw artifact path <类别> [--name <工作名>] [--issue <编号>] [--sub <类别内细分>] [--absolute]`，成功路径只写标准输出，提醒与错误只写标准错误 |
| 01 | 04 | 产物引用四项到路径的解析规则，`mmw artifact check` 复用它逐条解析 | 04 每次显式传 `--name`，复用同一解析结果和同一失败原因，不复制校验规则。该接口不检查目标路径是否存在——存在性由 04 自己判 |
| 02 | 01、06、07 | 任务状态输出里的工作名位。01 交付时 `--name` 必填，02 让它可缺省，缺省时读这个输出位 | `mmw task state` 的已绑定输出是 `bound <任务分支> <HEAD> <工作名>`，工作名是第四字段，前三个既有字段保持原位置。已绑定但缺少合法工作名时命令非零退出，且不输出状态行。`mmw artifact path` 缺省 `--name` 时只接受这个四字段输出，其他状态一律报错并且不输出路径 |
| 03 | 04 | 元数据块里承载产物引用的那个字段名与形状 | 字段名是 `artifact_refs`，始终存在；没有产物引用时写 `artifact_refs: []`。非空值是 YAML 映射列表，每项按 `category`、`name`、`issue`、`sub` 书写。`category` 与 `name` 必填，`name` 在持久化声明中不得缺省；`issue` 是整数，其余值是字符串；`issue` 与 `sub` 只在类别需要时出现。04 按键解析，不依赖键顺序，并且要能区分「没有元数据块」「没有该键」和「该键是空列表」三种情况 |
| 05 | 08 | 追加动作的调用形态。wayfinder 用它写 map 正文的决定索引 | `mmw issue append <issue 编号> --section "<小节标题>" --line "<要追加的一行>"`。`--section` 是二级标题的标题文字，wayfinder 传 `"Decisions so far"`，对应正文行 `## Decisions so far`。命令只在 V1 全部行与新增行都存在时成功；任一检查失败就重做，重做用尽后非零退出，并在标准错误输出缺失行原文 |
| 09 | 01、06 | 目标仓库配置里保留的四个工作目录根键名。01 解析工作目录根时读它们 | `.mmw.json` 的 `paths` 固定为 `scratch`、`reviews`、`release`、`worktrees` 四键，值由目标仓库配置，初始化迁移不覆盖已有值。01 的 `scratch` 记录 `root` 取 `scratch`，`review` 记录 `root` 取 `reviews`。`mmw init` 写进 `.gitignore` 的清单只含这四个根加 `graphify-out/`，不含 `.dispatch/` |
| 07、08 | 11 | 技能源改写完成后的落点写法。11 的两条正则规则要在改完的技能源上全绿 | 07 与 08 拥有的分区里不再出现「固定类别根加占位符」，也不再出现工作目录根默认值 `.scratch` 与 `.reviews`。命令里的类别参数值必须来自 01 的类别集合。11 扫描两者的合并结果，不增加临时豁免，也不修改技能源 |

字段由主 agent 从各份 plan 的 `## Change Map` 与 `## Contracts and Seams`，以及 `planner` 报告的跨 plan 接触点回填。回填后逐行核对过提供方与消费方：七行的双方写法一致，没有一份 plan 认领本节划给别份 plan 的分区。

### 一条给全部 `planner` 的边界

不认领本节划给别份 plan 的文件或分区。发现自己要改的位置归别人时，在报告的跨 plan 接触点里写出来，由主 agent 处置，不自行改动。

## Release Risk

**影响面是全部已装 MMW 的仓库。** MMW 是给多个仓库使用的工具箱，这次改的是全部产物的路径形状与产物引用。

**部署顺序有一处硬约束**：`mmw dispatch` 的 `--task <文件>` 改成标准输入是破坏性变更，CLI 与全部技能源的派发动作块必须同一批改完并同一次物化。分两批发会让中间那一批的派发全部失败。

**不可逆操作**：`mmw/cli/lib/wiki.sh` 与 `mmw/cli/tests/test_wiki.sh` 是删除，不是停用。删除前需要用户明确授权——`AGENTS.md` 规定删除现有发布入口前确认用户授权。用户在 decision ticket #27 已确认从未运行 `/mmw-closing`，也从未使用 Wiki，MMW 自身仓库的 Wiki 未初始化（克隆返回 `Repository not found`），因此没有内容会随删除而丢失。

**已知并接受的风险**：`agentflow` 仓库的 50 个 plan 目录保留旧的名字段取值，不改名。那 50 个目录里如果还有没交付完的任务，恢复它时 `mmw-start/resuming.md:24` 会按 `docs/plans/<工作名>/` 去找，目录名对不上就会判定 plan 没写。用户已知情并接受。

**这份 spec 自己落在旧路径上**。当前 `/mmw-to-spec` 规定 spec 落 `docs/specs/<任务 slug>/<任务 slug>.md`，本 spec 按当前生效的规则写在 `docs/specs/mmw-artifact-wiring/mmw-artifact-wiring.md`。它的元数据块已经按新合同写好，六个字段齐全，`spec_issue` 在发布后回填为 36。实现这份 spec 时把文件改名为 `docs/specs/mmw-artifact-wiring/spec.md`——不改名的话新增的 `mmw doctor` 检查会把它报出来。

**回滚方式**：全部改动在 Git 里，回滚是 revert 合并提交。路径形状与产物引用没有数据库或外部状态，回滚不产生中间态。已经按新合同写下的产物在回滚后仍然存在于旧路径规则找不到的位置，需要人工处理——这与前向的历史产物处理是同一类工作。

**没有新的用户交付物需要分发**。用户通过 `mmw/install.sh` 取得新版本，与既有做法一致。改产品版本时 `AGENTS.md` 列的五处版本号必须同步。

## Out of Scope

- 使用 MMW 的项目仓库中，非 MMW 产物的文档目录。这类文件不由任何 MMW 技能生产或读取。
- 技能源到各宿主技能产物的物化机制本身。MMW 已经具备这一层；本次只改被物化的内容，不改物化机制。
- 历史产物的自动迁移。不做 CLI 迁移命令，人工处理。
- 上游 wayfinder 与 grilling 技能的英文节标题字面。改它要先走 `upstream-skill-fidelity`，本次不改。
- `mmw-triage/examples.md` 里的路径写法。它是上游材料，改它要先走 `upstream-skill-fidelity`。
- handoff 文档的落点。它有上游对应，改它要先走 `upstream-skill-fidelity`。
- prototype 的 `README.md` 增加章节指引。它本身就是索引。
- 反向校验「产物存在而下游声明写无」。机器判不出相关性。
- map 正文的 `Decisions so far` 改成评论形态。评论只增不改确实不会被顶掉，但 map 正文就不再是一页纸的低分辨率视图，tracker 索引形态要跟着重做。

## Further Notes

**与 `awslabs/aidlc-workflows` v2 的关系。** 这项 effort 从它取得灵感，逐节对照过它的十二项机制（`docs/research/mmw-artifact-wiring/issue-30/aidlc-decision-audit/report.md`）。照搬的有四项：产物身份是名字不是路径；机械校验只校声明层引用完整性；缺失产物不许编造内容，并对被跳过的上游不做必然失败的检查；名称集合当场算出而不写成注册表文件。不照搬的核心理由只有一条——**aidlc 有引擎，MMW 没有**。aidlc 的下游只在 `consumes[]` 声明名字，由引擎在发 directive 时解析成路径；MMW 的每一跳都是 agent 读技能正文写出下一跳，两跳之间没有进程能做解析并注入下游上下文。所以承担解析的改成一条公开命令 `mmw artifact path`——aidlc 恰恰没有这条命令，因为解析是它引擎的内部行为。

另有两处方向相反且是有意的：产物落点锚定工作名而不是生产它的阶段（aidlc 是 `UNDER THE STAGE THAT OWNS THE FILE`），理由是一次交付有多条任务分支；产物引用不要求全局唯一（aidlc 的 Collision policy 要求），理由是产物引用带工作名，路径自带命名空间。

**没查清楚的部分**，实现时要补：

- `mmw task bind` 在 Codex App 宿主命名空间（`codex/` 前缀）下增加工作名参数之后的行为未实测。
- `mmw artifact path` 在 Codex App 的 managed worktree 下怎么解析仓库根未验证。`mmw_repo_root` 用 `git rev-parse --show-toplevel`，linked worktree 里的 `.mmw.json` 是该 checkout 自己那一份，行为看着成立，但没跑过。
- 后台 Bash 的标准输出在多大输出下会被宿主截断没有测过。去掉 `-o "$report"` 建立在「这个顾虑目前没有证据」之上。
- `mmw/skills-claude-code/`、`skills-pi/`、`skills-codex/` 三套已物化产物里的路径数量没有清点。它们由物化重新生成，数量不影响改法。
- aidlc 那条「没有全局产物落点门禁」是「已查范围内未找到」，不是完整否定结论；`resolveArtifactPath()` 的逐字源码未取得。

**这项 effort 的两次实际失效**都已被本 spec 涵盖：research 结论没传到下游由必读材料声明与交接表改动解决；map 正文丢行由 `mmw issue append` 解决。两次失效都发生在这项 effort 自己身上，不是假想的风险。
