# 344-quoted-accessible-names

## 改了什么

Playwright 在可访问性快照里，把一个节点的键（`role "name" [attrs]`）写成 YAML 单引号串，只要这个键不能按普通 YAML 读——名字里有「 #」或「: 」就够——引号里的单引号写成两个。drive-target 技能读快照的三处原来都不认这种行，整行跳过：`extract_skeleton.py` 的 `controls`（行清单）、`screen_driver.py` 的 `normalize_aria`（story judge 与 target trees 共用的归一化）、`screen_driver.py` 的 `name_options_from_dom`（`<option>` 的名字）。现在三处都先经 `screen_driver.py` 的 `unquote_key` 去掉 YAML 的引号，再按普通行读。

同一次改动给 `extract_skeleton.py` 加了 `# /// script` 依赖块（`playwright`、`pyyaml`）；以 `uv run python` 调用时缺依赖就经 `uv run --script` 重跑一次，不再要求调用方自己带 `--with`。

## 哪些产物失效

只影响交接包里有控件或文字的可访问名字含「 #」或「: 」的 consuming repository；没有这种名字的，重跑后什么都不变。

- **screen contract**：重跑 `extract_skeleton.py` 后，行清单多出原先被跳过的控件（例如 `button "收起 #98"`、`button "在 GitHub 打开 #133 ↗"`），`lint_contract.py` 对每个还没有行的报 `skeleton control without a row`。
- **target trees**：`docs/specs/<effort>/targets/<page>.aria` 缺这些节点。头部哈希只看 `scenes.json` 与页，不会失配，所以 lint 不会自己报出来。
- **ticket 的 `CHECK:`**：命令不变。但 `story-parity.py` 的树比对现在两边都读这些节点，以前比对里看不见的差异（产品把这类名字写错、漏掉）会成为 `DIFF`。
- **`.mmw/target.json`**：不变。

## 怎么迁

判断是否受影响：`grep -l "^\s*- '" <story-parity --out 目录>/*.aria.yml`，或对交接包跑一次 `extract_skeleton.py` 看行数是否变多。受影响时：

1. 按 align-screens 的「Re-runs」第一条重跑第 1 步和第 6 步：`extract_skeleton.py` 出新的 skeleton，给多出来的控件补行（行 id 不重排、不复用），再 `extract_skeleton.py --targets … --contract …` 重写 target trees，`lint_contract.py` 到零错误。
2. 已关闭的界面票不必重开；下一次跑它们的 story 判据（`reverify`）若出现新的 `DIFF`，按回归处理。
