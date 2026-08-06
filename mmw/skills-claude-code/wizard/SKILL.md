---
name: wizard
description: 为只能由用户完成的多步流程生成 Bash wizard。用于第三方服务配置、凭证或 CI secret、一次性迁移或 cutover。
---

# Wizard

Wizard 是一个 Bash 脚本。它逐步带用户完成必须由人操作的流程：打开 URL，说明点击和复制位置，读取用户输入，把值写入 `.env` 或 GitHub secrets，在不可逆动作前确认，并显示剩余进度。

[template.sh](template.sh) 已经实现统一交互：阶段进度、预计剩余时间、跨平台打开 URL、隐藏 secret 输入、幂等 `.env` 写入、GitHub secret 和 variable 写入，以及结束总结。你的职责是限定流程并编写各个 `stage`。`STAGES` 标记上方是固定 library，不修改。

Wizard 默认是临时产物，保存在 scratch 或临时 `scripts/` 路径。只有用户明确要求可重复的仓库设置入口时，才提交进仓库。

## 1. 限定流程

先读取仓库，不冷启动提问。

设置类任务读取 `.env`、`.env.example`、`.env.*`、README、`docker-compose*`、框架配置和 `.github/workflows/*`。CI 中每个 `secrets.*` 和 `vars.*` 引用都要追到来源。

迁移或切换类任务读取当前状态、目标状态和两者之间的不可逆动作。

向用户展示有序步骤，以及每步产生的值。每个值写清：

- 用户从哪里取得。
- 写到 `.env`、GitHub secret、两边，还是不持久化。
- 它是 secret 还是公开值。

用户确认步骤、顺序和值落点后，才能生成脚本。

完成判据：每个步骤已有名称和顺序；每个值都有来源、落点和 secret 属性。

## 2. 写清每步路径

每个步骤都写成陌生用户可以执行的精确路径：打开哪个 URL、点击哪里、值在哪里显示、填入哪个变量。

不知道当前 UI 或准确命令时，读取官方文档或询问用户。不能编造可能不存在的界面和步骤。

完成判据：每个步骤都有可执行说明和明确的输入输出。

## 3. 生成 wizard

以 [template.sh](template.sh) 为模板，在目标路径生成脚本。保留 `STAGES` 标记上方的 library，只替换示例步骤。

按依赖顺序写一个步骤一个 `stage`。使用现有 helper：`stage`、`say`、`step`、`open_url`、`ask`、`ask_secret`、`write_env`、`set_secret`、`set_var`、`pause` 和 `confirm`。设置诚实的 `TOTAL_STAGES` 和 `TOTAL_MINUTES`。

打开 URL 后再索取值。Secret 使用 `ask_secret`。需要持久化的值使用 `write_env`。只有 CI 实际消费的值才使用 `set_secret`。不可逆动作前必须使用 `confirm`。

一个 `stage` 只完成一个聚焦任务。`stage` 会清屏，当前步骤所需内容必须留在同一屏。

## 4. 验证并交给用户

- 运行 `bash -n <脚本>`。
- ShellCheck 可用时运行 ShellCheck。
- 运行 `chmod +x <脚本>`。
- 静态追踪每个值，确认来源和落点与第 1 步一致。
- 每个 `set_secret` 名称必须与 CI 的 `secrets.*` 引用完全一致。

不要替用户端到端运行脚本。它会打开浏览器并等待人工输入。把运行命令交给用户。

用户要求把 wizard 作为重复设置入口保存在仓库时，提交脚本并从 README 链接。临时 wizard 在任务完成后按用户决定清理。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 脚本通过静态验证 | **停**：给用户运行命令、脚本路径、会写入的位置和不可逆步骤 |
| 用户修改步骤、顺序或值落点 | **自己继续**：回第 1 步重新确认，再更新脚本 |
| 当前 UI 或命令无法从一手来源确认 | **停**：点名未知步骤和所需信息，不生成猜测版本 |
