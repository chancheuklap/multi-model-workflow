---
date: 2026-08-11
amends: []
---

# map 正文的决定索引由 CLI 追加，不由 agent 拼整份正文写回

`mmw/skills-src/mmw-wayfinder/walking.md:69` 规定每张 decision ticket 解完要往 map 正文的 `Decisions so far` 追加一行，但没有给出改正文的命令，`mmw/cli/lib/issue.sh` 也没有这个动作——它只有 create、claim、link、children、frontier。agent 因此各自用 `gh issue edit --body-file` 拼整份正文写回。三个会话并行时，先写的那一行被后写的整份覆盖，本 effort 已经发生两次。现在改为：`mmw issue` 增加一个追加动作，读最新正文、在指定小节插入这一行、写回、再读比对上一版的行集合，少行就自己重做；技能正文那两条手工自检删掉。

两次实例：

| 丢的那一行 | 关闭时间 | 被谁覆盖 |
| --- | --- | --- |
| decision ticket #25「历史产物迁移命令的形态与边界」 | 2026-08-11 10:51:04 | 随后关闭的 #26 与 #23 |
| decision ticket #31「长期产物的清单写成仓库文件还是命令当场输出」 | 2026-08-11 12:52:42 | 随后关闭的 #33 |

两次都由集成的主 agent 手工核对行数才发现，没有任何机械动作报错。

## Considered Options

- **写之前比对版本号，版本变了就拒绝，也就是乐观锁。** 否决，GitHub 不支持。实测对 `PATCH /repos/{owner}/{repo}/issues/{n}` 带 `If-Match` 头返回 400，错误原文是 `"Conditional request headers are not allowed in unsafe requests unless supported by the endpoint"`；同一请求去掉该头正常成功。issue 更新这个 endpoint 不在支持条件请求的名单里。这条路是硬堵死的，不是实现难度问题。
- **决定改成评论，不放在 map 正文里。** 否决。评论只增不改，确实不存在覆盖；但 map 正文就不再是一页纸的低分辨率视图，`0002-tracker-repo-authority.md` 定的 tracker 索引形态要跟着重做。代价大于收益。
- **维持现状，把手工自检的措辞写得更严。** 否决。现有自检查的是「自己那一行在不在」，而这类丢失发生时两个会话的自检都通过：会话 B 写回的是它更早读到的那一版，它从来没有见过会话 A 的行，所以 B 检查自己那行时一切正常。加严措辞改变不了这个时序。
- **在追加命令之外，再加一道收口前的全量核对。** 否决。命令自带写后验证之后，剩下的窗口是命令执行的几百毫秒。为它单独架一道例行检查，正是 `0010-computed-index.md` 否决过的那一类——要人主动跑，日常没人跑。真漏了那一次用 GraphQL 的 `userContentEdits` 事后查即可，那是现成能力，不必预先变成流程。

## Consequences

- `mmw issue` 增加追加动作。参数是 issue 编号、小节标题和要追加的内容。四步在一条命令内完成：读最新正文、在指定小节末尾插入、写回、再读比对。比对的对象是**上一版的行集合**，不是「自己那一行在不在」——后者查不出这类丢失。少行时命令自己重做，重做有次数上限；用尽仍不一致就非零退出，不静默。
- **判据修正**：本 spec 的第 12 节把成功判据改为两项同时成立：V1 的全部行都在 V3，且本次新增行也在 V3。任一项不成立都重做。上一条只把两项中的一项与另一项对照，描述不完整。
- 命令不为 map 写死。小节标题是参数，将来出现第二个并发编辑点时命令现成。规则这一层只规定 map 正文这一处必须用它：技能源里现在没有第二处二次编辑 issue 正文的地方，`mmw issue create` 出现在 `mmw-to-spec`、`charting` 与 `mmw-to-tickets` 三处，都是建立时写一次。
- `mmw/skills-src/mmw-wayfinder/SKILL.md:89` 与 `walking.md:69` 那两条手工自检删掉，换成一句「用 `mmw issue` 的追加动作，不要自己拼整份正文写回」。留着它们等于让 agent 手工再做一遍命令已经做的事，而且做的是被证明无效的那一种。
- 竞态窗口从「agent 读到写之间的思考时间」缩到「命令执行时间」。它不为零。这是本决定接受的代价。
- GraphQL 的 `userContentEdits` 是覆盖发生后的调查手段，不是例行检查。map #18 当前有 19 个版本，每版带 `editedAt`、`editor` 和当时的完整正文，比对相邻两版能看出哪几行消失，也能据此还原。
- 命令的名字、参数形状、重做次数上限和小节定位方式留给 spec 阶段。

## 与 aidlc-workflows v2 的对照

出处是 `docs/research/mmw-artifact-wiring/issue-20/aidlc-v2-artifact-wiring/report.md`。

- **aidlc 没有这个问题，而且它的解法 MMW 用不了。** 它的 state 由引擎串行写入：conductor 执行引擎给出的一个 directive，不自行计算下一阶段，也不自行拼接或登记产物位置（第 7 节）。靠的是「只有一个进程写」这个结构。MMW 的每个会话是独立进程，直接对 tracker 写，没有那一层。
- **本决定取的是能做到的最接近形态。** 把写这个动作收进一条命令，让读、改、写在一次进程内完成，窗口缩到命令执行时间。它不等于串行化，只是把窗口从分钟级压到毫秒级。
- **在 written 与 computed 之间这次取 written 一侧。** `"The registry is computed, not written."`（第 8 节）说的是注册表可以从声明派生。map 的 `Decisions so far` 不是派生物——它是每张 ticket 关闭时人写下的一句话概要，算不出来，所以必须写下来，也因此必须解决并发写。

来源：Wayfinder decision ticket #35「map 的决定索引会被并发会话覆盖」，map #18「MMW 产物归纳与接线合同」。
