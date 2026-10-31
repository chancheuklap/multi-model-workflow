---
date: 2026-10-31
amends: [0018, 0024]
---

# 原生工具也收进 runner adapter，共享工作流只等同步回执

MMW 同时支持命令行 runner 和只能由宿主原生工具控制的 runner。工作树、分支、角色、票据事件、relay 和 watchdog 仍由原有协议管理。adapter 决定如何完成 start、send、state、liveness、stop 和 self，独立会话保持独立上下文。共享技能和 playbook 不写任何 runner 的原生工具名或调用参数。

## 执行与能力

每个 adapter 的 `MMW_RUNNER` 声明分别给出模型目录来源、host 启动能力，以及可选的 tool executor。模型目录相同不代表两个 runner 能启动相同的 host。配置校验与任务板都读取这份声明。

tool executor 由当前调用会话在自身工具运行环境中执行，没有新模型或调度器。共享 shell 命令通过继承的请求与响应描述符调用原生操作，拿到真实回执后才继续登记或清理。executor 由调用方所在的 runner 决定，启动目标仍由既有配置决定。

Codex App 的原生调用位于它的 adapter 中。后台投递通过公共持久队列，队列接受属于既有的未确认送达，仍需 relay ack。后台状态来自宿主事件和进程启动身份。其他 app-server 的内存状态不能证明桌面会话停止。App 关闭或状态来源不明时回答 unknown。

App adapter 先通过公共接口在给定目录准备独立聊天，再用当前会话的原生工具发送首条任务。项目归类不是启动条件，标题设置失败只报告诊断。首条任务携带本次技能目录和 MMW 命令环境，子会话沿用发起方的运行版本与配置；App 不必复制终端的环境继承方式。子 agent 的模型配置继续独立于派发 session 所选的 runner。

## Considered Options

- **在共享提示词中让 agent 逐次调用 App 工具。** 否决。具体操作散出 adapter，其他宿主无法复用，也不能保证 shell 拿到确认的会话身份。
- **再创建一个 App coordinator 代理原 coordinator。** 否决。增加会话、状态和调度责任，当前会话已有原生工具可用。
- **把独立会话改成原生 subagent。** 否决。改变生命周期、上下文隔离和可恢复身份，不能保留原工作流的结果。
- **为了 shell 形式继续寻找私有 MCP 授权绕行。** 否决。真实 App 的原生创建、查询和停止已得到验证，实现方法服从能力边界。

## Consequences

- ADR 0018 的 runner 知识单一边界、工作树归共享协议和失败不换 runner 保留。同步桥取得真实身份后才让共享协议继续，区别于打印待执行对象后让模型决定是否执行。
- ADR 0024 的唯一配置 `models.json` 和 adapter 附加操作边界保留。模型目录与启动能力分开声明。
- shell runner 没有 executor，继续走原调用路径。App executor 使用已有宿主工具环境，不引入 Node 服务、第二套票据状态或定时 agent。
- 运行时安装与发布仍受现有授权和冻结版本边界约束。
