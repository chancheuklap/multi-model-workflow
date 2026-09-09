# 255-journey-address-case

## 改了什么

`journey.py` 把 `discover` 打印的地址放进环境时，只写每个键的大写拼法（`origin` 进环境是 `ORIGIN`）。小写那一份不再写入。

## 哪些产物失效

- ticket 的 `CHECK:`：一条 `journey.py run <name>` 判据，若其旅程脚本读 `$origin`（或其它 discover 键的小写拼法），变量为空，脚本从绿变红，没有一行指出是大小写的原因。
- screen contract 与 `.mmw/target.json` 不因此失效。

## 怎么迁

旅程脚本改读大写：`$ORIGIN`、`$INSTANCE`、`$INSTANCE_CHECK`。`references/runtime-environment.md` 里 `journeys` 那一条现在写明只认大写。
