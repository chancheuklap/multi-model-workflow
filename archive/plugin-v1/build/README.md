# Build System

源码模块化 + 运行时组合。`.tmpl` 模板由 `build.sh` 的内联 resolve 逻辑（`resolve_anchor()`）在 build time 组合成 SKILL.md / agent.md 中 agent 读到的最终内容。

## 锚点约定

```markdown
<!-- BEGIN: <anchor-name> -->
...content managed by resolver...
<!-- END: <anchor-name> -->
```

- 锚点由 `build.sh` 识别，`resolve_anchor()` 按 anchor 名生成替换内容
- 锚点不存在的文件会被跳过（不报错），便于渐进式接入
- 支持 variant：`<!-- BEGIN: review-dispatch [variant=execution] -->`

## 命令

```bash
# 检查：生成内容与当前文件是否一致（CI 用）
bash plugin/build/build.sh --check --plugin-dir plugin

# 应用：把生成内容写入文件（原子写入：tmp → rename）
bash plugin/build/build.sh --apply --plugin-dir plugin

# 只跑单个 resolver（调试用）
bash plugin/build/build.sh --apply --plugin-dir plugin --resolver=preamble
```

## 新增锚点步骤

resolve 逻辑已从早期的 `resolvers/*.sh`（每锚点一个脚本）塌缩为 `build.sh` 内
`resolve_anchor()` 的内联 `case "$anchor_name"`，分三类（不再有 `resolvers/` 目录）：

- **Type 1（纯 cat）**：模板整份注入，无 variant。
- **Type 2（文件级 variant）**：按 variant 选 `templates/<name>.<variant>.md.tmpl` 再 cat。
- **Type 3（内联 variant）**：从单一 `.tmpl` 用 sed 抽取 `[variant=X]` 段；voice 子型还在尾部单源追加 `VOICE_FOOTER`。

新增一个锚点：

1. 在 `templates/` 下新建对应 `.md.tmpl`
2. 在 `build.sh` 的 `resolve_anchor()` 里给新 anchor 加一个 `case` 分支（归入上面三类之一）
3. 在目标文件中插入 `<!-- BEGIN: <name> -->` / `<!-- END: <name> -->` 锚点对
4. 运行 `build.sh --apply` 注入内容（`--resolver=<name>` 可只跑该锚点）
5. 在 `tests/` 下新建 `test_<name>.sh` 验证

## macOS 注意事项

构建系统使用 python3 做锚点替换（避免 BSD sed 与 GNU sed 的不兼容问题）。确保 `python3` 在 PATH 中。

## 紧急修复

直接编辑 SKILL.md（立即生效），然后补改 `.tmpl` 源文件 + 重新 `--apply`。等同于编译语言的 hotfix 模型。
