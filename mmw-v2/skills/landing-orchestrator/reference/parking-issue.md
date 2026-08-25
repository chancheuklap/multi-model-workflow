# 停车 issue 模板

每个卡点一张 issue，标签 `blocked:decision`，挂任务父 issue 为父，并设成该票的原生 blocker。停车不阻塞循环：该票让路（摘认领、留评论），编排者回到查 frontier。

回程走的是 frontier 已有的那道门：`issue_dependencies_summary.blocked_by` 只数**开着的** blocker（`docs/agents/issue-tracker.md`「Wayfinding operations」）。人裁决完关掉停车 issue，票的 `blocked_by` 自己归零，下一轮查 frontier 它就回来了——不需要谁记得再补一个动作。`blocked:decision` 标签同时让停车 issue 自己不被当成票派出去（`scripts/frontier.py`）。

正文格式逐字取自 pstack `orchestrate.md` @46125561 所述的 `gates.md`（渲染器 `pstack/skills/poteto-mode/scripts/orch/store.ts` 的 `renderGates`）：`# Gates` 标题，每个 gate 一个 `## <id>` 块，字段 `Status`、`Question`、`Options`、`Default`，解决后加 `Answer`。本仓库做的唯一修改：在 `Default` 之前加一行 `Consequences`（spec 要求的「后果」段）。

## 创建

```bash
# 标签不存在先建
gh label list --json name --jq '.[].name' | grep -qx 'blocked:decision' || gh label create 'blocked:decision' --description '等人裁决的停车点' --color D93F0B
n=$(gh issue create --title "停车 #<票号>：<一句话问题>" --label blocked:decision --body-file <正文文件> --json number --jq .number 2>/dev/null \
    || gh issue create --title "停车 #<票号>：<一句话问题>" --label blocked:decision --body-file <正文文件> | grep -o '[0-9]*$')
# 下面两条都用数据库 id，不是 #编号
id=$(gh api repos/<owner>/<repo>/issues/$n --jq .id)
# 挂到任务父 issue 下
gh api --method POST repos/<owner>/<repo>/issues/<父票号>/sub_issues -F sub_issue_id="$id"
# 让它挡住这张票：裁决后关掉它，票自己回 frontier
gh api --method POST repos/<owner>/<repo>/issues/<票号>/dependencies/blocked_by -F issue_id="$id"
# 摘掉认领：停车期间这张票不属于任何人，别的会话看得出它不在途
gh issue edit <票号> --remove-assignee @me
```

## 正文

```
# Gates

## gate-<票号>-<序号>

- Status: open
- Question: <一句话说清卡在什么决定上；附工人的原话或 blocked 画面里的问题文本>
- Options: <A. … / B. … / C. …，每个选项一句话>
- Consequences: <对每个选项：选它会发生什么，A. … / B. … / C. …>
- Default: <不裁决时编排者会按哪个选项走，以及什么时候走；写「不走」则该票一直让路>
```

字段值可以跨多行：续行缩进两个空格。

## 裁决

人在正文里把 `Status: open` 改成 `Status: resolved`、加一行 `- Answer: <选项>`，然后关闭 issue。关闭这一下就是回程：被挡住的票 `blocked_by` 归零，编排者下一轮查 frontier 会重新派它。早上列全部待裁决项：

```bash
gh issue list --label blocked:decision --state open
```
