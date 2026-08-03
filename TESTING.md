# TESTING.md(仓库薄层)

> 完整测试写作权威随各宿主发布（人读：`plugin/skills/worktree-build/references/tests.md`）。各执行角色按阶段读取这份权威；仓库特有规则通过 `AGENTS.md` / `CLAUDE.md` 项目指令链进入，本仓库根 `AGENTS.md` 指向本文。本文只写本仓库事实，不重复或删减通用权威。

## 目录分层

| 层 | 位置 | 测什么 |
| --- | --- | --- |
| 脚本行为 | `plugin/scripts/tests/test_*.sh` | mmw 各子脚本:跑真命令,断 stdout / 退出码 / 状态文件(`task.json`、`loop-state.json`、`review-brief.md`) |
| 构建注入 | `plugin/build/tests/test_build.sh` | fragments 单源注入:--apply 传播、--check 抓 DRIFT、锚点结构 |
| release 合同 | `plugin/scripts/tests/test_release_*.sh` + `test_release_*.py` | 出包子系统:stage 推进、远端构建合同、脚本装配 |
| Droid 宿主 | `droid-plugin/**` 同构目录 | 同一套行为，宿主路径、hook 事件和执行后端不同 |
| pi 宿主 | `pi-plugin/**` 同构目录 | 同一套行为，状态目录、动态 workflow 和 pi-subagents 派发不同 |
| Cursor 宿主 | `cursor-plugin/**` 同构目录 | 同一套行为，状态目录、Task 派发和 `mmw task adopt` 不同 |

## 断什么、不断什么(本仓库特有边界)

- skill / reference / command 的 prose 就是行为面:断**结构**(锚点在、注入频次、段落顺序)与**短语义键**(如「独立任务边界」),不逐字锁整句——润色不该红。
- hook / CLI 的 stdout 是外部可观察面,可断语义键;不 grep 脚本源码文本。
- 状态文件字段走 `jq` 断具体值,不做字段全集镜像。

## 外部接缝(允许打桩的边界)

- `codex` 与 `droid` CLI：worker 测试用 PATH 前插的 stub bin。
- ssh / schtasks 远端（release）：`fixtures/fake-remote/` 的假构建机。它维护一棵目录树当远端文件系统、一份登记表当 Task Scheduler，**不记录命令文本**——断言对象是这两样的最终状态，不是引擎发出了什么命令。构建结果由 `FAKE_BUILD_OUTCOME` 等环境变量摆布（成功、失败、卡死、退出码损坏、启动失败、清理失败）。
- 宿主会话内的 Agent / subagent：不在 shell 测试中伪造模型判断，测到 prompt、brief 和派发账本生成为止。

## 没有自动化覆盖的行为（改动它们必须在构建机上实测）

下面这几条要一台 Windows 构建机才验得了，Mac 上跑不了，**也不要写假测试冒充覆盖**——假绿比没测更坏，它让人以为有保障。改动这些代码路径时，靠代码审查加构建机实跑，不靠 CI。

| 行为 | 为什么这里验不了 |
| --- | --- |
| 脱附计划任务会话里日志到底落不落地（管道不落地、原生重定向才落地） | 要真的 Task Scheduler 脱附会话 |
| PowerShell 5.1 原生重定向写 UTF-16LE 之后转 UTF-8 是否成功 | 开发机没有 PowerShell，且 PS Core 的编码行为跟 5.1 不同 |
| 安装器 include 路径是否越过 Windows 路径长度上限 | 上限是 Windows 特有的 |
| 上传的 `run-release.ps1` 内容对不对 | 同上两条。测试只断它被上传了、非空 |

假构建机能覆盖的是这些的**外围**：文件确实上传了、源码确实解压且内容一致、旧产物确实被清、任务确实被清理、危险路径确实被拒。

## 权威源指针

- 阶段、闸位和结论词：各宿主的 `state-schema/routes.json`。
- 共用片段：各宿主的 `build/fragments/*`（改后必须 `--apply` 再 `--check`）。
- 版本号：Claude Code 同步 plugin manifest 与 marketplace；Droid 同步 plugin manifest 与 marketplace；pi 以 `pi-plugin/package.json` 为准；Cursor 同步 `cursor-plugin/.cursor-plugin/plugin.json` 与根 `.cursor-plugin/marketplace.json`。

## 门控

```bash
for host in plugin droid-plugin pi-plugin cursor-plugin; do
  bash "$host/build/build.sh" --check || exit 1
  bash "$host/build/tests/test_build.sh" || exit 1
  for test_file in "$host"/scripts/tests/test_*.sh; do
    bash "$test_file" || exit 1
  done
done
python3 pi-plugin/scripts/render_agent_prompts.py --check
bash pi-plugin/workflows/install-workflows.sh --check
```

已知慢测试:`test_release_flow.sh` 约 90 秒(远端构建墙钟轮询用例),不是挂起。
