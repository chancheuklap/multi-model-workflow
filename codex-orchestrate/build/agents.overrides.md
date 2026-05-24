# build 规则

- Build template 用来消除 phase skill、reference 和 agent prompt 之间的重复漂移。
- Resolver 输出必须确定性，可被 `build.sh --check` 复核。
- 生成到 Codex runtime 的内容只能使用 Codex host primitive，不引入 Claude 运行时语义。
