# 原型 2：按 host 分块

打开：`http://127.0.0.1:56947/?sheet=1&variant=2`，另有 `&state=read-failed`、`&state=stale-model` 两个状态。

## 这个方案是什么

整页以 host 为单位。从上往下是：

1. **runner** 一行，旁边是「几点问各 host 的 CLI · 重新扫描」。runner 决定去哪里问型号（CLI 还是 Paseo），所以它放在所有 host 之前，扫描入口也挂在它旁边。
2. **每个 host 一块**（claude、codex）。块头是 host 名、现在的状态标签（「4 个 model」「本机没装」等，沿用原页的标签），右边写「型号目录 11:18 读到」。上次读取失败时，块头下面加一条斜线提示，写明失败时间、五种原因之一的中文和详情，以及「下拉里仍是 11:19 读到的目录」。
3. 块里第一段是**会话角色**：host 是这个 host 的那几行，四列（agent、host、model、effort）和原页一样。host 下拉框仍在；把某一行换到另一个 host，这一行就搬到那个 host 的块里，键盘焦点跟着这个下拉框过去，页面滚到它的新位置。
4. 块里第二段是**子代理**：review-axis、reader、default 三行，每行一句中文用途，只有 model 和 effort 两格，和上面会话角色的 model、effort 两列对齐。说明写的是「跑在 claude 上的会话派子代理时，用这几格」：models.json 里子代理按「派它的会话所在的 host」各存一格，这正好落在按 host 分块的页面里。
5. 页面上一律显示「跟叫它的会话一样」，存进去是 `inherit`。codex 的 effort 随所选 model 变；model 选「跟叫它的会话一样」时，effort 只列每个可见 codex 型号都支持的档位（假数据下是 low、medium、high）。
6. **存的型号已不在目录里**：那一格斜线标出，下拉里第一项是「gpt-5.5-sol · 目录里已经没有」，格子下面一行写「存的是 gpt-5.5-sol，codex 的目录里已经没有；现在可选：……」。会话角色行沿用原页的标记，只把原来那句「这台机器的 claude 已经不提供 opus[old]」换成同样的句式。

保存仍是底部一个按钮、一次 `PUT /api/settings`，多带 `subagents` 整段。改动计数、扫描中、冲突（409 → 重新读取）、拒绝（422 → 斜线标出那一格）、Escape 和关闭都照旧。我用无头浏览器逐项操作过：子代理改动计入「改了 N 处」；真实后端收下并写入了 `subagents`（之后已改回全部 `inherit`）；模拟的 422 `subagents.review-axis.codex.effort` 标在了 codex 块里 review-axis 那一行的 effort 格下；409 之后重新读取恢复正常；重新扫描后读取时间会更新；把 reviewer 的 host 换成 codex 后，它出现在 codex 块里，焦点也在它身上。

## 在「按 host」这个角度里考虑过、没有采用的

- **每块里列出全部会话角色，用一个「跑在这里」开关决定归属。** 每个角色会出现两次，而且 models.json 一个角色只存一组 host、model、effort。两块里各放一组 model 下拉，就是在画一个不存在的配置。
- **按 host 分标签页（claude | codex），一次只看一个。** 主人看不到整台机器的配置；「改了 N 处」会把看不见的标签页里的改动也算进去；另一个 host 读目录失败时，提示藏在没打开的标签页里。
- **会话角色仍用原来那张按 agent 排的表，host 块只放目录状态和子代理。** 那样页面的主轴仍是 agent，不属于这个角度；而且同一个 host 的事情会分散在两处。
- **把会话角色拖到另一个 host 块里来换 host，去掉 host 下拉框。** 键盘和读屏用不了，测试也不好找；简报要求 host 下拉框保留。
- **子代理三行合成一行，用一个下拉框选「哪个子代理」。** 省地方，但主人一眼看不到三行各配了什么，也做不到逐格标出 422。

这个角度要付的代价是：改 host 时整行会挪位置，原页一行固定不动。我用「焦点跟着走，并滚到新位置」来减轻它；主人试的时候请特别留意这一点是否别扭。

## #1025 §11 没有说定、我做了决定的地方

- **子代理用哪一格：** 按派它的会话所在的 host（依据 mmw-mode `## Subagents`：`models.py subagent <row> <host>` 里填的是自己所在的 host）。页面在每个 host 的子代理段里直接写明这一点。
- **codex 换 model 后，原来的 effort 新型号没有：** effort 改回「跟叫它的会话一样」，不留空。`inherit` 对任何型号都合法，所以换完不会卡住保存；这一格会显示为「已改动」。
- **存的子代理型号已不在目录里：** 算作 start 会拒绝的一处，保存按钮不可用，直到改掉。依据：每次 PUT 都会把 `subagents` 整段发出去，models.py 一定会以「choose one of …」拒绝它。这只是读接口给的 `stale` 列表，页面没有另写一套校验。
- **Claude 子代理的 model 选项**只有 sonnet、opus、haiku、fable（派子代理时调用接受的别名），不附会话角色下拉里那句英文说明，也不受 claude 目录读取成败的影响。
- **读取时间**按本机时区显示；不是今天的，加上「10月16日」这样的日期。
- **失败原因的中文：** missing 本机找不到它的 CLI；exit CLI 出错退出；timeout 超时；unparseable 回答看不懂；empty 回答了一个空列表。详情原样跟在括号里。
- **重新扫描的回答没有 `read_at` 时：** 扫描成功的 host 用这次扫描的时间作为读取时间。接口定稿时，`POST /api/settings/scan` 的回答也要带 `read_at` 和 `failure`，和 GET 一样；`fake.mjs` 现在只补了 GET。
- **MMW 不认识的 host：** 会话角色存了一个 hosts.json 里没有的 host 时，这一行放进最后一块「MMW 不认识的 host」，不会丢。

## 搬进产品时要改的

- 删掉 `import {withFake} from "../../fake.mjs"`。它只是为了让原型里的「重新读取」也带上假字段。
- `Subagents` 对象和合并后的底栏文字逻辑应并入 `local-config.mjs`（`LocalConfig.changes`、`problems`、`settingsView`）。原型为了不改 `local-config.mjs`，在 `sheet.mjs` 里把这一段重写了一遍。
- `SUBAGENT_WHAT` 应和 `ROLE_WHAT` 放在一起，并加上 #1025 §11 说的那条测试：`roles.json` 的 `subagents` 里每一行都有说明。
