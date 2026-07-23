# Investigate：用 Codex native subagents 查清现状

本阶段只摆证据，不选择方案、不下设计结论。产出固定写入
`docs/design/<slug>/investigating.md`，供 propose、design 和 build 使用。

## 决定调查范围

| 方向 | 查什么 | 可选外部 skill |
| --- | --- | --- |
| internal | 仓库模块边界、seam、数据流、根因 | `codebase-design`、`diagnosing-bugs`、`improve-codebase-architecture` |
| external | 成熟库、现有实现、第一方最佳实践；非必做 | 已安装的研究或文档 skill |

- 一个已知文件里的窄问题：主线程直接查，不派 subagent。
- 一个聚焦问题但要跨文件追调用链：派一个 topic subagent。
- 两个以上独立问题：一个 topic 一个 subagent，全部先派出再等待。
- internal 与 external 可以放在同一批并行；每个 topic 自己声明 `mode`。
- topic 只按真实问题拆，不凑数量、不设固定上限。

每个 topic 固定为 `{mode, angle, question, skill?}`。`skill` 只引用用户已经安装在
`~/.agents/skills/<skill>/SKILL.md` 的方法；plugin 不复制、不改写、不锁版本。

## 投查前 checkpoint

先按固定表格向用户展示：

```text
投查方向：<内部 / 外部 / 两者>
| # | angle | question | skill |
|---|---|---|---|
| 1 | <角度> | <唯一问题> | <skill 或 —> |
```

`attended` 等用户批、改或增删 topic 后再派；`afk` 展示后直接派；`unattended`
只按已确认范围派，不提问。

## 并行派 topic subagents

1. 定位 plugin root，完整读取
   `agents-roster/investigate-topic.md`。它只是 prompt 模板，不是 custom agent。
2. 给每个 topic 复制整份模板，在末尾追加唯一的 `<dispatch>` block：

   ```text
   <dispatch>
   mode=<internal|external>
   angle=<angle>
   question=<question>
   skill=<skill 或 none>
   repoRoot=<当前任务 App worktree 绝对路径>
   </dispatch>
   ```

3. 对每个 topic 调用 Codex native `spawn_agent`：
   - `fork_turns` 用 `none`，避免把主线程整段历史灌进机械取证任务。
   - `task_name` 用当前批次内唯一的短名，例如 `inv_module_boundary`。
   - 不传外部 CLI、不指定第二模型；这些调查工人使用 Codex 当前 GPT subagent。
   - 在同一轮连续发出全部 `spawn_agent`，中间不调用 wait，确保真并行。
4. 全部派完后用 `wait_agent` 等回执；需要看当前存活/完成状态时用
   `list_agents`。不要因先收到某一条结果就提前 synthesis。

## 校验、过滤和单 topic 重试

每个返回必须是 topic 模板规定的单个 JSON。用无状态合同脚本校验并过滤：

```bash
bash "$MMW_ROOT/scripts/investigate-contract.sh" topic \
  --mode <internal|external> --expected-topic <angle> <<'JSON'
<该 subagent 原样返回的 JSON>
JSON
```

脚本会：

- 拒绝非法 JSON、缺字段、多字段、topic 错配和 locator 类型错配。
- internal 只保留 `file:line` / `file:start-end`。
- external 只保留 URL。
- 丢弃 `low` confidence 或无有效 locator 的 finding。
- 把所有丢弃项原样保留在 `dropped`，不静默吞掉。

某个 topic 调用失败或合同不合法时，只处理该 topic：

1. 原 agent 仍可继续时，用 `followup_task` 把具体校验错误发回去，要求只重返合法
   JSON。
2. 原 agent 已不可用时，只为该 topic 再 `spawn_agent` 一次，仍使用同一 prompt。
3. 第二次仍失败就记入 `skipped`（angle + 真实失败原因），其他已通过 topic 不重跑。

全部 topic 都失败，或过滤后全批没有一条有效 finding 时，停止 synthesis。缩小问题
重派，仍无法取证则以 `needs-context` 诚实收口。

## 用全新 subagent synthesis

至少有一条有效 finding 后：

1. 完整读取 `agents-roster/investigate-synthesizer.md`。
2. 组装一个 JSON 对象：

   ```json
   {"topics":[<全部通过过滤的 topic 结果>],"skipped":[{"angle":"<失败 topic>","reason":"<真实错误>"}]}
   ```

3. 把这个对象放入模板末尾的 `<validated_evidence_json>`，不要加入原始对话、未过滤
   返回或主线程自己的判断。
4. 用 `spawn_agent(fork_turns="none")` 派一个全新的 GPT subagent。它只综合，不重新
   调查。
5. 等回执后校验：

   ```bash
   bash "$MMW_ROOT/scripts/investigate-contract.sh" report <<'JSON'
   <synth subagent 原样返回的 JSON>
   JSON
   ```

   校验失败时只纠正或重派 synthesis，不重跑已通过的 topics。

native agent target 只服务当前会话，不写入 `task.json`。会话中断后，阶段仍由
`mmw where` 恢复；未形成最终报告的 investigate 重新派发，不增加另一套 run
账本或 investigate 状态机。

## 主线程亲验并收口

1. 逐条打开承重 `file:line` 或 URL 亲验。外部库/API/规范结论沿引用链核到第一方
   来源；验不过的从正文删掉并记为待验。
2. 把 synth 的 `markdown` 和仍成立的 `open_questions` 写入
   `docs/design/<slug>/investigating.md`。
3. 亲验为真的 `spinoff_candidates` 逐条登记：

   ```bash
   mmw spinoff --tag <bug|optimize|out-of-scope|needs-evaluation> --finding "<一句话>"
   ```

4. 够后续使用：

   ```bash
   mmw handoff --conclusion pass --produced docs/design/<slug>/investigating.md
   ```

   必须用户补信息才能继续时用 `needs-context`。bug 无法重现时附已试重现路径；已经
   重现但无法定位根因时附已排除假设和证据，不能编一个根因继续。

investigate 不改 `docs/context`；领域文档由 design 阶段维护。
