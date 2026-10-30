# 用户级提示词

`shared.md` 是 Claude Code 与 Codex CLI 共用的用户级正文，带不带 mode 都读。它记录读回复的那个人的事实，以及 MMW 步骤之外派去搜索、调研的 subagent 用哪个模型。哪些决定只归主人，在 `principle-never-block-on-the-human` 技能里；工作规矩在 `mmw-mode` 技能里。

`mmw-v4/install.sh` 把两个原生入口都软链接到本次安装的 checkout 的 `prompt/shared.md`。

| Host | 用户级入口 |
| --- | --- |
| Claude Code | `~/.claude/CLAUDE.md` |
| Codex | `~/.codex/AGENTS.md`，设置了 `CODEX_HOME` 时为 `$CODEX_HOME/AGENTS.md` |

只修改开发 checkout 的 `shared.md`。正式发布才更新已安装版本，运行中的 watch 按仓库 `AGENTS.md` 的 Self-hosting boundary 保持冻结。软链接不需要生成器或后台同步；host 何时重新读取指令由 host 决定，不能假定已有会话会刷新。

## 安装与迁移

安装由主人明确授权。在准备发布的 checkout 中运行：

```bash
bash mmw-v4/install.sh
bash mmw-v4/install.sh --check
```

安装先停止并移除 `com.mmw.prompt-sync`，再安装提示词软链接。旧任务停不下来时不迁移提示词。Codex 的旧生成文件只有来源标记中的正文哈希仍匹配时才会替换。手改过的生成文件、外来文件或外来软链接都会保留并报冲突。把需要保留的内容搬进共享源，再移除冲突入口并重跑安装。缺席的 host 目录跳过。

`--check` 只核对源是否存在、两个入口是否指向安装源、旧同步任务是否残留，不写文件或卸载任务。从其他 checkout 运行时，核对交给 `~/.mmw/installed-root` 指定的已安装版本。

`--back` 在调用旧版安装器之前摘掉两家的 v4 提示词软链接，避免旧生成器沿链接写入 v4 源。

## 验证与范围

```bash
bash mmw-v4/tests/install/run.sh
```

安装测试在一次性目录中验证共享读取、旧文件迁移、冲突保护、旧任务移除、自定义 `CODEX_HOME` 与回退。Codex CLI 0.165.0 的实际指令加载器也验证过指向项目外文件的用户级软链接，以及目标更新后的新一次加载。

该方案面向当前两个 CLI。Claude Cowork 跳过用户级软链接；若服务范围包含 Cowork，需要重新选择交付方式，见 [ADR 0063](../../docs/adr/0063-shared-prompt-through-two-symlinks.md)。
