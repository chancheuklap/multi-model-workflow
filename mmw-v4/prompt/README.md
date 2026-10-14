# prompt

用户级提示词的源。`shared.md` 是每个 host 的每个会话都读的正文，带不带 mode 都读：关于读每条回复的那个人的事实。哪些决定只归他，在 `principle-never-block-on-the-human` 技能里；别的规矩在 `mmw-mode` 技能里。

| 文件 | 谁读 | 怎么到 host |
| --- | --- | --- |
| `shared.md` | Claude Code、Codex | Claude Code：`~/.claude/CLAUDE.md` 是指向它的软链。Codex：`render.py` 把它写进 `~/.codex/AGENTS.md`（设了 `CODEX_HOME` 就写进那里） |

生成文件 = 一行 HTML 注释（来源与正文哈希）+ `shared.md`。改源不改生成物：`render.py` 靠那行哈希认出生成物有没有被人手改，改过就拒绝覆盖，退出 2。

```
python3 mmw-v4/prompt/render.py            # 写生成文件
python3 mmw-v4/prompt/render.py --check    # 只比对，不一致回 1
python3 mmw-v4/prompt/render.py --adopt    # 目标文件还不是生成物时也覆盖（每台机器首次装）
bash   mmw-v4/prompt/tests/run.sh          # 测试
```

`mmw-v4/install.sh` 负责那条软链、调用 `render.py`，并装一个 launchd 任务监视 `shared.md`，改动即重新生成。Claude Code 读的是软链，不经过 launchd。
