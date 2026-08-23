# mmw-v2/skills

自研技能源目录。不负责上游技能，那些在 `mmw-v2/upstream/`。

- 只有 `exe-release/scripts/` 需要第三方 Python 包（`pydantic`，经 `uv run --with`）；其余脚本用裸 `python3` 或 `bash`。
- 技能正文调用自己脚本的写法：先解析一次绝对路径，再到处用（`exe-release/SKILL.md` 的做法）。
