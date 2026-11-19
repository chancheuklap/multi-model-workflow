# prompt

用户级提示词的源。`shared.md` 是每个 host 的每个会话都读的正文，带不带 mode 都读：读回复的人是谁，哪些决定只归他。别的规矩在 `mmw-mode` 技能里。

| 文件 | 谁读 | 怎么到 host |
| --- | --- | --- |
| `shared.md` | Claude Code、Codex、Grok | Claude Code：`~/.claude/CLAUDE.md` 是指向它的软链。其余两家：`render.py` 把它写进各自的 `AGENTS.md` |

生成文件 = 一行 HTML 注释（来源与正文哈希）+ `shared.md`。改源不改生成物：`render.py` 靠那行哈希认出生成物有没有被人手改，改过就拒绝覆盖，退出 2。

Grok 的 `~/.grok/config.toml` 里 `[compat.claude]` 的 `agents` 必须是 `false`，否则 Grok 把 `~/.claude/CLAUDE.md` 再读一遍，提示词进两次；`render.py` 见到不是 `false` 就报。

Cursor 不在此列：它的用户级提示词只能在 app 里手动粘贴。

```
python3 mmw-v3/prompt/render.py            # 写两份生成文件
python3 mmw-v3/prompt/render.py --check    # 只比对，不一致回 1
python3 mmw-v3/prompt/render.py --adopt    # 目标文件还不是生成物时也覆盖（每台机器首次装）
bash   mmw-v3/prompt/tests/run.sh          # 测试
```

`mmw-v3/install.sh` 负责那条软链、调用 `render.py`，并装一个 launchd 任务监视 `shared.md`，改动即重新生成。Claude Code 读的是软链，不经过 launchd。
