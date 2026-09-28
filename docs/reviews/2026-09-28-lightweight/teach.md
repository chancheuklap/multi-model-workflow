# teach

## 定稿（主 agent 复核）

**判断**：上游正文的灵魂完整，本仓只改了三处，这三处没有废话。要做的是把 `e74e0140` 挪进 merge-note 的两句"为什么"放回正文，并补两个上游仍未修的缺陷在本机的对应处。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md` `### Self-contained pages` 开头（恢复原句，去掉破折号） | A lesson is often opened away from its folder (an editor preview, a rendering pane, a copy someone was sent), where every file it points at is lost and it arrives as unstyled text. So each page carries what it uses. | agent 看到同一节已要求起本地 HTTP 服务，会觉得嵌入是多余的，改成外链 `./assets/`；有了理由，它能判断清单外的东西（图片、字体、生成的 SVG）也要内嵌。learn-jev 建于这句还在的时候，所有页面都是自足的。 |
| I2 | `## Lessons` HTTP 交付那一句之后（恢复原句） | Opened straight from disk, under `file://`, some browsers block links that leave the page's own directory, so lessons and reference pages stop reaching each other. | 页面自足之后，起服务剩下的唯一理由是课程与参考页之间的跨目录链接。有了它，agent 能判断宿主自带的预览能不能代替，以及下次会话要不要重启服务。`file://` 的浏览器行为是 merge-note 的说法，未实测。 |
| I3 | `## Teaching Workspace` 第一句之后 | The workspace is the directory the user is learning in, never this skill's own directory where the `*-FORMAT.md` files sit. When the current directory belongs to another project, ask where the workspace is before writing anything. | 上游 issue #377（仍开着）：课程被写进技能目录。在本机，技能目录就是冻结的安装工作树，写进去就是改了 `AGENTS.md` 要求不动的副本。learn-jev 的交接文档也记着，会话启动目录是另一个产品仓库。 |
| I4 | `## Teaching Workspace` 文件清单加一项 | `GLOSSARY.md`: the workspace's canonical terms, one name per concept, used by every lesson and learning record. Use the format in [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md). | 上游 issue #559（仍开着）：`GLOSSARY-FORMAT.md` 在技能里没有入口。learn-jev 没有词汇表，你第三次指出同类术语问题后，才手工定下"一个概念只用一个名字"。能否因此避免那三次返工是推断。 |

### 连带改动

- `mmw-v2/merge-notes/teach.md` 两处"正文只写做法，理由只记在这里"改为"理由写在正文"；为 I3、I4 各加一行，写明"上游修掉 #377 / #559 → 收上游，删我们这一句"。

## 结论

`mmw-v2/upstream/skills/productivity/teach/` 共 2,904 词（`SKILL.md` 1,597、`MISSION-FORMAT.md` 253、`RESOURCES-FORMAT.md` 281、`LEARNING-RECORD-FORMAT.md` 416、`GLOSSARY-FORMAT.md` 343、`agents/openai.yaml` 14），没有脚本。与最近一次上游 squash（`5b1a4c51`，上游 `c55ee460`；上游 GitHub 上 `skills/productivity/teach` 此后没有新提交）相比，本仓只改了 `SKILL.md` 三处，合计约 140 词：`## Lessons` 的读者段和 HTTP 交付句、`## Assets` 的 `### Self-contained pages`。这三处都没有废话、没有死板流程，A 和 C 都是零条。问题出在反方向：提交 `e74e0140`（2026-09-22）把两句"为什么"删进了 merge-note，本仓加的两条做法因此只剩动作没有目的；另外上游有两个仍未关闭的缺陷，在本机唯一一个真实教学工作区 `/Users/cheuklapchan/learn-jev` 里有对应的迹象。建议净增约 110 词，不删任何东西。上游原文的"灵魂"完整，是这个技能的主体。

## A. 删除或改成脚本

无。逐句核对了本仓加的三处（`SKILL.md` 第 55、57、73–75 行）和四个 format 文件：没有复述脚本的内容（技能没有脚本），没有历史记录或 issue 号，没有空态度。上游原文里有少量 agent 默认会做的句子（例如 `LEARNING-RECORD-FORMAT.md` `## Numbering` 的 "Scan `./learning-records/` for the highest existing number and increment by one."），按任务书"为减字数删上游原文不提"，不列。

## B. 灵魂

### 保留，勿删

上游原文（本仓不改，列出是防止下一轮修剪误删）：

- `SKILL.md` 开头 "This is a stateful request - they intend to learn the topic over multiple sessions."：一句话定下整个技能的形状，工作区里的每个文件都是为跨会话连续性服务的。learn-jev 的 `docs/handoff/2026-09-20-b.md` 第 54 行写"每次会话开始先读它，再读工作区的 `MISSION.md`、`NOTES.md`、学习记录"，说明 agent 照这个意思在做。
- `SKILL.md` `## Philosophy`，"Never trust your parametric knowledge."：上游文档 `mmw-v2/upstream/docs/productivity/teach.md` 第 65 行记录了真实事故（给 2x2 魔方用户编造了解不开的公式）；learn-jev 的 `docs/handoff/2026-09-20-a.md` 第 86 行列了该会话更正过的七处说法。这句话是整套 `RESOURCES.md` 和引用要求存在的理由。
- `SKILL.md` `### Fluency vs Storage Strength` 全节：告诉 agent 流畅感是假的掌握，目标是长期保持，这决定了它设计练习而不是只写讲解。
- `SKILL.md` `## Lessons` "Learners' working memory is very small ... a single tangible win"：限定一课的尺度。learn-jev 学习记录 `0007-overview-first-then-narrow.md` 正是违反它的后果（第 5 课四页"内容过于繁杂"）。
- `SKILL.md` `## Lessons` 第 55 行 "The reader knows nothing about this topic. Pictures show ..."（本仓加的）：learn-jev 的 `NOTES.md` 记录学习者指出"第 1 课补充内容只搬了文字"、学习记录 `0004-statistics-vocabulary-is-new.md` 记录第 3 课用了一串没解释的术语，上游文档第 71 行也说"假定用户已懂"是最常见的实质投诉。这段守的是真实发生过的失败。
- `SKILL.md` `## Assets` "Reuse is the default, not the exception." 与 "A shared stylesheet is the first component every workspace earns, so the lessons look like one consistent course rather than a pile of one-offs."：说明组件复用的目的是"一门课"而不是"一堆页面"。
- `SKILL.md` `## The Mission` "Failing to understand the mission will mean knowledge acquisition is not grounded in real-world goals ... You will have no way of judging what the user should do next." 和 "Confirm with the user before changing the mission."：前者给出目的，后者划出 agent 与用户的权限边界。
- `SKILL.md` `## Knowledge` "For acquiring knowledge, difficulty is the enemy." 与 `## Skills` "For skill acquisition, difficulty is the tool."：一对相反的判断标准，agent 设计每一段内容时都要用。
- `SKILL.md` `## Acquiring Wisdom` 全节：给出技能能力的边界（真实世界的判断要交给社群），并要求尊重用户不加入社群的偏好。
- `SKILL.md` `## Reference Documents` "Lessons will rarely be revisited later - reference documents will be."：决定什么内容进 `reference/`。
- `MISSION-FORMAT.md` "A bad mission is worse than no mission." 和 "If `MISSION.md` runs past a screen, it has stopped being a compass and started being a plan."。
- `LEARNING-RECORD-FORMAT.md` "Coverage is not learning. Wait for evidence." 和 "The value is recording _that_ this is now known and _why_ it changes what to teach next"：防止把学习记录写成流水账。
- `GLOSSARY-FORMAT.md` "Building it is itself part of learning"、`RESOURCES-FORMAT.md` "A bare link is useless in three months."。

### 缺口与补充草稿

- `SKILL.md` `### Self-contained pages`（第 73–75 行）：只有做法，没有目的。提交 `e74e0140` 删掉了原来的第一句 "A lesson opened away from its folder — an editor preview, a rendering pane, a copy someone was sent — loses every file it points at, and arrives as unstyled text."，理由移进了 `mmw-v2/merge-notes/teach.md` `## 总原则`。缺了它，agent 看到同一节上方已经要求"起本地 HTTP 服务"，很自然会想"既然走 HTTP，`<link>` 到 `./assets/` 就能用，嵌入是多余的"，把这个设计简化掉；它也无从判断标记清单之外的东西（图片、字体、生成的 SVG）是否也要内嵌。证据：learn-jev 建于 2026-09-20，当时这句还在，agent 写的 `assets/build.py` 文档字符串就是"使页面可脱离目录单独打开"，所有页面没有一个相对路径的 `src=`。建议恢复（去掉破折号，`mmw-v2/tests/lib/check_upstream_em_dashes.py` 会拦）：
  > A lesson is often opened away from its folder (an editor preview, a rendering pane, a copy someone was sent), where every file it points at is lost and it arrives as unstyled text. So each page carries what it uses.

  顺带一处措辞：现文 "between `<!--CSS-->` and `<!--JS-->` markers" 可以读成"一个以 CSS 开头、以 JS 结尾的区间"。learn-jev 的 agent 自己改成了成对的开闭标记（`<!--CSS--><!--/CSS-->`）并加了第三对 `<!--LAB-->`，没有出错，所以只在恢复上面那句时顺手改成 "between paired markers (for example `<!--CSS-->` ... `<!--/CSS-->`)"，不单独立项。

- `SKILL.md` `## Lessons` 第 57 行 "Hand the finished lesson over by serving the workspace root over a local HTTP server ..."：同一次提交删掉了后半句 "A page opened straight from disk sits under `file://`, where some browsers refuse to reach anything outside the page's own directory — cross-document links go dead and the reader cannot tell why."。页面自足以后，起服务剩下的唯一理由就是 `./lessons/` 与 `./reference/` 之间的跨目录链接；agent 不知道这一点，就判断不了宿主自带的预览面板能不能代替、服务进程下次会话不在了要不要重启（learn-jev 两份交接文档都专门提醒"进程可能已不在，交付前确认并重启"）。建议恢复为：
  > Opened straight from disk, under `file://`, some browsers block links that leave the page's own directory, so lessons and reference pages stop reaching each other.

  注意：`file://` 的浏览器行为是 merge-note 的说法，我没有实测。

- 与现有裁定的冲突：`mmw-v2/merge-notes/teach.md` 的 `Lessons：If possible, open the lesson file…` 一行写"正文只写做法，这条理由只记在这里"，`## 总原则` 下也写"为什么要嵌入……不写进正文"。这与本任务书对"灵魂"的要求冲突，也与 `SKILL-SET-REVIEW.md` `### Redundancy and bloat` 的 "These stay" 一段冲突（"a reason the agent needs ... to keep a design choice it would otherwise simplify away"）。按任务书，上面两句应回到正文；merge-note 这两处措辞随之改为"理由写在正文里"。

## C. 死板的流程

无。本仓加的三处都是目标加做法，没有编号步骤、没有 if-then 清单。`<!--CSS-->` / `<!--JS-->` 这两个固定标记名看似替 agent 规定了细节，但没有任何共享脚本依赖它们，learn-jev 的 agent 也照需要加了自己的标记，所以它们起的是起步约定的作用，不构成限制。上游的 `## Zone Of Proximal Development` 三条和 `LEARNING-RECORD-FORMAT.md` `## When to write a learning record` 四条是判断标准，不是必须逐条执行的流程。

## 上游原文：在本仓使用中会让 agent 做错的两处

按 `SKILL-SET-REVIEW.md` `### Upstream skills`，上游原文只在"加了衔接文字仍会做错"时才改。这两处在 teach 之外没有可以放衔接文字的地方（技能是用户直接点名触发的，没有调用方），所以只能在 `SKILL.md` 里加句子，并在 merge-note 里登记。两处都是上游仍未关闭的 issue。

- **工作区位置**（上游 issue #377，OPEN："teach skill cannot locate the correct working directory (CWD)"）。`SKILL.md` 同时用 `./` 指两种根目录：`./MISSION-FORMAT.md` 等在技能目录里，`./lessons/`、`./assets/` 等在用户目录里；本仓加的 `./assets/build.py` 也沿用了这种写法。上游文档第 59 行记录了课程被写进 `~/.claude/skills` 的真实事故。在本机，技能目录解析到冻结的安装工作树 `.worktrees/mmw-installed/mmw-v2/upstream/skills/productivity/teach/`；课程写进那里就是改动了 `AGENTS.md` `## Self-hosting boundary` 要求不动的安装副本。另一个真实情形：learn-jev 的 `docs/handoff/2026-09-20-b.md` 第 7 行记录会话的启动目录是另一个产品仓库 `/Users/cheuklapchan/agentflow`，每条命令后还会被重置回那里，而 `## Teaching Workspace` 第一句是 "Treat the current directory as a teaching workspace."。该次 agent 靠用户指明路径、全程用绝对路径避开了；我查了安装工作树，目前没有误写入的文件。四问：本机没有触发过，但正常使用可以走到（在产品仓库的会话里点名 teach），前提有上游事故和本机交接文档两处实证，所以不算过度防御。建议在 `## Teaching Workspace` 第一句后加：
  > The workspace is the directory the user is learning in, never this skill's own directory where the `*-FORMAT.md` files sit. When the current directory belongs to another project, ask where the workspace is before writing anything.

- **词汇表没有入口**（上游 issue #559，OPEN："GLOSSARY-FORMAT.md is an orphan"）。`## Teaching Workspace` 的文件清单没有 `GLOSSARY.md`，全文没有链接 `GLOSSARY-FORMAT.md`；`LEARNING-RECORD-FORMAT.md` 却把 `[[GLOSSARY.md]]` 当作已存在的文件引用。learn-jev 没有 `GLOSSARY.md`；它的 `NOTES.md` `## 写课的硬规则` 记录负责人"第三次指出同类问题后"定下"一个概念全课只用一个名字，官方有多个叫法的，定义时说明并选定一个"，这几乎就是 `GLOSSARY-FORMAT.md` 的 "Be opinionated" 和 "Flag ambiguities explicitly" 两条。一份被链接的词汇表能否避免那三次返工，是推断，不是证实；但它至少补上了 `SKILL.md` 第 142 行 "Glossaries, in particular, are an essential reference" 与格式文件之间断掉的一环。建议在文件清单里加一项：
  > - `GLOSSARY.md`: the workspace's canonical terms, one name per concept, used by every lesson and learning record. Use the format in [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md).

  两处都要在 `mmw-v2/merge-notes/teach.md` 各加一行意图，并写明"上游修掉 #377 / #559 → 收上游，删我们这一句"。

看过、判断不必改的上游问题：上游文档第 68 行说的"正确答案总在第一个选项"，在 learn-jev 的 40 道测验里不成立（正确项在第 1、2、3 位分别是 5、20、15 次）；上游文档第 74 行说的"不会主动提出转入复习"是上游功能缺口（issue #725 一类的功能请求），不是本仓工作流造成的，不提。

## 脚本

无。考虑过一个方向并否决：`./assets/build.py` 是每个工作区由 agent 自己写的确定性脚本，看起来符合"确定性的事交给脚本"，可以做成技能自带的 `scripts/`。不建议这样做：教学工作区是独立的、可提交可分享的目录（learn-jev 就是独立 git 仓库，上游文档第 24 行推荐这样用），把重建脚本放在技能目录里会让工作区依赖本机的 MMW 安装才能重建；每个工作区的组件不同（learn-jev 有第三对标记 `LAB`），通用脚本需要额外约定；而 agent 写这个脚本只要二十来行。

## 与其他技能的重复或交接问题

- 第 55 行的读者段与 `mmw-v2/upstream/skills/productivity/wait-what/VISUAL.md` 第 18 行、`mmw-v2/upstream/skills/engineering/improve-codebase-architecture/HTML-REPORT.md` 第 24 行逐字相同。三份各由不同技能在动手那一刻加载，都该留；三份 merge-note 已登记"改一处，三处一起改"。这一段的第一句 "The reader knows nothing about this topic." 与 teach 自己的学习记录机制（`LEARNING-RECORD-FORMAT.md` 第 34 行 "Record it so future sessions don't re-teach it"）字面上有张力；但实际发生的失败全在反方向（假定用户懂得太多），所以不建议为 teach 单独改这一句，也就不必打破三份同步。
- `mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md` 第 88 行对 teach 的描述与技能一致，没有问题。

## 没查到的

- `file://` 下浏览器拒绝跨目录链接的说法（merge-note 的依据）没有实测。
- learn-jev 的课件正文只用 grep 抽查了 `src=`、`href=`、`<link>` 和测验结构，没有通读；两份交接文档只按关键词检索。
- 上游 issue #335（上游文档引用的测验位置问题）在 `mattpocock/skills` 里用 `gh issue view` 查不到，可能是 PR 或已迁移，没有继续查。
- 没有逐字读 `wait-what` 和 `improve-codebase-architecture` 的全文，只核对了三份读者段是否一致。
