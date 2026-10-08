---
date: 2026-10-08
amends: []
---

# 一个仓库里每个产品占 `.mmw/<产品>/`，一次运行仍只租一个按产品分段的 lease，control-ui 与 control-cli 是 ui-acceptance 的 reference 而不是 skill

一个仓库里常有几个产品，网页后台和 Electron 桌面端放在一起。根 `.mmw/target.json` 只留 `checks`、`products` 和 `needs`。每个产品的起停、体检和界面验收放在 `.mmw/<产品>/`，里面是 `target.json`、`harness/`、`stories/` 和 `journeys/`。一次运行租一个 lease。这个 slot 的端口块按根上 `products` 的次序切给各产品，数据目录按产品分开。有 `needs` 时先起被依赖的产品，把它 `discover` 打出的地址交给下一个。登记里的 `started` 按起的次序记产品名，`release --stop` 按倒序跑各产品的 `stop`。操作网页、Electron 和命令行的写法在 `mmw-v3/skills/ui-acceptance/references/control-ui.md` 与 `control-cli.md`，和 `journey.md` 放在一处。产品用 `start` 在 lease 里起。

## Considered Options

- **根 `target.json` 加 `surfaces` 列表。** 否决。产品答案还是挤在同一个文件里，两张票会写同一处。spec #894 `### 2. 目录布局与唯一的读入点` 改成每个产品一个目录，根上只留 `checks`、`products`、`needs`。contract ticket 只拥有自己那个产品的 `.mmw/<产品>/`。
- **每个产品一个 lease。** 否决。一次运行要同时起被测产品和它依赖的产品，并且一起停掉。spec #894 `## Solution` 定的是一次运行仍只租一个 lease。一个产品一份 lease 会把同一次运行拆成多份登记。端口分段、`started` 和倒序停都没有一个登记可写。
- **照 pstack 给每个仓库生成一个验证 skill。** 否决。spec #894 `### 7. 引入 create-verification-skill，并让 setup-mmw 逐个产品接入` 让 create-verification-skill 写 `.mmw/<产品>/`，不写 `.cursor/skills/verify-<app>/`。pstack 的 Launch、Doctor、Drive、Evidence、Cleanup、Isolate 落到已有的 `start` 与 `stop`、`doctor`、证据位置和 lease 分段上。再生成一份验证 skill，就是把同一套验收再写一份。
- **control-ui 作独立 skill。** 否决。spec #894 `### 8. control-ui 与 control-cli 作为 ui-acceptance 的 reference` 采纳 advisor 2026-10-07 的意见。改写后剩下的是多窗口共用调试端口时怎么选页面、一次做一个动作再看一次、以及 CDP 能做的事。这些属于 `mmw-v3/skills/ui-acceptance/references/journey.md` 的 `## What the script gets, and what it must be`。两份 skill 讲同一件事，按 `mmw-v3/skills/mmw-mode/references/skill-set-rules.md` 的 `## Checks` 里 Duplication 一条删一份。`mmw-v3/imports.tsv` 的 J579 已经把 runtime-forensics 里的 "via the control skill" 改成在 lease 里用 `start` 起自己的实例。这个判断保留。control-cli 同样不单独成 skill。

## Consequences

- 根 `.mmw/target.json` 出现 `start` 这类产品键，就是旧布局。产品自己的键在 `.mmw/<产品>/target.json`。`checks` 仍是整仓的，可以没有。
- journey 的名字是 `<产品>/<flow>`，目录是 `.mmw/<产品>/journeys/<flow>/`。只有一个产品的仓库也这么写。
- ADR 0038 的分层不变。`.mmw/<产品>/` 仍是 `.mmw/` 那一层，是 MMW 会执行的产品答案。
- Electron 两套并行的结论在 `efforts/verification/prototypes/894/EXP/README.md` 的 `## 5. Conclusion`，2026-10-08 实测。端口都落在自己那一段，并且 `start` 把用户数据目录以外的状态也挪进 `MMW_DATA_DIR` 时，两套 parrot 互不干扰。只换用户数据目录不够。`PARROT_DUBBING_RUNTIME_ROOT` 不移动数据库，要设 `PARROT_DUBBING_DB_PATH`。两个日志根、`RUNTIME_DIR`、渲染进程的后端端口和 Vite 端口也要挪。单实例锁跟着用户数据目录走。Vite 会从 5173 静默换到下一个空端口，那个端口在 lease 外面。命令行没给调试端口或后端端口时，产品不得自己选一个写死的端口。写死的端口既躲开 lease，也躲开最后那次端口安静检查。
- Gateway 实测听 4 个端口。harness 仍占块内第 3 到第 6 个时，`ports` 写 7。parrot 和 hedgehog 在开发模式各要 3 个端口，分别是后端、CDP 和 Vite，不是 2 个。打包后的应用，以及 `electron-vite preview`，去掉 Vite 那一个。三者合计 13 个端口，少于一个 slot 的 20 个。`PORT_STRIDE` 的默认值是 20。
- 先起依赖是安全规则，不是存活规则。未激活的 parrot 没有 Gateway 也能起来，设置页能用。激活之后的功能需要 Gateway。生产地址的回退是真的。agentflow 里 parrot 的 `app.py`、`client_security.py` 和 `api/activation_routes.py` 依次读 `PARROT_GATEWAY_BASE_URL`、`GATEWAY_URL`、`https://capyapi.cn`。hedgehog 依次读 `HEDGEHOG_GATEWAY_BASE_URL`、`GATEWAY_URL`，然后再到生产地址。所以有 `needs` 的 `start` 在没拿到依赖地址时不得启动。
- `doctor` 在两套实例上都通过。每个监听都属于该实例自己的进程组，版本是源提交。
- 停的次序是先 parrot，后 Gateway。40 个端口随后都安静。`stop` 跑 `compose down` 且不带 `-v` 时，留下两个具名卷，以及每个实例一个 2.9 GB 的 `mmw-<instance>-gateway` 镜像。`lease.py list` 把 Docker 发布的端口记在 colima 的 `ssh … [mux]` 进程上，cwd 对不上。点名产品、端口和 pid 的拒绝，会把 Gateway 端口的 pid 说成 colima。
- 截图在 `stop` 和 `release` 之后还在 `$MMW_DATA_DIR/parrot/evidence`。`lease.py remove-instance` 在工作树消失后会删掉它们。要先拷出来。
- 真去操作一个 parrot 功能，需要已经激活的实例。激活要过浏览器授权，那是人的一步。系统原生对话框，调试端口够不到。这两件不在这份决定里改产品。
