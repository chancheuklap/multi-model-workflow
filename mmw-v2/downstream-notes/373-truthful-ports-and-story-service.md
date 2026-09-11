# 373-truthful-ports-and-story-service

## 改了什么

1. **story 服务脱离租约。** `story-parity.py` 不再给 `stories` 命令传租约变量，也不再占槽；它只传 `MMW_AUTOMATION=1`。story 页面是产品的展示组件加 scene data，背后没有后端、没有种子、没有路由，需要的只是一个端口，而那个端口由机器分配最省事。`verify-ticket.py` 的"跑产品的判据"不再包含 `story-parity.py`，所以界面票不再占 `instance.max`。
2. **端口是否被占用改成问端口本身。** `lease.py` 的 `listener()` 先向 `127.0.0.1` 和 `::1` 发连接，连得上就是有人在听，再退回原来的 bind 检查。原来只用带 `SO_REUSEADDR` 的 bind 探 `127.0.0.1`：BSD 语义下有人占着 `0.0.0.0` 时这个 bind 照样成功，所以容器引擎发布的端口、以及只监听 `::1` 的服务（Node 把 `localhost` 解析成 `::1`）全部看不见，`release` 和 `sweep` 会把还活着的栈的槽收回去。
3. **旅程的收尾。** `journey.py` 在负控制那一遍之后再跑一次 `stop`，然后检查本次租约的端口段；还有人在听就报 `JOURNEY LEFT THE PRODUCT UP <name>`（exit 1），并点名端口、pid 与该进程的目录。
4. **harness guard 读 git 跟踪的文件。** `harness-guard.py` 扫的是 `git ls-files --cached --others --exclude-standard`，不再是整个目录树；同时放行不随发布走的测试文件（路径段 `__tests__`、`__mocks__`，或文件名以 `.test.<ext>`、`.spec.<ext>` 结尾）。

## 哪些产物失效

- `.mmw/target.json` 的 `stories` 命令：从 `MMW_PORT_BASE` 推导端口的写法失效，那个变量不再传给它。
- `.mmw/target.json` 的 `stop`：停不干净的现在会被看见——`release` 拒绝还槽，旅程报 `JOURNEY LEFT THE PRODUCT UP`。以前"看不见"不等于当时是对的。
- ticket 的 `CHECK:`：跑 `story-parity.py` 的判据不再占槽，`instance.max` 可以按真正要起整栈的票重估；为躲开 harness guard 而把变量名拼接起来的产品代码（`process.env["MMW_" + "NEGATIVE"]`）可以改回直接读，前提是那个文件符合上面的测试文件命名。

## 怎么迁

1. `stories` 命令改成向机器要端口：绑 `127.0.0.1:0`，再打印实际拿到的端口作为 `origin`。例如 Python：

   ```
   server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
   print(f"origin=http://127.0.0.1:{server.server_address[1]}", flush=True)
   ```

   Vite 一类的开发服务器：不要传固定端口，把它打印的地址原样作为 `origin`。
2. 确认 `stop` 之后本次租约端口段全空（含容器发布的端口），用 `lease.py release <worktree> --stop` 自查。
3. 旅程脚本里删掉任何"发现产品没起就起一遍"的兜底。
4. 把为躲开 harness guard 写的拼接读法改回直接读，并确认该文件在 `__tests__/`、`__mocks__/` 下或以 `.test.*`、`.spec.*` 结尾；两者都不成立就把它移进 `tests/`。
5. 重估 `instance.max`：现在只有真正起整栈的票占槽。
