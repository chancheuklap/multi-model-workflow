# 构建系统

源码模块化 + 运行时组合。`.tmpl` 模板和 resolver 在 build time 组合成 SKILL.md / TOML agent 中实际会被 Codex 读取的内容。

## 锚点约定

```markdown
<!-- BEGIN: <anchor-name> -->
...content managed by resolver...
<!-- END: <anchor-name> -->
```

- 锚点由 `build.sh` 识别，resolver 负责生成替换内容
- 锚点不存在的文件会被跳过（不报错），便于渐进式接入
- 支持 variant：`<!-- BEGIN: review-dispatch [variant=execution] -->`

## 命令

```bash
# 检查：生成内容与当前文件是否一致（CI 用）
bash codex-orchestrate/build/build.sh --check --plugin-dir codex-orchestrate

# 应用：把生成内容写入文件（原子写入：tmp → rename）
bash codex-orchestrate/build/build.sh --apply --plugin-dir codex-orchestrate

# 只跑单个 resolver（调试用）
bash codex-orchestrate/build/build.sh --apply --plugin-dir codex-orchestrate --resolver=preamble
```

## 新增 resolver 步骤

1. 在 `resolvers/` 下新建 `<name>.sh`，接收 3 个参数：`TEMPLATE_DIR` / `ANCHOR_NAME` / `VARIANT`
2. 在 `templates/` 下新建对应 `.md.tmpl`
3. 在目标文件中插入 `<!-- BEGIN: <name> -->` / `<!-- END: <name> -->` 锚点对
4. 运行 `build.sh --apply` 注入内容
5. 在 `tests/` 下新建 `test_<name>.sh` 验证

## macOS 注意事项

构建系统使用 python3 做锚点替换（避免 BSD sed 与 GNU sed 的不兼容问题）。确保 `python3` 在 PATH 中。

## 紧急修复

直接编辑 SKILL.md（立即生效），然后补改 `.tmpl` 源文件 + 重新 `--apply`。等同于编译语言的 hotfix 模型。
