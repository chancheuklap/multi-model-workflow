#!/usr/bin/env bash
# 语言工具链：按规则表探测这个仓库该配哪些语言服务器与命令行检查器，并把该有的配置写出来。
#
# 实现分三份，这一层只做转发：探测在 cli/lib/toolchain_detect.py，产出配置在
# cli/lib/toolchain_apply.py，编辑后诊断在 cli/lib/toolchain_check.py。规则表在
# config/toolchain-rules.json，模板在 toolchain/templates/。
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

# 把探测出来缺的语言服务器与检查器装上。默认只列不装，加 --yes 才真装。
mmw_toolchain_install() {
  python3 "$MMW_ROOT/cli/lib/toolchain_install.py" \
    "$(mmw_repo_root)" \
    "$(mmw_toolchain_rules)" \
    "$@"
}

# 按探测结果把配置写进仓库。`mmw init` 会调它，所以换仓库、换电脑不用靠人想起来。
# 谁拥有哪份内容由规则表的 mode 决定，详见 cli/lib/toolchain_apply.py 的文件头。
mmw_toolchain_apply() {
  python3 "$MMW_ROOT/cli/lib/toolchain_apply.py" \
    "$(mmw_repo_root)" \
    "$(mmw_toolchain_rules)" \
    "$MMW_ROOT/toolchain/templates" \
    "$@"
}

# 编辑后的单文件诊断。各宿主的推送通道最终都调到这里：Codex 从 hooks.json 的
# PostToolUse 调，Pi 从扩展的 tool_execution_end 调，Grok 从 Stop hook 调，
# Claude Code 有原生 LSP，也挂同一 hook 补类型以外的检查。
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
