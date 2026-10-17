# 候选 1：同一张表延伸

子代理三行接在「一个 agent 一行」那张表里，用同一套四列：agent、host、model、effort。会话角色一行一个 host，用下拉框选；子代理一行占两行高，host 一列不是下拉框，固定写 `claude`、`codex`，各配一组 model 和 effort。这样 `reviewer` 的 `claude · sonnet · high` 和 `review-axis` 的 `claude · 跟叫它的会话一样 · 跟叫它的会话一样` 上下对齐，一眼能比。

型号目录的状态贴在顶部「本机的 host」每个 host 上：标签后面写「型号目录 11:18 读到」。读失败时，在这个 host 下面加一条斜线提示，写失败时间、种类（中文）、详情，以及下拉框里仍是哪一次读到的目录。

存的型号已不在目录里时，那一格画成斜线，选项里第一项是存的名字加「目录里已经没有」，下面一行写「存的是 X，……现在可选：A、B、C」。会话角色行和子代理行都这样写。

## 文件

- `sheet.mjs`：页面。从 `settings.mjs` 复制过来，多了子代理行和目录状态；`import` 用的是 `/local-config.mjs`、`/shared.mjs`。
- `subagents.mjs`：子代理的视图模型，即 `Subagents` 的选项、问题、改动、`setCell`；`flagsFromErrors` 能认出 `subagents.<行>.<host>.<格>`；`sheetView` 在 `settingsView` 之上把两类行的问题和改动合起来，算页脚和「保存」按钮能不能按。
- `sheet.css`：只放这个方案多出来的部分。

## 考虑过、没选的

- **Claude、Codex 两组横排在同一行**（agent | Claude model | Claude effort | Codex model | Codex effort）。四个下拉框挤在一行，列和会话角色的四列对不上：会话角色的 model 列落在子代理的 Claude effort 下面，「两类行一眼可比」就没了。所以两组上下叠放在同一行内，列不变。
- **子代理单开一个区块，自带表头**。两张表之间隔着标题和说明，列宽会各自算，对不齐。现在用同一个 `.roles` 网格，中间只插一行「子代理」分组标题和一句说明。
- **子代理的 host 一列放一个禁用的下拉框**。看着像能改，其实不能改，所以只写纯文字的 host 名。
- **目录读取时间塞进 host 标签里**（`codex 7 个 model · 11:19`）。失败原因很长，标签里放不下，所以每个 host 改成一行：标签 + 读取时间，失败时下面跟一条提示。

## #1025 §11 没定、这里替它定的

- **Codex 换了型号、原来的 effort 新型号不支持时**：effort 清空，那一格要重新选，选好之前不能保存。这和会话角色行一样，也不会悄悄换成「跟叫它的会话一样」，免得主人以为还是原来那一档。「跟叫它的会话一样」每个型号都能选，所以从它换型号不会被清空。
- **Codex 选了具体型号时**，effort 选项是「跟叫它的会话一样」加上这个型号支持的档位。`_validate_subagents` 对任何型号都接受 `inherit`。
- **页脚计数**：一个子代理行算一处，跟会话角色一样，例如「reader 的 Codex model、Codex effort」。子代理行有问题时，页脚说「MMW 会拒绝」，不说「start 会拒绝」，因为子代理不是 `start` 起的。
- **子代理三行的中文用途**写在 `subagents.mjs` 的 `Subagents.WHAT` 里，照 `roles.json` `subagents` 的英文翻译。§11 要它和 `ROLE_WHAT` 放在一起；这个方案如果胜出，把它挪进 `local-config.mjs`。
- **读取时间的格式**：今天读的只写时:分，更早的写 `月-日 时:分`。
- **失败种类的中文**：`missing` 找不到命令，`timeout` 超时，`exit` 非零退出，`unparseable` 读不出结构，`empty` 读出空列表。
- **点「重新扫描」之后**：扫描的回答（`POST`）里没有 `read_at` 和 `failure`，页面就沿用打开时的值，等下一次 `GET` 再更新。服务端以后在扫描回答里带上这两样，页面就会直接用新的。

## 原型才有的部分

- 「重新读取」要经过 mount 再读一遍数据，因为 fake 补的字段只加在 mount 的 `fromPayload` 上；见 `sheet.mjs` 里的 `reload`。放进产品后，它就是 `fromPayload(body)`。
- CSS 由模块自己插一个 `<link>` 加载。放进产品时，把 `sheet.css` 合进 `styles/settings.css`。
