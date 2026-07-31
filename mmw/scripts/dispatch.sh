#!/usr/bin/env bash
# 适配层。只有模型专用宿主（Claude Code、Codex CLI）需要它：这类宿主派不了别家模型的
# 子代理，得起无头进程。多模型宿主（Cursor、pi、Droid）在角色文件里直接指定模型，不用这个。
#
# 它只做机器比模型准的事：读角色的参数、把命令行一次拼对、抓会话号、按角色声明的边界核越界。
# 它不组装提示词、不建工作树、不判该派谁、不生成派发指南——那些是主线程的判断。
#
# 用法：
#   dispatch.sh run    --role <角色名> --cwd <目录> --prompt <文件> [--add-dir <目录>]
#   dispatch.sh resume --role <角色名> --cwd <目录> --session <会话号> --prompt <文件>
#   dispatch.sh check  --role <角色名> --cwd <目录> --since <提交>
#
# 角色参数一律从 ../roles/<角色名>.md 的头部读：model、effort、sandbox、
# allow-paths（白名单，只准碰这些）或 deny-paths（黑名单，禁碰这些）。
# 角色名在 roles/ 下找不到，或缺 sandbox，直接非零退出——不猜默认值。
#
# run 与 resume 都回两行机器可读的头（会话号、退出码），再回被派者的最后一条消息。
# 后台起由调用方负责：审一轮和落地一份计划都常超前台超时上限。

set -euo pipefail

echo "ERROR: 第三层接线时实现。" >&2
exit 2

# ## 施工单
#
# - **来源**：`plugin/scripts/worker.sh` 的 `run_codex`、`run_codex_plan`、`_extract_codex_session`、
#   `check_docs_boundary`、`check_plan_boundary`、`preflight_skill`、`preflight_doc`；
#   `plugin/scripts/review.sh` 的无头派发命令行
# - **保留**：抓会话号前先剥 ANSI 色码（旧脚本踩过：色码顶开行首锚点，会话号抓空，
#   续接记账整条丢失）；恢复会话要把围栏与模型档整套重钉，恢复不继承；
#   越界检查两个方向（写码的禁碰文档、写计划的只准碰计划与切片）；
#   开工前预检点名的技能已装、传入的文档存在，缺装备当场报错不让开工后才发现；
#   并行派多份计划时会话记账各自分开，同一个工作树里互不覆盖
# - **删除**：提示词正文组装（主线程给，脚本只透传）；派发指南文本生成（253 行里的大头，
#   那是提示词工程封进 shell）；审者分档矩阵；建工作树；状态目录管理；
#   原型状态校验；检索候选快照管道；三十九字段任务档案的读写
