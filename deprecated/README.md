# deprecated

mmw-v2 里退役的技能与 subagent。**不装、不跑、不当事实**：`mmw-v2/skills.txt` 里没有它们，`install.sh` 不碰这个目录，`assemble.py` 也扫不到。留在仓库里只为一件事——将来要拿回哪一部分时，原件还在。

`archive/` 是上一代 `mmw` 的整体冻结归档；这里是 v2 自己退下来的东西，两者不是一回事。

## `ui-qa`（2026-08-30 退役）

按约定标准检查界面，九种检查分两类：A1–A4 确定性的算违规，B1–B5 模型判断的算发现。

退役是因为 v2 的落地流水线定型之后，九种检查的去向逐个查完，没有一种还需要它：

| 检查 | 判什么 | 现在由谁做 |
| --- | --- | --- |
| A1 尺寸阈值 | 按钮和字够不够大 | `mmw-v2/skills/verify-ticket/scripts/visual-parity.py`——实现与基线不一致就失败 |
| A3 token 越界 | 颜色圆角的值在不在设计系统里 | 同上 |
| B1 设计系统规则 | 违没违反 `DESIGN.md` 的规矩 | 同上 |
| A4 运行时报错 | 页面报不报 JavaScript 错 | 同上，`--console-errors` 参数，默认一条都不许有 |
| B2 认知走查 | 用户找不找得到下一步 | 用户自己判 |
| B3 困惑度 | 这一步卡不卡人 | 用户自己判 |
| B4 Trunk Test | 初见者知不知道这是哪 | 用户自己判 |
| B5 可用性标准 | 违没违反这个产品自己的规矩 | 用户自己判 |
| A2 无障碍 | 读屏念不念得出、键盘走不走得到 | **没有人做。** 见下 |

另外三处和流水线直接冲突，使它无法原样接进去：它自己改代码自己提交（票有 `## Owns` 管着谁能改哪些文件）；它停下来逐条问用户（夜里派出去的 worker 没人答）；它要四个外部依赖，缺两个就停。

**A2 是唯一没有承接对象的一种。** `visual-parity.py` 里没有 axe-core，一处都没有；它比的是 ARIA 树一不一样，不是判无障碍对不对。而 `aria-label`、`tabindex` 这些是写代码时才产生的属性，Claude Design 的基线里根本不存在，所以这一种不可能靠比对基线查出来。要拿回来的话，拿的是 `scripts/deps.json` 里 `accessibility` 那一条能力，落点是 `mmw-v2/skills/verify-ticket/scripts/` 下一个新脚本、票上一条 `CHECK:`，不是这整个技能。

## `claude-design-blocks` 的 port 脚本（2026-09-20 退役）

把本地 mockup 变成 Claude Design 页面的一套脚本：`mk.py`（按 `src/<name>.py` 生成 `.dc.html`）、`example.src.py`（源文件模板）、`mkharness.py`（切换 scene 的测试页）、`serve.sh`（用预览地址查看已上传的页）、`deadsweep.py`（清掉没人引用的类规则），以及把 scene data 从下载下来的页里跑出来的 `export_scene_data.py` 与 `export_scene.js`，连同它们的测试与夹具。

退役是因为设计不再在仓库里生成：Claude Design 项目是设计的唯一源头，页面在那里写、在那里改，仓库这一侧只有 pull。这套脚本承担的事现在归 `mmw-v2/skills/design-pages/`：页面由你或 agent 经 MCP 在 Claude Design 里写（`references/edit-pages.md`），scene data、`scenes.json`、`vendor/`、README 与 pull report 由 `scripts/pull_design.py` 一次写出（`references/pull.md`）。选择器检查没有退役，改名为 `scripts/check_editable_selectors.py`，仍在这个 skill 里。

## `agents/verifier`（2026-09-05 退役）

按票重跑验收标准、在票上留一行 `VERDICT` 的原生 subagent。提示词正文现在是 `mmw-v2/skills/dispatch/references/verifier.md`，随 dispatch 技能一起装，由 `dispatch.sh start <n> verifier` 写进 initialPrompt。这里留下退役当天的 `agent.json` 和 `out/claude.md`，此后不再装配。

## `ui-evaluator`（2026-08-30 退役）

以初见者身份判断界面的 subagent，只被 `ui-qa` 的 B2、B3、B4 派。那三种归用户自己判之后，它没有调用方了。

`out/` 里五个宿主的成品是退役当天的那一份，此后不再装配。
