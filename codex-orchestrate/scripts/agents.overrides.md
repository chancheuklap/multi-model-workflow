# scripts 规则

- Scripts 承担 state、dispatch、review lane、install、verification 和 cleanup 的可执行 runtime 行为。
- Scripts 必须能从 plugin install path 运行，并优先使用 `PLUGIN_ROOT` / `PLUGIN_DATA`。
- 除非测试通过 `STATE_BASE` 覆盖，正式 state 必须写入 `.codex/multi-model-workflow`。
- Review wrapper 只走 native Codex Review；baseline review 必须通过 `review-lane.sh` 模型路由。
- 作为 hook helper 被调用的脚本必须容忍未知 hook payload shape；只对已识别的命令和状态执行副作用。
