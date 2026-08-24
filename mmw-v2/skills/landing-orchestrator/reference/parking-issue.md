# 停车 issue 模板

每个卡点一张 issue，标签 `blocked:decision`，挂任务父 issue 为父。停车不阻塞循环：该票让路（保留认领、留评论），编排者回到查 frontier。

正文格式逐字取自 pstack `orchestrate.md` @46125561 所述的 `gates.md`（渲染器 `pstack/skills/poteto-mode/scripts/orch/store.ts` 的 `renderGates`）：`# Gates` 标题，每个 gate 一个 `## <id>` 块，字段 `Status`、`Question`、`Options`、`Default`，解决后加 `Answer`。本仓库做的唯一修改：在 `Default` 之前加一行 `Consequences`（spec 要求的「后果」段）。

## 创建

```bash
# 标签不存在先建
gh label list --json name --jq '.[].name' | grep -qx 'blocked:decision' || gh label create 'blocked:decision' --description '等人裁决的停车点' --color D93F0B
n=$(gh issue create --title "停车 #<票号>：<一句话问题>" --label blocked:decision --body-file <正文文件> --json number --jq .number 2>/dev/null \
    || gh issue create --title "停车 #<票号>：<一句话问题>" --label blocked:decision --body-file <正文文件> | grep -o '[0-9]*$')
# 挂到任务父 issue 下（sub-issue 用 issue 的数据库 id，不是编号）
gh api --method POST repos/<owner>/<repo>/issues/<父票号>/sub_issues -F sub_issue_id="$(gh api repos/<owner>/<repo>/issues/$n --jq .id)"
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

人在正文里把 `Status: open` 改成 `Status: resolved`、加一行 `- Answer: <选项>`，然后关闭 issue。早上列全部待裁决项：

```bash
gh issue list --label blocked:decision --state open
```
