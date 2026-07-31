---
name: mmw-dispatch
description: 你要派 roles/ 里任何一个角色出去干活时读这份。它讲的是本宿主怎么让那些角色跑起来。
user-invocable: false
---

**这份是宿主适配层，换一家宿主整份重写。** 角色是什么在 `roles/`，那六份不动；这里只讲本宿主怎么让它们跑起来。

## 本宿主的限制

Claude Code 只能原生派自家模型的子代理。`roles/` 里模型是 Claude 家的两份走原生子代理，另外四份模型是 GPT，本宿主派不了，只能起无头命令行。

判断规则：看角色的 `model`。是 Claude 家的走原生，不是就走无头。

多模型宿主（Cursor、pi、Droid）不存在这个限制，六份全走原生子代理，那边这份技能会短得多。

## 原生这条路

`reviewer-claude` 与 `scout` 已由插件清单点名注册，直接用派子代理的工具派，模型、思考档、工具白名单由宿主按那两份文件强制执行。

## 无头这条路

`plan-writer`、`executor`、`executor-capable`、`reviewer-gpt` 四份，宿主不注册，由你读那份角色文件、照里面的模型与思考档起命令行。

| 角色 | 沙箱 | 起法 |
| --- | --- | --- |
| `plan-writer`、`executor`、`executor-capable` | `workspace-write` | `codex exec -C <工作树> --sandbox workspace-write --add-dir <主仓库 git 公共目录> -m <模型> -c model_reasoning_effort="<档>"` |
| `reviewer-gpt` | `read-only` | `codex exec -C . --sandbox read-only -m <模型> -c model_reasoning_effort="<档>"` |

提示词走标准输入。放行 git 公共目录是因为不放行的话工作树里跑不了 git。

一律起在后台：审一轮和落地一份计划都常超前台超时上限。

角色的方法论不由你转述——那四份角色的 `skills` 字段点名了要读哪份技能，起之前先确认那份技能已装进无头这一侧的技能根，缺了当场报错，不让工人开工后才发现。

续接追问用同一条命令行加恢复会话，**围栏与模型档必须整套重钉**：恢复不继承原来的沙箱与模型。

## 施工单

- **来源**：`plugin/scripts/worker.sh` 的 `run_codex` / `run_codex_plan` / `dispatch` / `plan-dispatch`、`plugin/scripts/review.sh` 的派发指南
- **保留**：无头进程的沙箱与放行目录；后台起、会话可恢复且恢复要重钉围栏；开工前预检技能已装与文档存在
- **删除**：把这些封成 shell 脚本（含会话记账、日志目录、边界检查三套子命令）；两份并行编排脚本

<!-- 派发细节待填。第三层接线时落定。 -->
