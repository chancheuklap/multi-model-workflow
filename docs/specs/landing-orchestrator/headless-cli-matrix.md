# 五 CLI 无头调用矩阵（本机取证记录）

> landing-orchestrator spec 的附件。2026-08-24 在本机逐个跑 `--help`/`--version` 取证（未发起模型调用）。版本：claude 2.1.241、cursor-agent 2026.08.11、codex 0.149.1、grok 1.0.5、pi 0.84.2。实现前如 CLI 升级，重跑 help 复核。

| | 无头一次性 | 指定模型 | 思考强度 | 工作目录 | 注入系统提示/规则 | 结构化输出 |
|---|---|---|---|---|---|---|
| **claude** | `-p, --print` | `--model`（别名 fable/opus/sonnet） | `--effort low…max` | **无参数**，靠 `cd` | `--system-prompt[-file]` / `--append-system-prompt[-file]`（`-file` 变体未列入 help 但实测存在） | `--output-format text\|json\|stream-json`；`--json-schema` |
| **cursor-agent** | `-p, --print` | `--model`；`--list-models` 可发现 | 写进模型串 `model[effort=high]` | `--workspace` | **无单次注入参数**（rules 是交互生成的文件） | `--output-format`，`--stream-partial-output` |
| **codex** | 子命令 `exec`（prompt 可走 stdin） | `-m, --model`（无发现命令） | **无专用参数**，仅 `-c key=value` 覆盖 | `-C, --cd` | **无**；`.rules` 是磁盘文件（`--ignore-rules` 可关） | `--json`（JSONL 事件流）；`--output-schema <FILE>`；`-o` 落终局消息 |
| **grok** | `-p, --single`；`--prompt-file` | `-m`；子命令 `models` 可发现 | `--reasoning-effort`（alias `--effort`） | `--cwd` | `--rules`（追加，alias `--append-system-prompt`）/ `--system-prompt-override` / `--verbatim` | `--output-format plain\|json\|streaming-json\|streaming-messages-json`；`--json-schema`；`--max-turns` |
| **pi** | `-p, --print`（`@file` 附文件） | `--model provider/id[:thinking]`；`--list-models` | `--thinking off…max` | **无参数**，靠 `cd` | `--system-prompt` / `--append-system-prompt`（文本或文件路径通吃）；`--skill` | `--mode text\|json\|rpc`（注意不是 `--output-format`） |

## 编排实现要点

1. 只有 codex（`-C`）与 grok（`--cwd`）免 `cd`；claude / pi 由派发方 `cd` 或 `subprocess(cwd=)`；cursor 用 `--workspace`。
2. 单次注入口只有 claude / grok / pi 三家；cursor 的纪律走简报正文；codex 的 brief 全走 prompt 正文（`exec` 吃 stdin）。
3. 强度四形态：独立 flag（claude/grok/pi）、模型串内联（cursor）、无专用面（codex）。
4. **退出码不可信**：五家 help 全文均无退出码承诺——成败解析结构化输出（ponytail benchmark 先例：只解析 JSON、stdout 重定向到文件防管道挂死；skills 若是插件形态须 `--plugin-dir` 激活，`--append-system-prompt` 塞正文不会激活）。
5. 会话续用：claude `--resume/--fork-session/--bg`、codex `exec resume --last`、cursor `--resume`、grok `-c/--resume`、pi `--session-id`。
6. 权限参数按 MMW 授权约定配置，不照抄参考项目的全量绕过。

交叉核对来源：swarm-forge 启动器四家命令行（https://github.com/unclebob/swarm-forge `swarmforge/scripts/swarmforge.bb:460-480` @ 7c1d1c9）与 ponytail benchmark 的 claude 无头调用（https://github.com/DietrichGebert/ponytail `benchmarks/agentic/run.py:304-330` @ 2ed6c52），两者与本机 help 逐条一致。
