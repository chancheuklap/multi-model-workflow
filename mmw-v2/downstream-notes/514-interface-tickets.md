# 514-interface-tickets

## 改了什么

有 screen contract 的 spec，`to-tickets` 按五种 ticket 切： **design-system ticket**、**contract ticket**、**interface ticket**、**app page ticket**、**acceptance ticket**。规则在 `to-tickets/references/cutting-interface-tickets.md`。原先写在 216、220、221、298、344 里、现在仍在役的机制由本说明接住。

Interface ticket 与 app page ticket 的 criterion 与 `## Read first`：

- story：`story-parity.py --contract docs/specs/<effort>/screen-contract.yaml --pages <mount,…>`，`EXPECT: STORY OK <passed>/<total>`。`<total>` 是 scene × viewport。judge 按 `data-ui` id 离线比外观与逐字文案。产品组件根元素的形状见 `453-element-parity.md`。story 服务由 `.mmw/target.json` 的 `stories` 起，不占租约。
- boundary：`boundary-check.py --run "<产品自己的测试>"`，`EXPECT: BOUNDARY OK <n>/<n>`。产品测试断言该行四列；第二遍 `MMW_NEGATIVE=1` 必须红。`wiring-check.py` 已删除；`visual-parity.py` 不再比较运行中的产品。
- `## Read first` 两行 baseline：handoff package（外观与逐字文案）；screen contract 写成 `docs/specs/<effort>/screen-contract.yaml rows: a.b, a.c`（本票拥有的行 id）。其余从这些 id 派生：`scenes.json`，以及每份 baseline 类 `source` 各一次。`--lint` 把这一行当作 interface ticket 的标记。

Acceptance ticket 的 `--break` 与共用 journey helper：

- `journey.py run <name> --break "<METHOD> <route>"`，`EXPECT: JOURNEY OK <name>`。contract ticket 的 smoke journey 不带 `--break`。break switch 的生效方式见 `455-journey-break.md`。
- 两张以上 journey ticket 需要同一套产品入口（起栈、健康检查、登录、充值）时，contract ticket（没有则本批第一张 journey ticket）在 `.mmw/harness/` 写一个 helper，列入它的 **Owns**；后面的 journey 引用它。

`.mmw/target.json` 现行字段：`start`、`stop`、`discover`、`stories`、`journeys`（默认 `.mmw/journeys`）、`leaves_machine`、`harness_markers`，可选 `instance`、`checks`。不再答 `reach` / `transport_off` / `transport_on`。`discover` 打印 origin 类地址加 `instance`；产品是否已停由 `journey.py` 在 `stop` 之后检查 slot 已空。

screen-contract 现行形状：`scenes.<name>` 只留 `page`；scene data 不进合同。行的 `trigger` 是控件的 `data-ui` id。格式的其余键见 `494-screen-contract-format.md`。

scene data 的来源是交接包里的页，不是 `src/*.py`。`design-pages` 的 pull 写入 `scenes.json`；story adapter 读这份数据，按 `data-ui` id 嵌套。形状见 `473-handoff-package-by-pull.md`。

accessible name：Playwright 把可访问性快照里含「 #」或「: 」的键写成 YAML 单引号串。`design_render.py` 的 `unquote_key` 去掉这些引号后再读 ARIA 行和 `<option>` 的名字；`extract_skeleton.py` 用同一函数。skeleton 按 `(page, data-ui id)` 列控件，accessible name 是说明不是身份；需要引号的名字不再被整行跳过。`extract_skeleton.py` 带 `# /// script` 依赖块，`uv run python` 缺依赖时经 `uv run --script` 重跑。

## 哪些产物失效

ticket 的 `CHECK:` 与 `## Read first`：

- 仍写 `wiring-check.py`、整机 `visual-parity.py --mount`、或 `story-parity.py --max-pct` 的界面票。
- `## Read first` 没有 `screen-contract.yaml rows: <id, id>` 的 interface / app page ticket；`--lint` 报 `[screen-contract]`。
- 合同行已经声明某个 page mount，但没有任何 `story-parity.py --pages` 点名它：`--lint` 报 `ERROR … [screen-contract]`（`verify-ticket.py` 对 `expected_pages` 的检查）。
- 某行的 `calls` / `next` / `app` 要求接线检查，票上却没有 `boundary-check.py --run`：同一 `[screen-contract]` ERROR。
- `boundary-check.py --run` 点名的测试文件已经存在，但文件正文里没有该行 `trigger` 的 `data-ui` id：同一 `[screen-contract]` ERROR。测试文件还没写是 WARN，不是 ERROR。
- 不带 `--break` 的 acceptance ticket journey。spec 的 Testing Decisions 仍写 **Cross-ticket flows** 而不是 **Critical flows**（关键流程）的，切票会对不上。
- 两张以上 journey 各自复制登录/起栈、没有 `.mmw/harness/` 共用 helper 的。

`.mmw/target.json`：仍写 `reach` / `transport_off` / `transport_on`、或缺 `stories` / `leaves_machine` / `harness_markers` 的，`target_config.py --check` 从绿变红。`discover` 仍打印 `instance_check` 的，多出来的键不再被求值。

screen contract：仍按 role 与 accessible name 写 `trigger`、或 `scenes` 带 `page` 以外的键、或把 scene data 写进合同的，lint 从绿变红。本仓库 `docs/specs/task-board/screen-contract.yaml`、agentflow `docs/specs/work-monitor/screen-contract.yaml` 与变色龙现役合同仍是这一类，迁法见 `494-screen-contract-format.md`。

handoff package：仍从 `src/*.py` 导出 scene data、或 `scenes.json` 仍是 `{state, vals}` 的，story adapter 读不到现行页上的值。迁法见 `473-handoff-package-by-pull.md`。

## 怎么迁

1. 打开 consuming repository 里有 screen contract 的未关闭界面票。`## Read first` 写成两行 baseline（handoff package；`docs/specs/<effort>/screen-contract.yaml rows: <本票行 id>`），再列出 `scenes.json` 与那些行的 baseline 类 `source`。`CHECK:` 改成上面的 story / boundary 形状；从 story 命令删掉 `--max-pct`。每个被这些行声明的 mount 都要出现在某条 `story-parity.py --pages` 里；每个需要接线检查的行都要有一条 `boundary-check.py --run`，并且 `--run` 点名的测试文件正文里出现该行 `trigger` 的 `data-ui` id。改完跑 `verify-ticket.py <n> --lint`，`[screen-contract]` ERROR 到零。
2. 每条 Testing Decisions 的关键流程（钱、登录、提交链）一张 acceptance ticket：`Owns` 为 `.mmw/journeys/<flow>/`，criterion 带 `--break "<METHOD> <route>"`，默认取该流程合同行里最后一个写操作。contract ticket 的 smoke journey 保持不带 `--break`。
3. break switch 按 `455-journey-break.md` 接到 `.mmw/harness/` 的 `start`。两张以上 journey 共用的起栈/登录放到同一目录的 helper，由 contract ticket（或第一张 journey ticket）列入 **Owns**。
4. 在仓库根跑 `target_config.py --check`（ui-acceptance 技能），按它点名的缺项填 `stories`、`leaves_machine`、`harness_markers`，删掉 `reach` / `transport_off` / `transport_on`。`discover` 打印 `origin` 与 `instance`。旅程脚本放在 `.mmw/journeys/<name>/`。
5. screen contract、skeleton、scene data 仍是旧形状的，分别按 `494-screen-contract-format.md`、`492-skeleton-by-data-ui-id.md`、`473-handoff-package-by-pull.md` 迁。重跑 `extract_skeleton.py` 时，accessible name 含「 #」或「: 」的控件会出现在清单里，给它们补行（行 id 不重排、不复用）。
