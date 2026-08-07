# `diagnosing-bugs` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| feedback loop | 反馈循环 | 标准中文译名 |
| tight | 紧密 | 表达快速、明确、确定的循环质量 |
| red、green、red-capable | 变红、变绿、能够变红 | 保留测试信号语义 |
| harness | `harness` | 不与测试框架或宿主混同 |
| instrumentation | `instrumentation` | 不把诊断观测手段缩成普通日志 |
| hypothesis、prediction、probe | 假设、预测、`probe` | 前两者有标准中文，probe 保留诊断动作名 |
| seam、shallow | `seam`、`shallow` | 与 codebase-design 词汇一致 |
| finding | `finding` | 与审查和诊断产出术语一致 |
| regression test | 回归测试 | 标准中文译名 |
| post-mortem | 事后分析 | 标准中文译名 |
| flaky、flake | `flaky`、`flake` | 不与一般随机性混同 |
| HITL、AFK | `HITL`、`AFK` | 行业缩写 |

## 逐行完整性检查

空行只承担 Markdown 或 Shell 分隔，不包含待翻译文字。下表逐一登记其他每一行。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | `name: diagnosing-bugs` 字面量已保留 |
| `SKILL.md:3` | 困难 bug、性能回归、diagnose、debug 和 broken、throwing、failing、slow 五类报告均已保留 |
| `SKILL.md:4` | YAML 结束分隔符已保留 |
| `SKILL.md:6` | `Diagnosing Bugs` 标题已保留 |
| `SKILL.md:8` | 困难 bug 纪律和只有明确理由才跳阶段均已保留 |
| `SKILL.md:10` | 探索时读取可选 CONTEXT、建立相关 module 心智模型和检查相关 ADR 均已保留 |
| `SKILL.md:12` | 阶段 1 建立反馈循环已保留 |
| `SKILL.md:14` | 反馈循环就是技能本体、其余机械、紧密通过失败信号、本 bug 变红、必能找原因、三类动作消费信号和无信号盯代码无效均已保留 |
| `SKILL.md:16` | 投入不成比例的精力，以及 aggressive、creative、refuse to give up 三项强调均已保留 |
| `SKILL.md:18` | 构建方法和大致尝试顺序已保留 |
| `SKILL.md:20` | 触及 bug 的 seam、失败测试和三类测试均已保留 |
| `SKILL.md:21` | 运行中开发服务器上的 Curl 或 HTTP 脚本已保留 |
| `SKILL.md:22` | CLI、fixture input、stdout 与已知正确 snapshot diff 均已保留 |
| `SKILL.md:23` | headless 浏览器、两个工具、驱动 UI 和三个断言面均已保留 |
| `SKILL.md:24` | 重放 trace、三类真实捕获物、保存磁盘和隔离重放代码路径均已保留 |
| `SKILL.md:25` | 一次性 harness、最小系统子集、两个例子和单函数调用执行 bug 路径均已保留 |
| `SKILL.md:26` | property 或 fuzz、偶发错误输出、1000 个随机输入和寻找失败模式均已保留 |
| `SKILL.md:27` | 二分 harness、两个已知状态、三类状态、自动循环形状和 git bisect run 均已保留 |
| `SKILL.md:28` | 差异循环、同输入、旧新 version 或两套 config 和输出 diff 均已保留 |
| `SKILL.md:29` | HITL Bash 是最后手段、人类点击、模板驱动人、结构化循环和捕获输出返回均已保留 |
| `SKILL.md:31` | 正确反馈循环代表 bug 已修复 90% 已保留 |
| `SKILL.md:33` | 收紧循环标题已保留 |
| `SKILL.md:35` | 把循环视为产品、已有循环后收紧均已保留 |
| `SKILL.md:37` | 提速问题和缓存、跳过初始化、缩范围三个例子均已保留 |
| `SKILL.md:38` | 信号更明确、断言具体症状和不只检查未崩溃均已保留 |
| `SKILL.md:39` | 确定性问题和固定时间、RNG seed、filesystem、network 四项均已保留 |
| `SKILL.md:41` | 30 秒 flaky 与 2 秒确定循环对比和调试超级能力均已保留 |
| `SKILL.md:43` | 非确定性 bug 标题已保留 |
| `SKILL.md:45` | 目标是提高复现率而非干净复现、五种增率手段和 50% 与 1% 对比均已保留 |
| `SKILL.md:47` | 确实无法建立循环的标题已保留 |
| `SKILL.md:49` | 停止并说明、列出尝试、环境访问、四类捕获产物、临时 production instrumentation 许可和禁止无循环假设均已保留 |
| `SKILL.md:51` | 紧密且会变红的完成判据标题已保留 |
| `SKILL.md:53` | 紧密、red-capable、一条命令、三种命令例子、至少已运行一次、粘贴调用与输出均已保留 |
| `SKILL.md:55` | red-capable、真实 bug 路径、用户准确症状、当前变红修后变绿、非仅无错误和捕获具体 bug 均已保留 |
| `SKILL.md:56` | 每次相同结论和 flaky bug 固定高复现率均已保留 |
| `SKILL.md:57` | 秒而非分钟的快速判据已保留 |
| `SKILL.md:58` | agent 无人值守运行和 human 只能经 HITL 模板参与均已保留 |
| `SKILL.md:60` | 命令前建立理论必须停止、直接假设是本技能防止的失败和无 red-capable 命令不得进阶段 2 均已保留 |
| `SKILL.md:62` | 阶段 2 复现与最小化已保留 |
| `SKILL.md:64` | 运行循环、观察变红和 bug 出现均已保留 |
| `SKILL.md:66` | 确认清单引导已保留 |
| `SKILL.md:68` | 必须是用户所述失败而非附近失败，以及认错 bug 导致错修均已保留 |
| `SKILL.md:69` | 多次可复现和非确定性 bug 的足够高复现率均已保留 |
| `SKILL.md:70` | 捕获准确症状、三类例子和供后续验证实际解决均已保留 |
| `SKILL.md:72` | 最小化标题已保留 |
| `SKILL.md:74` | 红后缩到最小红场景、五类削减项、每次一项、每次重跑和只保留不可缺少内容均已保留 |
| `SKILL.md:76` | 最小复现缩小阶段 3 假设空间、减少活动部分和成为阶段 5 回归测试均已保留 |
| `SKILL.md:78` | 每个剩余元素不可缺少和移除任一会变绿的完成判据均已保留 |
| `SKILL.md:80` | 必须同时复现和最小化后才继续已保留 |
| `SKILL.md:82` | 阶段 3 提出假设已保留 |
| `SKILL.md:84` | 测试前产生 3 至 5 项排序假设和单假设锚定风险均已保留 |
| `SKILL.md:86` | 每项假设可证伪并说明预测已保留 |
| `SKILL.md:88` | If X、改变 Y 消失、改变 Z 加重的格式已保留 |
| `SKILL.md:90` | 无法说明预测就是凭感觉，需丢弃或明确均已保留 |
| `SKILL.md:92` | 测试前展示排序、用户领域知识和已排除信息、部署示例、低成本高收益、不阻塞和 AFK 时继续均已保留 |
| `SKILL.md:94` | 阶段 4 Instrumentation 已保留 |
| `SKILL.md:96` | 每个 probe 对应具体预测和每次只改一个变量均已保留 |
| `SKILL.md:98` | 工具优先顺序引导已保留 |
| `SKILL.md:100` | 环境支持时 debugger 或 REPL 优先和一个 breakpoint 胜过十 log 均已保留 |
| `SKILL.md:101` | 在区分假设的边界增加定向 log 已保留 |
| `SKILL.md:102` | 禁止记录一切再 grep 已保留 |
| `SKILL.md:104` | 每条 debug log 唯一 prefix、示例、一次 grep 清理和 tagged 死 untaged 留均已保留 |
| `SKILL.md:106` | 性能回归通常不用 log、四类 baseline measurement、随后二分和先测后修均已保留 |
| `SKILL.md:108` | 阶段 5 修复与回归测试已保留 |
| `SKILL.md:110` | 修前测试和必须存在正确 seam 的条件均已保留 |
| `SKILL.md:112` | 正确 seam 的真实 bug 模式与调用位置定义、太 shallow 的两个例子和虚假信心均已保留 |
| `SKILL.md:114` | 无正确 seam 本身是 finding、记录、架构阻止锁定 bug 和为下一阶段标记均已保留 |
| `SKILL.md:116` | 存在正确 seam 时的步骤引导已保留 |
| `SKILL.md:118` | 最小复现转成 seam 上失败测试已保留 |
| `SKILL.md:119` | 观察失败已保留 |
| `SKILL.md:120` | 应用修复已保留 |
| `SKILL.md:121` | 观察通过已保留 |
| `SKILL.md:122` | 对原始未最小化场景重跑阶段 1 循环已保留 |
| `SKILL.md:124` | 阶段 6 清理与事后分析已保留 |
| `SKILL.md:126` | 宣布完成前必需清单已保留 |
| `SKILL.md:128` | 重跑阶段 1 后原始复现不再出现已保留 |
| `SKILL.md:129` | 回归测试通过或记录缺少 seam 已保留 |
| `SKILL.md:130` | grep prefix 并移除全部 DEBUG instrumentation 已保留 |
| `SKILL.md:131` | 删除一次性 prototype 或移到明确 debug 位置已保留 |
| `SKILL.md:132` | 正确假设写入 commit 或 PR message 供下位调试者学习已保留 |
| `SKILL.md:134` | 预防问题、三类架构答案、带细节移交架构改进、修后而非修前建议和信息增量理由均已保留 |
| `scripts/hitl-loop.template.sh:1` | Bash shebang 已保留 |
| `scripts/hitl-loop.template.sh:2` | Human-in-the-loop 复现循环注释已翻译 |
| `scripts/hitl-loop.template.sh:3` | 复制、编辑步骤和运行三项说明已翻译 |
| `scripts/hitl-loop.template.sh:4` | agent 运行、用户按 terminal 提示操作的分工已翻译 |
| `scripts/hitl-loop.template.sh:5` | 注释分隔行已保留 |
| `scripts/hitl-loop.template.sh:6` | Usage 注释已翻译 |
| `scripts/hitl-loop.template.sh:7` | Bash 调用字面量已保留 |
| `scripts/hitl-loop.template.sh:8` | 注释分隔行已保留 |
| `scripts/hitl-loop.template.sh:9` | 两个 helper 引导已翻译 |
| `scripts/hitl-loop.template.sh:10` | step 调用形状、显示 instruction 和等待 Enter 均已保留 |
| `scripts/hitl-loop.template.sh:11` | capture 调用形状、显示 question 和读入 VAR 均已保留 |
| `scripts/hitl-loop.template.sh:12` | 注释分隔行已保留 |
| `scripts/hitl-loop.template.sh:13` | 最后输出 KEY=VALUE 供 agent 解析已翻译 |
| `scripts/hitl-loop.template.sh:15` | `set -euo pipefail` 已保留 |
| `scripts/hitl-loop.template.sh:17` | `step()` 起始已保留 |
| `scripts/hitl-loop.template.sh:18` | instruction 输出命令已保留 |
| `scripts/hitl-loop.template.sh:19` | Enter 提示已翻译，read 逻辑已保留 |
| `scripts/hitl-loop.template.sh:20` | `step()` 结束已保留 |
| `scripts/hitl-loop.template.sh:22` | `capture()` 起始已保留 |
| `scripts/hitl-loop.template.sh:23` | 三个 local 变量和参数赋值已保留 |
| `scripts/hitl-loop.template.sh:24` | question 输出命令已保留 |
| `scripts/hitl-loop.template.sh:25` | answer 输入提示和 read 逻辑已保留 |
| `scripts/hitl-loop.template.sh:26` | 通过 printf 写入目标变量已保留 |
| `scripts/hitl-loop.template.sh:27` | `capture()` 结束已保留 |
| `scripts/hitl-loop.template.sh:29` | 下方可编辑区域注释已翻译 |
| `scripts/hitl-loop.template.sh:31` | 打开本地应用和登录提示已翻译，URL 已保留 |
| `scripts/hitl-loop.template.sh:33` | ERRORED 变量、Export 按钮、错误询问和 y/n 均已保留 |
| `scripts/hitl-loop.template.sh:35` | ERROR_MSG 变量、粘贴错误和 none fallback 均已保留 |
| `scripts/hitl-loop.template.sh:37` | 上方可编辑区域注释已翻译 |
| `scripts/hitl-loop.template.sh:39` | Captured 标题已翻译，printf 结构已保留 |
| `scripts/hitl-loop.template.sh:40` | ERRORED 的 KEY=VALUE 输出已保留 |
| `scripts/hitl-loop.template.sh:41` | ERROR_MSG 的 KEY=VALUE 输出已保留 |
| `agents/openai.yaml:1` | `interface` 字段已保留 |
| `agents/openai.yaml:2` | `display_name: "Diagnosing Bugs"` 已保留 |
| `agents/openai.yaml:3` | 困难 bug 和 regression 均已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。三个上游文件的每个非空行，包括 Bash 模板，都有对应译文和独立检查记录 |
| 增写 | 无。没有加入 MMW 的角色、tracker、worktree、验证或架构接线 |
| 曲解 | 无。必须先有能够变红的紧密循环、再复现最小化、再排序假设、最后修复的阶段顺序保持原样 |
| 术语漂移 | 无。反馈循环、变红、变绿、instrumentation、seam、finding 和回归测试使用一致 |
