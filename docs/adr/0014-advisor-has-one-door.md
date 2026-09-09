---
date: 2026-09-08
amends: []
---

> 现行读法见 ADR 0015：`## Consequences` 第三条末句「`assemble.py` 的补位机制不变，仍然由 reviewer 在 claude 上那一行用着」不再成立——`assemble.py` 连同 `mmw-v2/agents/` 整个目录已经删掉，`models.md` 的解析搬进了 `mmw-v2/skills/dispatch/scripts/models.py`。advisor 只有一扇门、正文是技能、两侧共用这个决定本身没有变。

# advisor 只有一扇门：正文是技能，两侧共用

advisor 不再有 native subagent。它只是一个 Paseo 会话，由撞上决定的那个 agent 用 `create_agent` 起，`initialPrompt` 点 `advisor` 技能的名字。技能分两扇门：`references/consulting.md` 给要问的人，`references/advising.md` 给答的人。

## 要修的是什么

派 advisor 的 main agent 经常替它划定调查范围——告诉它查哪几点、跳过哪个文件、期待哪个结论。一个只查了你让它查的东西的第二意见，是你自己的意见换了个更强的模型说出来。

三条原因，前两条是文字缺失，第三条是结构：

- **caller 看得见的任何文字里都没有这条禁令。** 它只写在 advisor 自己的正文里，而那份正文只有 advisor 读。
- **advisor 自己的正文在教它服从边界。** 原正文的 `Expand scope. Answer the decision you were asked` 落到实处，就是"caller 收窄过的那个问题"。
- **advisor 是这条流水线里唯一由模型现写 prompt 的 agent。** worker、reviewer、verifier 的 `initialPrompt` 由 `dispatch.sh` 打印；只有 advisor 留了空白，而 `create_agent` 的 `initialPrompt` 字段本身就是"派活"的语义。

## 为什么这修法要动那扇门

禁令要落在 caller 恒在 context 的位置才管用。技能的 frontmatter `description` 正是这样一个位置——host 启动时扫进去，五个 host 都扫。native subagent 的 `description` 也是，但它只在 native 那条路上；两个位置同时存在，就是同一份触发条件维护两遍，而 advisor 已经不走 native 那条路了。

## Considered Options

- **留着 native subagent，只补文字。** 否决。两份门各自维护同一份触发条件，且 Paseo 那扇门的 `initialPrompt` 里钉着 `~/.claude/agents/advisor.md` 这个 claude 专属的绝对路径——它今天能用只因为 advisor 的 `bypass` 行恰好落在 claude 这一格，行一挪就指错。
- **caller 那侧写进用户级提示词。** 否决。`mmw-v2/prompt/shared.md` 到不了 Cursor（Cursor 的用户级提示词在 app 里手动维护），而技能装进 `~/.agents/skills` 五家都扫。它还要为一件偶尔发生的事付每回合的常驻 context。
- **由脚本生成 advisor 的 `initialPrompt`，像 `dispatch.sh` 对三种流水线 agent 那样。** 否决。包的内容只有 caller 有，脚本只能生成骨架，重量远大于一份 reference 能拿到的收益。
- **给 advisor 换一个只读权限档。** 查证后否决。`inspect_provider claude` 的档位是 `plan`、`default`、`acceptEdits`、`auto`、`bypassPermissions`，没有只读档；`plan` 会把 advisor 推进"提交计划等批准"的流程，而无人值守时没人去批。

## Consequences

- **没有任何权限档拦着 advisor 写文件**，拦住它的是 `references/advising.md` 里那条规则。这不是这次改动的代价：native 那扇门的 description 本来就写着"`list_profiles` 列出 advisor 就改用 `create_agent`"，装了 Paseo 的机器从不走它；它的 `tools` 列表还带着 `Bash`，本来也拦不住写。`inspect_provider claude` 没有只读档，也不收工具白名单，所以只读这件事在这台机器上从来只有一种实现方式，就是写在文字里。
- **advisor 跑在 caller 的 workspace 里**，看得见未提交的改动——正在被决定的那份工作往往还没提交，看不见就答不了。代价是它一旦违规写入，写的就是 caller 正在改的文件。不要为此给它单开 worktree：那样它就看不见未提交的改动了。
- **`models.md` 里 advisor 只剩一行**，`bypass`。原先五条 `—` 行没了，`agents/advisor/` 目录也没了。`assemble.py` 的补位机制不变，仍然由 reviewer 在 claude 上那一行用着。
- **profile 的 `notes` 里不再有任何绝对路径**，只有技能名。advisor 的 `bypass` 行以后换到哪个 host 都不用改这句话。
- **技能同时被 main agent 和 advisor 调用。** 它是 model-invoked 的：main agent 必须能自己够到它，这正是修法本身。
