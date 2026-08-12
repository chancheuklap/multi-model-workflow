---
name: wizard
description: 为只能由用户完成的多步流程生成 Bash wizard。用于第三方服务配置、凭证或 CI secret、一次性迁移或 cutover。agent 自己跑得了的步骤不要调用本技能。
---

# Wizard

Wizard 是一个 Bash 脚本。它逐步带用户完成必须由人操作的流程：打开 URL，说明点击和复制位置，读取用户输入，把值写入 `.env` 或 GitHub secrets，在不可逆动作前确认，并显示剩余进度。

**它针对的是两头都繁琐的流程**：用户每次手动做一遍很繁琐，每次向 agent 重新解释一遍同样繁琐。脚本一旦存在，这段流程就不必再解释第二次。只发生一次、以后不会再来的人工步骤，做成 wizard 不回本。

[template.sh](template.sh) 已经实现统一交互：逐阶段进度、跨平台打开 URL、隐藏 secret 输入、幂等 `.env` 写入、GitHub secret 和 variable 写入，以及结束总结。

你的职责是限定流程并编写各个 `stage`。`STAGES` 标记上方是固定 library，一个字都不改——**每一份 wizard 的这一段完全相同，一致性本身就是目的**，用户第二次跑另一份 wizard 时不用重新认界面。

Wizard 默认是临时产物，固定保存在当前任务的 Git 忽略 scratch。流程完成或放弃后删除。只有用户明确要求可重复的仓库设置入口时，才写入并提交仓库的正式路径。

## 1. 限定流程

先读取仓库，不冷启动提问。

设置类任务读取 `.env`、`.env.example`、`.env.*`、README、`docker-compose*`、框架配置和 `.github/workflows/*`。CI 中每个 `secrets.*` 和 `vars.*` 引用都要追到来源。

迁移或切换类任务读取当前状态、目标状态和两者之间的不可逆动作。

向用户展示有序步骤，以及每步产生的值。每个值写清：

- 用户从哪里取得。
- 写到 `.env`、GitHub secret、两边，还是哪儿都不写——有些步骤只有动作，不产生值。
- 它是 secret 还是公开值。

用户确认步骤、顺序和值落点后，才能生成脚本。

完成判据：每个步骤已有名称和顺序；每个值都有来源、落点和 secret 属性。

## 2. 写清每步路径

每个步骤都写成陌生用户可以执行的精确路径：打开哪个 URL、点击哪里、值在哪里显示、填入哪个变量。

不知道当前 UI 或准确命令时，读取官方文档或询问用户。不能编造可能不存在的界面和步骤。

完成判据：每个步骤都有可执行说明和明确的输入输出。

## 3. 生成 wizard

先运行 `mmw task state`。第一个词是 `bound` 时，运行 `mmw task name` 取工作名。

输出是 `detached` 时，先分别确定任务分支名和工作名。运行 `mmw task bind <任务分支名> "<用户原话>" --name <工作名> [--from <父分支或基点 SHA>]`。

输出是 `local` 时，先分别确定任务分支名和工作名。禁止 `mmw task new`。宿主已把你放在树上则运行 `mmw task bind <任务分支名> "<用户原话>" --name <工作名> [--from <父分支或基点 SHA>]`。还没有树时请用户用宿主建树，新会话已经在树上后再 bind。

输出是 `outside` 时，向用户索取目标仓库路径。拿到路径后进入该仓库，再重新运行 `mmw task state`。

两种建树动作之后都重新运行 `mmw task state`。第一个词确认是 `bound` 后，运行 `mmw task name` 取工作名。

以 [template.sh](template.sh) 为模板。取这次流程的 `<流程>`。它不是任务分支名。一个任务可以运行多次 wizard。运行下面的完整命令。Wayfinder decision ticket 需要范围段时加入 `--issue <编号>`：

```bash
mmw artifact path scratch [--issue <编号>] --sub wizard/<流程>.sh
```

在输出文件生成 wizard。保留 `STAGES` 标记上方的 library。只替换示例步骤。

用户明确要求把 wizard 变成可重复的仓库入口时，改用用户确认的正式路径，不在 scratch 保留第二份。

按依赖顺序写一个步骤一个 `stage`：

| 需要 | helper |
| --- | --- |
| 开始一个步骤 | `stage` |
| 显示说明 | `say`、`step` |
| 打开页面 | `open_url` |
| 读取公开值 | `ask` |
| 读取 secret | `ask_secret` |
| 写入 `.env` | `write_env` |
| 写入 CI secret 或 variable | `set_secret`、`set_var` |
| 等待或确认 | `pause`、`confirm` |

把 `TOTAL_STAGES` 设成你实际写出的阶段数。打开 URL 后再索取值。Secret 使用 `ask_secret`。需要持久化的值使用 `write_env`。只有 CI 实际消费的值才使用 `set_secret`。不可逆动作前必须使用 `confirm`。

一个 `stage` 只完成一个聚焦任务。`stage` 会清屏，当前步骤所需内容必须留在同一屏。

## 4. 验证并交给用户

- 运行 `bash -n <脚本>`。
- ShellCheck 可用时运行 ShellCheck。
- 运行 `chmod +x <脚本>`。
- 静态追踪每个值，确认来源和落点与第 1 步一致。
- 每个 `set_secret` 名称必须与 CI 的 `secrets.*` 引用完全一致。

不要替用户端到端运行脚本。它会打开浏览器并等待人工输入。把运行命令交给用户。

用户要求把 wizard 作为重复设置入口保存在仓库时，提交脚本并从正式文档链接。临时 wizard 在流程完成或放弃后删除。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 临时脚本通过静态验证 | **停**：给用户运行命令、scratch 脚本路径、会写入的位置和不可逆步骤；等待流程完成或放弃后清理 |
| 用户确认临时流程已经完成或放弃 | **自己继续**：删除当前任务 scratch 中这份 wizard，再报告清理结果 |
| 用户明确要求可重复的仓库入口，脚本通过静态验证 | **停**：确认脚本已写入正式路径，并从正式文档链接 |
| 用户修改步骤、顺序或值落点 | **自己继续**：回第 1 步重新确认，再更新脚本 |
| 当前 UI 或命令无法从一手来源确认 | **停**：点名未知步骤和所需信息，不生成猜测版本 |
