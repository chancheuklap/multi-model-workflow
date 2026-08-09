#!/usr/bin/env bash
# 语言工具链：按规则表探测这个仓库该配哪些语言服务器与命令行检查器。
#
# 探测的实现在 cli/lib/toolchain_detect.py，这一层只做转发。规则表在
# config/toolchain-rules.json。
#
# 为什么这值得一条子命令（对照 cli/mmw 顶部的准入判据第 3 条）：语言工具链是宿主机械
# 差异的落点。Claude Code 有原生 LSP 通道，Codex 与 Pi 没有、要靠 hook 加 MCP 桥接同一批
# 语言服务器，Cursor 又是另一套配置文件。四个宿主要拿到同一组能力，探测这一步必须只有
# 一份，否则每个宿主各探一次、结论各不相同。
#
# detect 只读：读 git 跟踪清单、读各工作区的依赖声明、跑 `<bin> --version`。它不写文件，
# 也不装东西。有缺失或版本对不上时退出码是 1，所以它能直接当门禁用。

set -euo pipefail

mmw_toolchain_rules() {
  echo "$MMW_ROOT/config/toolchain-rules.json"
}

mmw_toolchain_detect() {
  python3 "$MMW_ROOT/cli/lib/toolchain_detect.py" \
    --repo "$(mmw_repo_root)" \
    --rules "$(mmw_toolchain_rules)" \
    "$@"
}

# 编辑后的单文件诊断。三个宿主的推送通道最终都调到这里：Codex 从 hooks.json 的
# PostToolUse 调，Pi 从扩展的 tool_execution_end 调，Claude Code 有原生 LSP 不用它。
# 同一个仓库、同一份规则表、同一批检查器，三家看到的诊断因此是同一套。
#
# 有问题时退出码 2：Claude Code 与 Codex 的 hook 合同都把 2 当作"把 stderr 交回给
# agent"。
mmw_toolchain_check() {
  python3 "$MMW_ROOT/cli/lib/toolchain_check.py" \
    --repo "$(mmw_repo_root)" \
    --rules "$(mmw_toolchain_rules)" \
    "$@"
}
