# mmw-v2/skills/ui-qa

界面 QA。不安装任何依赖：`scripts/check-deps.sh` 只报告四种能力在哪，`deps.json` 故意不锁版本。

- `check-deps.sh` 和它的测试硬依赖 `jq`。
- 外部技能 `create-design-md` 不经 `install.sh` 安装，来自 `npx skills add ibelick/ui-skills@create-design-md -g -y`，检测路径 `~/.agents/skills/create-design-md/SKILL.md`。
- `deps.json` 经 `jq … | @tsv` 读取，可选字段缺省填 `-` 而不是空串，否则 `IFS=$'\t'` 会吞掉连续制表符让后面的字段左移。
- 单跑 Python 测试：`uv run --quiet --with pytest python -m pytest tests/test_wiring_lint.py -q`。
