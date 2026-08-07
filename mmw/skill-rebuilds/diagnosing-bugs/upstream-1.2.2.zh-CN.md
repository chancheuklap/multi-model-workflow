# `diagnosing-bugs` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/diagnosing-bugs/SKILL.md:1-4 -->

```yaml
---
name: diagnosing-bugs
description: 用于困难 bug 和性能回归的诊断循环。用户说“诊断”“调试这个问题”，或报告某项内容损坏、抛出异常、失败或缓慢时使用。
---
```

<!-- source: vendor/mattpocock-skills/skills/engineering/diagnosing-bugs/SKILL.md:6-18 -->

# Diagnosing Bugs

一套处理困难 bug 的纪律。只有在明确说明理由时，才能跳过阶段。

探索代码库时，读取 `CONTEXT.md`（如果存在），以建立对相关 module 的清晰心智模型；同时检查本次涉及范围内的 ADR。

## 阶段 1——建立反馈循环

**这就是本技能。** 其他一切都是机械操作。如果你拥有一个针对该 bug 的 **tight** 通过或失败信号，也就是一个会因为**当前** bug 变成 red 的信号，你就能找到原因；二分、假设检验和插桩都只是消费这个信号。如果没有，无论盯着代码看多久都无济于事。

在这里投入不成比例的精力。**积极尝试。发挥创造力。拒绝放弃。**

### 构建反馈循环的方法——大致按照以下顺序尝试

<!-- source: vendor/mattpocock-skills/skills/engineering/diagnosing-bugs/SKILL.md:20-31 -->

1. 在任何能够触及 bug 的 seam 上编写**失败测试**，可以是单元测试、集成测试或端到端测试。
2. 针对正在运行的开发服务器执行 **Curl 或 HTTP 脚本**。
3. 使用 fixture 输入执行 **CLI 调用**，并把 stdout 与已知正确的快照进行 diff。
4. 使用 **headless 浏览器脚本**，例如 Playwright 或 Puppeteer，驱动 UI，并对 DOM、控制台或网络作出断言。
5. **重放捕获的 trace。** 把真实的网络请求、载荷或事件日志保存到磁盘；在隔离环境中通过代码路径重放它。
6. **一次性 harness。** 启动系统的最小子集，例如一个服务和模拟依赖，并通过一次函数调用执行 bug 代码路径。
7. **属性或 fuzz 循环。** 如果 bug 是“有时输出错误”，运行 1000 个随机输入，并寻找失败模式。
8. **二分 harness。** 如果 bug 出现在两个已知状态之间，例如提交、数据集或版本，就自动执行“在状态 X 启动、检查、重复”，以便使用 `git bisect run`。
9. **差异循环。** 让同一个输入分别经过旧版本与新版本，或两套配置，然后对输出作 diff。
10. **HITL Bash 脚本。** 这是最后手段。如果必须由人类点击，就用 `scripts/hitl-loop.template.sh` 驱动**人类**，使循环仍然结构化。捕获的输出会返回给你。

建立正确的反馈循环，bug 就已经修复了 90%。

<!-- source: vendor/mattpocock-skills/skills/engineering/diagnosing-bugs/SKILL.md:33-41 -->

### 让循环更加 tight

把循环当成产品。拥有一个循环后，继续让它变得更加 **tight**：

- 能否让它更快？例如缓存设置、跳过无关初始化、缩小测试范围。
- 能否让信号更明确？断言具体症状，不要只断言“没有崩溃”。
- 能否让它更具确定性？固定时间、设定 RNG seed、隔离文件系统、冻结网络。

一个需要 30 秒且 flaky 的循环只比没有循环稍好；一个 2 秒且确定的循环是 tight 的，这是调试工作的超级能力。

<!-- source: vendor/mattpocock-skills/skills/engineering/diagnosing-bugs/SKILL.md:43-60 -->

### 非确定性 bug

目标不是得到一次干净复现，而是获得**更高的复现率**。循环执行触发操作 100 次、并行执行、增加压力、缩窄时间窗口、注入休眠。复现率为 50% 的 flaky bug 可以调试，复现率为 1% 的 bug 不可以。继续提高复现率，直到能够调试。

### 确实无法建立循环时

停止，并明确说明。列出尝试过的内容。向用户请求以下任一项：(a) 能够复现问题的环境访问权限；(b) 捕获的产物，例如 HAR 文件、日志转储、核心转储或带时间戳的屏幕录制；(c) 增加临时生产环境插桩的许可。**不要**在没有循环时继续提出假设。

### 完成判据——一个会变成 red 的 tight 循环

当循环既 **tight** 又 **red-capable** 时，阶段 1 完成：你可以指出**一条命令**，例如脚本路径、测试调用或 curl；你已经**至少运行过它一次**，并能粘贴调用及其输出；这条命令满足：

- [ ] **Red-capable**——它会执行真实 bug 代码路径，并断言**用户所述的准确症状**，因此能在当前 bug 上变成 red，并在修复后变成 green。它不能只是“运行时没有报错”，而必须能够**捕获这个具体 bug**。
- [ ] **具有确定性**——每次运行都得到相同结论。对于 flaky bug，按照上方规则固定并取得较高复现率。
- [ ] **快速**——只需几秒，不是几分钟。
- [ ] **Agent 可运行**——你可以在无人值守时运行它；只有通过 `scripts/hitl-loop.template.sh` 才允许 human in the loop。

如果你发现自己在这条命令存在前就阅读代码以建立理论，**立即停止；直接跳到假设，正是本技能要防止的失败。** 没有 red-capable 命令，就不能进入阶段 2。

<!-- source: vendor/mattpocock-skills/skills/engineering/diagnosing-bugs/SKILL.md:62-80 -->

## 阶段 2——复现并最小化

运行循环。观察它变成 red，也就是 bug 出现。

确认：

- [ ] 循环产生的是**用户**描述的失败模式，不是碰巧位于附近的另一个失败。认错 bug，就会做出错误修复。
- [ ] 失败可以在多次运行中复现。对于非确定性 bug，复现率必须高到足以据此调试。
- [ ] 你已经捕获准确症状，例如错误消息、错误输出或缓慢的耗时，使后续阶段能够验证修复确实解决了该症状。

### 最小化

循环变成 red 后，把复现缩小到**仍然会变成 red 的最小场景**。每次只削减一项输入、调用方、配置、数据或步骤；每次削减后重新运行循环。只保留导致失败不可缺少的内容。

这样做的理由是：最小复现会缩小阶段 3 的假设空间，因为可怀疑的活动部分更少；它也会成为阶段 5 中干净的回归测试。

当**每个剩余元素都不可缺少**时完成最小化；移除任何一个元素都会使循环变成 green。

完成复现**并且**完成最小化之前，不要继续。

<!-- source: vendor/mattpocock-skills/skills/engineering/diagnosing-bugs/SKILL.md:82-92 -->

## 阶段 3——提出假设

测试任何假设之前，先产生 **3 至 5 项按可能性从高到低排序的假设**。只提出一项假设会使你锚定第一个看似可信的想法。

每项假设都必须**可以证伪**：说明它作出的预测。

> 格式：“如果 <X> 是原因，那么 <改变 Y> 会使 bug 消失，或 <改变 Z> 会使 bug 更严重。”

如果无法说明预测，这项假设就只是感觉；丢弃它，或使它更加明确。

**测试前向用户展示排序后的清单。** 用户通常拥有能够立即改变顺序的领域知识，例如“我们刚刚部署了与第 3 项相关的改动”；也可能知道哪些假设已经被排除。这是成本很低、可以节省大量时间的检查点。不要因此阻塞；如果用户 AFK，就按照你的排序继续。

<!-- source: vendor/mattpocock-skills/skills/engineering/diagnosing-bugs/SKILL.md:94-106 -->

## 阶段 4——插桩

每个探针都必须对应阶段 3 中的一项具体预测。**每次只改变一个变量。**

工具优先顺序：

1. 环境支持时，使用**调试器或 REPL 检查**。一个断点胜过十条日志。
2. 在能够区分不同假设的边界处增加**定向日志**。
3. 绝不“记录一切，然后 `grep`”。

为**每一条调试日志增加标记**，使用唯一前缀，例如 `[DEBUG-a4f2]`。最后只需一次 `grep` 就能完成清理。没有标记的日志会留下；有标记的日志会删除。

**性能分支。** 对于性能回归，日志通常是错误工具。应先建立基线测量，例如计时 harness、`performance.now()`、性能分析器或查询计划，然后进行二分。先测量，再修复。

<!-- source: vendor/mattpocock-skills/skills/engineering/diagnosing-bugs/SKILL.md:108-122 -->

## 阶段 5——修复并编写回归测试

在修复**之前**编写回归测试，但前提是存在一个**正确 seam**。

正确 seam 是测试能够按照 bug 在调用位置出现的方式执行**真实 bug 模式**的位置。如果唯一可用的 seam 太 shallow，例如 bug 需要多个调用方却只能编写单调用方测试，或单元测试无法复制触发 bug 的调用链，那么在该 seam 编写回归测试会带来虚假的信心。

**如果不存在正确 seam，这本身就是一项发现。** 记录它。代码库架构正在阻止你锁定该 bug。为下一个阶段标记这一点。

如果存在正确 seam：

1. 把最小复现转成该 seam 上的失败测试。
2. 观察测试失败。
3. 应用修复。
4. 观察测试通过。
5. 针对原始的、未最小化的场景重新运行阶段 1 的反馈循环。

<!-- source: vendor/mattpocock-skills/skills/engineering/diagnosing-bugs/SKILL.md:124-134 -->

## 阶段 6——清理与事后分析

宣布完成前必须满足：

- [ ] 原始复现不再出现问题，再次运行阶段 1 循环
- [ ] 回归测试通过，或者已经记录缺少 seam
- [ ] 已移除全部 `[DEBUG-...]` 插桩，通过 `grep` 查找前缀
- [ ] 已删除一次性 prototype，或把它们移动到明确标记的 debug 位置
- [ ] 已在提交或 PR 消息中说明最终证明正确的假设，使下一位调试者能够获知

**随后询问：什么能够预防这个 bug？** 如果答案涉及架构改动，例如没有良好测试 seam、调用方相互纠缠或隐藏耦合，就把具体情况移交给 `/improve-codebase-architecture` 技能。在修复完成**之后**提出建议，不要提前提出；现在掌握的信息比开始时更多。

## `scripts/hitl-loop.template.sh`

<!-- source: vendor/mattpocock-skills/skills/engineering/diagnosing-bugs/scripts/hitl-loop.template.sh:1-41 -->

```bash
#!/usr/bin/env bash
# Human-in-the-loop 复现循环。
# 复制本文件，编辑下方步骤，然后运行。
# agent 运行脚本；用户按照终端中的提示操作。
#
# 用法：
#   bash hitl-loop.template.sh
#
# 两个 helper：
#   step "<instruction>"          → 显示指令，等待按下 Enter
#   capture VAR "<question>"      → 显示问题，把回答读入 VAR
#
# 最后，捕获的值以 KEY=VALUE 形式打印，供 agent 解析。

set -euo pipefail

step() {
  printf '\n>>> %s\n' "$1"
  read -r -p "    [完成后按 Enter] " _
}

capture() {
  local var="$1" question="$2" answer
  printf '\n>>> %s\n' "$question"
  read -r -p "    > " answer
  printf -v "$var" '%s' "$answer"
}

# --- 在下方编辑 ---------------------------------------------------------

step "打开 http://localhost:3000 上的应用并登录。"

capture ERRORED "点击“Export”按钮。是否抛出错误？(y/n)"

capture ERROR_MSG "粘贴错误消息；如果没有，输入 'none'："

# --- 在上方编辑 ---------------------------------------------------------

printf '\n--- 已捕获 ---\n'
printf 'ERRORED=%s\n' "$ERRORED"
printf 'ERROR_MSG=%s\n' "$ERROR_MSG"
```

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/engineering/diagnosing-bugs/agents/openai.yaml:1-3 -->

```yaml
interface:
  display_name: "Diagnosing Bugs"
  short_description: "诊断困难 bug 和回归"
```
