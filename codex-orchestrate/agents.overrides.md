# codex-orchestrate 规则

- 本目录是 Codex 原生编排源码。不要导入、修补或复活旧 repo 根目录 `codex/` 实现。
- `plugin/` 是行为合同蓝本；本目录只做 Codex host primitives、Codex plugin packaging、`.codex/multi-model-workflow` 状态、Codex hook/event 语义的映射。
- runtime 安装后必须能独立运行，所以源码文件要保持自足。
- Hook manifest 固定为 `hooks/hooks.json`；不要在根目录新增重复 manifest。
- 修改子目录合同时，同步更新对应子目录的 `agents.overrides.md`。
