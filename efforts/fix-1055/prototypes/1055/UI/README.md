# #1055 本机配置：子代理一块与型号目录状态（UI 原型）

**问题。** 「本机配置」要加 #1025 §11 的三样东西（子代理三行、每个 host 的型号目录状态、存的型号已不在目录里），页面怎么组织。

**结论（主人 2026-10-17 选定）：`winner/`。**
- 三个页签：「会话角色」「子代理」「型号目录」，共用底部一个状态栏和一个「保存」（一次 `PUT /api/settings`，多带 `subagents`）。页签名后带标记：`N 处不对`、`改了 N 处`、`读取失败`、`N 格旧型号`。
- 「子代理」页用方案 1 的排版：和「一个 agent 一行」同样四列（子代理、host、model、effort）；每个子代理占两行，host 一列固定写 `claude`、`codex`，各跟 model、effort 两个下拉框。说明：「会话内部临时派出的帮手，只在步骤点名时派。每一行在 Claude、Codex 上各有一组；派它的会话在哪个 host 上，就用哪一组。「跟叫它的会话一样」就是用派它的那个会话自己的 model 或 effort。」三行用途：
  - `review-axis`：code-review 的四个审查轴，一个轴派一个
  - `reader`：读大量材料，交回压缩过的结论
  - `default`：其余点了名的子代理步骤，也包括没点行名的
- 「型号目录」页：「本机的 host」（扫描时间、重新扫描）搬到这里；每个 host 一张卡：状态标签、「目录读于 HH:MM（N 小时前）」、读失败时一条斜线提示「最近一次读取失败（时刻）：<种类> · <详情>。仍在用 HH:MM 读到的那份。」、「现在可选」；下面「存的型号已不在目录里」逐格列出，每格「跳到这一格」切页签并把焦点放到那一格。
- **型号的名字全页只有一种**（主人定）：都用会话角色那一列的写法，即 `models.py` 的 `_slug_everyday(id)`，目录有说明时加「 · 说明」（`gpt 6.1 sol`、`sonnet · Most efficient for simpler tasks`）。**存进 `models.json` 的值不变**：会话角色行存这个名字（现状），子代理的 codex 格存目录 id（`gpt-6.1-sol`，`_validate_subagents` 只认 id），`inherit` 存 `inherit`。页面上的名字由接口按 id 给出（`subagent_options.labels`），页面不自己换算。
- Codex 换 model 后原 effort 不被支持时，effort 落回「跟叫它的会话一样」；model 选「跟叫它的会话一样」时，effort 只列每个 Codex model 都支持的档位。
- 有一格存的型号不在目录里时，「保存」不可用（`models.py` 本来也会拒）。

**试过、没选的。** 方案 1「同一张表延伸」（子代理接在会话角色表下，读取时间贴在顶部 host 标签旁）：子代理排版被采用，整页结构没选。方案 2「按 host 分块」：页面主轴改成 host，和现在差别最大，没选。方案 3「三个页签」：整页结构被采用，它原来的子代理排版（Claude、Codex 两组四列横排）换成方案 1 的。各方案的理由见 `candidates/<n>/README.md`。

**接口（API fake 的草稿，见 `fake.mjs` 头注释）。** 真后端已有：`models.json` 的 `subagents` 读写与校验、`scan.hosts.<host>.read_at` / `failure`（读真 CLI 时）。要新加的：`subagent_options`（`rows`、claude 的固定选项、codex 的目录选项、`labels`）、缺省时三行 `inherit`、`stale`。

**原型对决策（#1025 §11 的每条界面规则）。** 子代理一块与一句说明 ✓；三行各有行名和中文用途 ✓；Claude model：跟叫它的会话一样、sonnet、opus、haiku、fable ✓；Claude effort：跟叫它的会话一样、low、medium、high、xhigh、max ✓；Codex model 来自目录、effort 随 model 变、都含「跟叫它的会话一样」✓；页面不显示 `inherit`、存 `inherit` ✓；Codex 选「跟叫它的会话一样」时 effort 只列共有档位 ✓；每个 host 显示目录读取时间 ✓；读失败写出种类和详情 ✓（状态地址 `?state=read-failed`）；存的型号不在目录里写明存的名字和可选的名字 ✓（`?state=stale-model`）；同一个保存按钮、同一次 PUT，冲突、校验失败时提示和现在一样 ✓；可选值由设置接口给，页面不写死 ✓（`fake.mjs` 即接口草稿）。

**真代码要拿走的。** `winner/sheet.mjs` 的页签、子代理行和型号目录页，并入 `mmw-v4/board/page/settings.mjs`；`SUBAGENT_WHAT` 挪到 `local-config.mjs` 的 `ROLE_WHAT` 旁；`winner/sheet.css` 并入 `styles/settings.css`；`reload()` 里经过 mount 的那一步去掉。
