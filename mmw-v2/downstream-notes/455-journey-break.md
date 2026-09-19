# 455-journey-break

## 改了什么

`journey.py run <name> --break "<METHOD> <route>"` 的第二遍会重启真实产品，并只让指定接口失败；journey 必须在这一遍失败。`start` 只在第二遍收到 `MMW_BREAK`，生效后必须打印逐字相同的 `BREAK ARMED <METHOD> <route>`。journey 脚本不再收到 `MMW_JOURNEY_NEGATIVE`，也收不到 `MMW_BREAK`。不带 `--break` 的旧 `CHECK:` 仍按停掉产品并改写地址的方式运行。

## 哪些产物失效

- 带 `--break` 的 ticket `CHECK:` 若消费仓库的 `.mmw/harness/` 尚未实现 break switch，会在第二遍启动后退出 2。
- journey 脚本若读取 `MMW_JOURNEY_NEGATIVE` 来提前结束第二遍，该分支不再运行，必须删除。
- screen contract 与 `.mmw/target.json` 的字段没有改变；失效的是 `.mmw/harness/` 的启动行为和依赖旧变量的 journey 脚本。

## 怎么迁

1. 删除 journey 脚本中读取 `MMW_JOURNEY_NEGATIVE` 的分支；脚本两遍执行同一路径。
2. 在 `.mmw/harness/` 的 `start` 所启动的产品进程中实现 break switch：读取 `MMW_BREAK` 的 `<METHOD> <route pattern>`，按产品自己的路由规则匹配占位符，只让该接口失败，不改变其它接口。
3. `start` 确认 break switch 已生效后打印逐字相同的 `BREAK ARMED <METHOD> <route>`；该变量不要传给 journey 脚本或其它会让脚本判断 pass 的进程。
4. 把新 acceptance criterion 写成 `journey.py run <name> --break "<METHOD> <route>"`；已有不带 `--break` 的 `CHECK:` 无需改写。
