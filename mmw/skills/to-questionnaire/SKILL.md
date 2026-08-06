---
name: to-questionnaire
description: 把当前用户无法独自回答的决定写成给知识持有者填写的 questionnaire。
disable-model-invocation: true
---

把当前用户无法独自回答的内容变成一份 **questionnaire**。用户把 Markdown 发给一位掌握缺失知识的人，由对方异步填写，或者在会议中共同填写。

**只 grill 发送过程，不 grill 主题。** 当前用户能回答的是问卷发给谁，以及需要从对方拿回什么。问卷的问题再对准知识持有者和信息缺口。

## 1. 确认收件人

一次问清收件人的角色、专业领域，以及与当前用户的关系。这些信息决定语气和问卷需要自带多少上下文。

完成判据：知道收件人是谁，以及他掌握什么当前用户缺少的知识。

## 2. 确认需要拿回什么

一次问清当前用户无法独自解决、必须由收件人提供的事实和决定。

完成判据：得到一份具体清单，说明问卷回来后用户必须能够完成哪些决定或动作。

## 3. 写 questionnaire

先确定当前任务的产物目录。Wayfinder 场景从当前 map 或子 issue 正文的 `## 产物目录` 读取；decision ticket 同时读取正文记录的 `issue-<编号>`。Wayfinder 派生的 spec 任务从已绑定任务状态读取任务 slug，并使用 `task-<任务 slug>` 子目录。普通任务使用当前任务 slug，不带子目录。不要从任务 worktree 的物理目录名推断。

运行 `mmw artifact path scratch <产物目录> [issue-<编号>|task-<任务 slug>]`，在命令返回的 Git 忽略 scratch 目录写 `to-questionnaire-<slug>.md`，slug 取主题。不要写当前目录。完成后报告路径。

用户明确要求长期保存 questionnaire 时，改写到用户指定的正式落点。

把它写成 discovery questionnaire。问题按重要性排序；超过少量问题时按主题使用 `##` 分组。每题只问一个意图，并在题目下直接留下回答位置。只有问题可能被误解或得到敷衍答案时，才补一行“为什么重要”。

```markdown
# <Questionnaire title>

**Purpose:** <为什么要问，以及哪项决定取决于答案>

**From:** <当前用户> — **To:** <收件人> — **How your answers will be used:** <答案进入哪里>

## Context

<让未参与此前讨论的收件人能够作答的一段上下文>

## How to answer

<截止时间和预计用时。说明部分回答和“不知道”也有用；不确定时请标出来>

## <Theme heading>

### <一个意图的问题>

_Why this matters: <只有需要时才写>_

>

## Anything else?

<还有什么没有问到但应该知道？>
```

完成判据：文件存在；第 2 步清单中的每一项都由至少一个问题覆盖；没有复合问题；每题都有回答位置。

## 4. 吸收答案并清理

调用方拿到答案后，先把答案吸收到共同理解、ticket、spec 或其他正式产物。确认正式产物已经完整承载答案后，删除 scratch 中的 questionnaire 和答案副本。用户明确要求长期保存时保留用户指定的正式副本。

完成判据：正式产物已经承载下游需要的答案；scratch 不再保存 questionnaire 和答案副本，或者已有用户明确要求的长期保存落点。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| Questionnaire 已生成 | **停**：报告 scratch 文件路径和收件人，等待答案返回 |
| `/mmw-grilling` 因当前用户不掌握事实而移交进来，答案已经返回 | **移交**：`/mmw-grilling`，先把答案吸收到共同理解，再按第 4 步清理 scratch 副本 |
| 收件人或信息缺口仍不清楚 | **自己继续**：回第 1 步或第 2 步，只追问发送过程 |
