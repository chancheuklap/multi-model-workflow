# 本机配置
Route: / → 顶栏齿轮「本机配置」
Tests: settings.e2e.ts, subagents.e2e.ts

在看板上看、改这台机器上每个 agent 跑在哪个 host、model、effort，以及会话派子代理时用哪个 model、effort，保存到本机的 `models.json`。分三个页签：「会话角色」「子代理」「型号目录」，共用底部一个状态栏和一个「保存」。

## Sub-features

- 「会话角色」：runner（用什么起 session），和「一个 agent 一行」：每个会话角色一行，host、model、effort 三个下拉框。
- runner 的启动能力决定可选 host。选择 codex-app 后，全部会话角色自动切到 codex，模型只来自对应目录；兼容的已有模型和 effort 保留，不兼容的值按新目录调整。子代理和型号目录页只显示所选 runner 支持的 host，其他 host 的子代理配置保留，切回对应 runner 后重新显示。
- 「子代理」：`review-axis`、`reader`、`default` 三行，各写一句用途；每行在 claude、codex 上各有 model、effort 两个下拉框。「跟叫它的会话一样」就是用派它的那个会话自己的 model 或 effort。Claude 的 model 可选 sonnet、opus、haiku、fable，effort 可选 low 到 max；Codex 的 model 来自它的型号目录，effort 随所选 model 变；Codex 选「跟叫它的会话一样」时，effort 只列每个 Codex model 都支持的档位。
- 「型号目录」：每个 host 问到了几个 model、目录是什么时候读到的、现在可选哪些；最近一次读取失败时，写出失败种类和详情，并说明仍在用哪一次读到的那份；「重新扫描」再问一次。下面列出所有「存的型号已不在目录里」的格子，写明存的名字和现在可选的名字，「跳到这一格」把焦点放到那一格。
- 一个型号在整页只有一种名字，和「会话角色」那一列的写法相同。
- 页签名后标出这一页的情况：几处不对、改了几处、读取失败、几格旧型号。
- 底部状态栏写改了几处、为什么不能保存、已保存；有格子不对时「保存」不可用。「保存」一次写回整份配置，子代理也在里面。
- 打开之后配置被别处改过，保存被拒，「重新读取」换成现在保存着的内容。

## How to get to it (user POV)

打开看板，点右上角齿轮「本机配置」，再点页签。不需要账号。

## Driving it with e2e

`settings.e2e.ts` 改 `reviewer 的 effort`，看底部「改了 1 处：」，点「保存」看「已保存」，关掉再打开，读回新值。`subagents.e2e.ts`（#1055）在「子代理」页改 `reader 的 Codex model`、`reader 的 Codex effort`，保存后重开读回；在「型号目录」页看读取时间和「现在可选」；目录读取失败、存的型号已不在目录里两个状态，用 `browser.route` 改 `GET /api/settings` 的回答。

下拉框按「<agent> 的 host / model / effort」和「<子代理> 的 Claude|Codex model|effort」的可访问名字找；页签是 `tab`，名字以页签名开头、后面跟标记（按 `/^子代理/` 找）；子代理一行是 `group`「子代理 <行名>」；关闭按钮是「关闭本机配置」。「改了 N 处」在页签标记和底栏各出现一次，底栏那句带冒号（`/^改了 1 处：/`）。

## Proof

- 改过的格子在关掉、重新打开本机配置后仍是新值，底部写「已保存 · <时刻>」。
- 「子代理」页三行各有用途；Claude 的 model 有 5 项、effort 有 6 项；Codex 的 model 有 8 项（「跟叫它的会话一样」和目录里的 7 个），选「跟叫它的会话一样」时 effort 只有「跟叫它的会话一样、low、medium、high」；选项里的型号名和「会话角色」那一列的写法相同（`gpt 6 luna`、`sonnet · Most efficient for simpler tasks`）。
- 「型号目录」页两个 host 都写「目录读于 HH:MM」和「现在可选：…」；读取失败时写「最近一次读取失败（时刻）：<种类> · <详情>。仍在用 HH:MM 读到的那份。」，页签带「读取失败」。
- 存的型号已不在目录里时，页签带「N 格旧型号」，「保存」不可用，那一格列在「型号目录」页，写「存的是 <名字>，<host> 的目录里已经没有；现在可选：…」，「跳到这一格」把焦点放到那个下拉框。

存进 `models.json` 的值（子代理 codex 格存目录 id、`inherit` 存 `inherit`）由票里的后端测试证明，不在 e2e 里断言。

## Gotchas

- 每次运行的 `MMW_HOME` 是新的，从 `scripts/dev/board-fixtures/` 起步：`reviewer` 是 claude、sonnet、high，子代理都是「跟叫它的会话一样」。型号目录来自 `host-catalog.json`，不问本机的 claude、codex。
- 「重新扫描」在测试里读的是同一份目录，看不出目录变化；目录读失败、存的型号不在目录里，这两个状态本机造不出来，用 `browser.route` 改 `GET /api/settings` 的回答（`subagents.e2e.ts` 的 `answerSettings`）。
- 读取时间不是今天时，页面写成「10月16日 23:38」；测试数据里的读取时间是固定的，总有一天不是今天，断言读取时间要容许前面的日期。
- 同一次运行的测试共用一个看板和一份 `models.json`，所以配置里 `workers: 1`；两个测试同时保存会互相得到 409。
