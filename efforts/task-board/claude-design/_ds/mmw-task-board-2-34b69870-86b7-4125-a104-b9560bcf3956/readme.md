# MMW 任务板 Design System

MMW（multi-model workflow）是一套在本机跑的多模型流水线：若干 agent 各自在自己的 host、model、effort 上跑 ticket，一个 supervisor 在上面调度。任务板是这套流水线唯一的界面——一个只读的本地网页，顶栏是四个计数和本机配置入口，左栏是任务列表，中间是画布（ticket、决策、容器卡片和它们之间的阻塞关系），右栏是选中对象的详情，另有一个「本机配置」弹窗。

界面的两条主轴，读代码时要先分清：

- **phase（步骤）**：ticket 在自己内部走到哪一步，六个值 `queued / working / waiting / review / verify / landed`，由步骤标签（pill）表达。
- **lamp（灯）**：ticket 要外面做什么，四个值 `needs you / running / queued / done`，由 9px 的圆点（lamp）表达。

两者互不推导：一个 ticket 可以 `working` 却什么都不要，也可以 `landed` 却还需要人。**橙色只属于「需要你」这盏灯，不用在别处**；绿色是「在跑」，灯上和画布上流动的线用同一个绿。

这套 design system 是从已经在跑的生产代码里提炼出来的。产品当初没有照任何 design system 写，样式是一块一块加上去的，所以同一个零件常有几种写法、几种数值。这里把它们合并成一套可复用的视觉词汇；每一处合并都记在文末的 [Unifications](#unifications) 表里，产品代码之后照那张表跟着改。

## 来源

- **生产代码**：<https://github.com/chancheuklap/multi-model-workflow>，分支 `dev`，目录 `mmw-v2/board/page/`。
  - `styles/tokens.css`、`board.css`、`topbar.css`、`tasks.css`、`canvas.css`、`detail.css`、`settings.css` —— 全部外观数值的来源。
  - `board-logic.mjs`（phase / lamp / 事件词表）、`topbar.mjs`、`tasks.mjs`、`canvas.mjs`、`detail.mjs`、`settings.mjs` —— 决定页面上有哪些元素、用什么类名、在什么情况下变成什么状态。
  - `index.html` —— 页面骨架。
  - 该目录以外的文件与界面无关。
- **示例数据**：同一仓库 `prototypes/task-board/claude-design/data/`，五个区域在各种状态下的真实数据。
- **字体**：`fonts/` 下的 Geist、Geist Mono、Instrument Serif 是产品自带的 woff2，原样沿用，没有做任何替换。
- **图标**：`assets/icons/` 下两个 Lucide 图标，是产品顶栏内联的那两个。
- 项目根的 `github.md` 记着仓库关联与同步状态。

这套 design system 按**零件**组织，不按产品页面的区块组织。整条顶栏、整栏任务列表、画布、详情栏、本机配置弹窗都不在这里——它们是设计项目里的页面。

## 索引

| 文件 | 内容 |
| --- | --- |
| `styles.css` | 唯一入口，只有 `@import` |
| `tokens/fonts.css` | 三套字体的 `@font-face` |
| `tokens/colors.css` | 颜色、分隔线、底色、斜线纹理 |
| `tokens/typography.css` | 字体栈、五档字号、字重、行高、字距 |
| `tokens/spacing.css` | 间距档位 |
| `tokens/shape.css` | 圆角、阴影 |
| `components/*.css` | 零件，一个文件一类 |
| `cards/*.html` | Design System 标签页里的卡片 |
| `assets/icons/` | rotate-cw、settings（Lucide） |
| `fonts/` | Geist / Geist Mono / Instrument Serif woff2 |

零件清单（都是类名，不是 React 组件）：

`.board` · `.title` `.display` `.prose` `.meta` `.code` · `.brand` · `.lamp` · `.status-word` `.scan` `.spin` · `.pill` · `.eyebrow` `.section` · `.btn` `.iconbtn` `.link` · `.counter` · `.card` · `.row` `.task` · `.bar` · `.sel` · `.hatch-bar` `.hatch-swatch` · `.callout` · `.e-trunk` `.e-block` `.e-beam` `.e-port` `.legend` `.canvas-surface` · `.kv` · `.log-block` · `.toolbar` · `.empty` · `.readstate` `.links` `.counters`

## 内容基调 Content fundamentals

界面是**中英混排**的，而且分工固定：

- **机器的词用英文，原样不译**。phase 名（`working`、`verify`、`landed`）、lamp 名（`needs you`、`running`、`queued`、`done`）、事件名（`Worker started`、`Merge bounced`、`Criteria run`）、host/model/effort、`spec`、`ticket`、`map`、`landed` 计数，全部小写英文，不做首字母大写（事件名例外，它们是句首式大写）。
- **对人说的话用中文，短句，陈述语气**。`读 GitHub 失败 · 下面是 22:14 的数据（18 分钟前）`、`只有你能拍板；worker 先按默认值继续`、`没有带 mmw:map label 的 ticket。`
- 中文句子里出现的英文名词不加引号、不加空格以外的装饰：`加上 mmw:map label 的 ticket`。
- **不用第一人称**，也很少用「你」——只有在确实要人动手时才出现：`只有你能拍板`、`needs you`。
- **不用感叹号，不用 emoji**，没有任何一处。
- **不夸张、不安慰**。坏消息直说：`MMW 自己坏了，开它的 agent 已停下`、`合不进 dev：冲突在 board.css、canvas.css。等早上 triage`。
- **数字带单位和上下文**：`3/8 landed`、`1h31m`、`12 of 18 criteria met`、`waiting for a slot · since 02:18`。
- 分隔用 `·`（中点，两侧各一个空格），不用 `|` 也不用 `—`。
- 小标题一律小写英文加字距放大：`the night`、`blocked by`、`decision tickets · 3`。

## 视觉基础 Visual foundations

**纸与墨。** 整个界面是米白纸面（`--desk #e6e3df`）上的一叠白色面板（`--panel #ffffff`），画布是略冷的灰（`--canvas #ebecee`）加 28px 网点。文字是带蓝的深灰 `--ink #2d3142`，向下五档到 `--ghost`。**除了状态色，界面上没有第二种颜色。**

**颜色只在说状态时出现。** 橙 `#eb6c36` = 需要人；绿 `#22a06b` = 在跑；红 `#c9304f` = 被挡住；墨色实心 = 完成；空心描边 = 排队。四个步骤色（`working` 橄榄绿 / `waiting` 土黄 / `review` 紫 / `verify` 青）都是低饱和的，只出现在步骤标签上，三档一组：描边用原色，底用 .18 透明度，文字用加深版。蓝 `--focus #2e5aa8` 只做焦点圈，蓝灰 `--closeout #5e7a9b` 只做收尾卡片的左条。

**字体三套。** Geist 做全部界面文字（中文回落到苹方 / 黑体）；Geist Mono 做一切机器写的东西——编号、时间、host、model、计数、大写小标签；Instrument Serif 只出现在两个地方：字标的后半 `task board`，和空状态的大字。**衬线体从不做正文。**

**五档字号，之间没有别的**：9 / 11 / 13 / 18 / 24。9px 只给大写 mono 标签和卡片脚注，11px 给所有 mono 元信息与次要说明，13px 是正文，18px 是面板标题，24px 是空状态。字重三档 400 / 500 / 600。行高 1（标签）/ 1.3（标题）/ 1.45（正文）/ 1.6（成段说明）。

**边框三档、底色两档。** 分隔线 `.07`，默认描边 `.14`，悬停描边 `.30`；悬停底 `.04`，选中底 `.08`。全部是 `rgba(45,49,66,·)`——同一种墨色的不同浓度，没有灰色实色。

**悬停一律是「变深」**：描边 .14 → .30，或者底色透明 → .04，文字 muted → ink。**没有位移、没有缩放、没有颜色跳变。** 按下态在产品里没有单独定义——这是只读界面，能点的东西很少。焦点是 2px `--focus` 描边、2px 偏移，全局一条规则。

**选中态是墨色。** 卡片选中 = 描边变 `--ink` 加 `--shadow-2`；任务行选中 = 左侧 3px 墨色竖条加 `.08` 底；图标按钮选中 = 描边 `.30` 加墨色图标。选中从不换成彩色。

**圆角三档 + 圆头**：4（小按钮、关闭、警示条、内联代码）/ 8（按钮、下拉框、图标按钮、块）/ 12（画布卡片、弹窗）/ 999（步骤标签、计数、进度条、缩放条）。灯是正圆。

**阴影三档，都很轻**：浮在画布上的条 `0 2px 8px @.08`，选中的卡片 `0 4px 16px @.14`，遮罩上的弹窗 `0 24px 64px @.28`。**面板之间靠分隔线区分，不靠阴影。**

**面板里的内容只有四种块**：分节（`.section`，一条细线加一个大写小标题）、键值块（`.kv`，`.04` 灰底圆角，左列键右列值，全 mono）、事件块（`.log-block`，一个步骤一块，可开合，里面一行一个事件）、提示块（`.callout`，唯一带色条的）。没有第五种。

**画布上的线自成一套语汇。** 灰实线（`--line-grey`）是「包含」和「已经走过的路」；阻塞线的颜色说明这次等待处在什么状态——红＝还挡着，绿＝已放行且后面那张在跑（半透明，选中时加亮），灰＝已放行且完成；虚线＝循环依赖。线宽三档 1.5 / 1.8 / 2.4，透明度三档 .3 / .45 / .85。每条线末端有一个 3px 的圆点端口，颜色跟线走。绿色的光束顺着曲线跑，带两层绿色 drop-shadow，是界面上唯一的发光。

**没有渐变、没有图片、没有插画。** 唯一的「纹理」是 135° 斜线底纹（`--hatch`，6/12px @5%），它只有一个意思：**机器拒绝做这件事**——读取失败的顶栏、被拒绝的保存、`start` 会拒绝的配置格。底纹永远配 1px 墨色描边。

**透明与模糊**：只有画布上的图例条用 `rgba(255,255,255,.86)`（`--panel-veil`）压住底下的网点，弹窗遮罩用 `--scrim`。**全站没有 backdrop-filter。**

**动画只有两处**：卡片描边与阴影 .12s 过渡，读取中的 0.8s 旋转点。画布上的绿色光束沿曲线跑动是画布自己的事。两者都在 `prefers-reduced-motion` 下关掉。

**布局**：52px 顶栏，236px 左栏，画布占满剩下，340px 详情栏——详情栏没有选中对象时整列撤掉，画布把宽度收回去。所有列各自滚动，页面本身不滚。

## 图标 Iconography

产品几乎不用图标。全部图标只有两个，都是 **Lucide**，`stroke-width: 1.8`、圆头圆角、`fill: none`、`viewBox 0 0 24 24`，在顶栏右端内联为 SVG：

- `rotate-cw` —— 立刻重读 GitHub
- `settings` —— 本机配置

两个文件在 `assets/icons/`。图标尺寸 15px（`.iconbtn` 里）或 13px（`.iconbtn.sm` 里），颜色继承 `currentColor`（默认 `--soft`，悬停 `--ink`）。

其余位置用 **Unicode 字形**，不用图标：`▾` `▸` 展开收起，`×` 关闭，`−` `+` 缩放，`⇄` 循环依赖。下拉框的箭头是一个 10×6 的内联 data-URI SVG（1.4 描边），墨色版本给 `.bad` 状态。

**不用 emoji**，一处也没有。需要新图标时从 Lucide 取，保持 1.8 描边。

## 品牌标识

**产品没有图形 logo。** 标识就是字标：Geist 600 的 `MMW`（字距 .02em）+ Instrument Serif 斜体的 `task board`（`--soft` 色）+ Geist Mono 的仓库名（`--faint` 色）。需要放「logo」的地方就放这个字标，不要画标记。

---

## Unifications

代码里每一处不一致都合并成了一个值。左边是产品现在的写法，右边是这套 design system 的值——**产品代码照这张表跟着改**。

### 字号 → 9 / 11 / 13 / 18 / 24

| 零件或变量 | 代码里原来的值（类名） | 统一后 |
| --- | --- | --- |
| 大写 mono 小标签 | 9px（`.col-eyebrow` `.dp-eyebrow` `.dp-section-title` `.pv-eyebrow` `.pv-sec-title` `.pv-why-t` `.roles-head`）、8.5px（`.lane-label`） | 9px `--t-micro` |
| 步骤标签、卡片脚注 | 9.5px（`.pill` `.card-kind` `.card-run` `.card-count` `.pv-kind`） | 9px `--t-micro` |
| mono 元信息 | 10px（`.task-meta` `.task-count` `.legend` `.va-t` `.va-btime` `.pv-detail`）、10.5px（`.brand-repo` `.counter-sub` `.readstate` `.zoom-level` `.zoom-btn.text` `.rel-num` `.rel-state` `.pv-rel-n` `.pv-rel-s` `.pv-rel-hold` `.dp-elapsed` `.va-elapsed` `.dp-origin` `.pv-links` `.scan` `.hs-name` `.pv-run-k`） | 11px `--t-meta` |
| 次要说明与表单文字 | 11px（`.sheet-code` `.hs` `.pv-gh` `.pv-run-model` `.pv-run-v` `.role-what` `.pv-none` `.foot-quiet`）、11.5px（`.card-num` `.counter` `.dp-gh` `.va-bsum` `.va-x` `.pv-run-grade` `.role-bad` `.set-note`）、12px（`.sel` `.rel` `.pv-rel` `.pv-why` `.role-agent` `.sheet-sub` `.lamps-count` `.foot-status` `.refused`） | 11px `--t-meta` |
| 正文 | 12.5px（`.btn` `.dp-empty` `.canvas-empty-text` `.va-n`）、13px（`.board` `.card-title` `.task-title` `.status-word` `.va-word` `.brand-mark`）、14px（`.card-title.map` `.zoom-btn`） | 13px `--t-body` |
| 标题 | 17px（`.brand-name` `.pv-title`）、18px（`.dp-title` `.sheet-title`） | 18px `--t-title` |
| 关闭字形 | 16px（`.dp-close` `.pv-close`） | 18px `--t-title` |
| 弹窗根字号 | 16px（`.settings-root`） | 13px `--t-body`（并入正文，不再单独设根字号） |
| 空状态大字 | 22px（`.dp-empty-title`）、26px（`.canvas-empty-title`） | 24px `--t-display` |
| 行高 | 1.32（`.pv-title`）、1.5（`.va-x`） | 1.3 `--lh-title`、1.45 `--lh-body` |

### 字距

| 零件 | 原来 | 统一后 |
| --- | --- | --- |
| 大写 mono 标签 | .18em（列头、分节标题）、.16em（`.lane-label`）、.14em（`.pv-why-t`） | .18em `--track-wide` |
| 非大写 mono 标签 | .14em（`.roles-head`）、.08em（`.lane-label.warn`） | .14em `--track` |
| 字标与步骤标签 | .02em（`.brand-mark` `.pill`） | .02em `--track-loose`（不变） |

### 灰阶 → 边框三档、底色两档

| 用途 | 原来 | 统一后 |
| --- | --- | --- |
| 分节线 | `.07`（`--rule-2`） | `.07` `--rule-2`（不变） |
| 默认描边 | `.12`（`--rule`）、`.14`（`.card` `.zoom`）、`.18`（`.sel`）、`.2`（`.btn` `.pv-kind`）、`.24`（`.pill.queued`） | `.14` `--rule` |
| 悬停/强描边 | `.3`（`.lamp.hollow` `--line-grey`）、`.34`（`.gear:hover` `.card:hover`）、`.36`（`.sel:hover`）、`.38`（`.e-port.done`）、`.4`（`.btn:hover`） | `.30` `--rule-strong` |
| 悬停底 | `.025`（`.va-bhead`）、`.03`（`.task:hover`）、`.035`（`.pv-run` `.pv-detail`）、`.04`（`.chev:hover`）、`.05`（`.dp-close:hover` `.pv-close:hover`） | `.04` `--fill` |
| 选中底 / 填充 | `.05`（`.task.on`）、`.055`（`.va-bhead:hover`）、`.06`（`.zoom-btn:hover` `.code`）、`.08`（`.card-bar`）、`.10`（`.bar`） | `.08` `--fill-strong` |

### 圆角 → 4 / 8 / 12 / 圆头

| 原来 | 类名 | 统一后 |
| --- | --- | --- |
| 2px | `.hatch` | 4px `--r-sm` |
| 3px | `.code` | 4px `--r-sm` |
| 4px | `.readstate.failed` `.dp-close` `.pv-close` | 4px `--r-sm` |
| 5px | `.chev` `.pv-rel.hold` | 4px `--r-sm` |
| 6px | `.sel` `.hs` `.legend` `.dp-gh` `.pv-gh` `.pv-why` | 8px `--r-md` |
| 6px | `.refused` | 4px `--r-sm`（与 `.readstate.failed` 合成同一个警示条） |
| 7px | `.gear` `.btn` | 8px `--r-md` |
| 8px | `.va-block` `.pv-run` | 8px `--r-md`（不变） |
| 9px | `.pill` `.pv-kind` | 999px `--r-pill` |
| 10px | `.card` | 12px `--r-lg` |
| 12px | `.sheet` | 12px `--r-lg`（不变） |
| 12px | `.pill.big` | 999px `--r-pill` |
| 13px / 17px | `.counter` `.zoom-btn` `.zoom` | 999px `--r-pill` |
| 1px / 1.5px | `.card-bar` `.bar` `.bar-fill` | 999px `--r-pill` |

### 零件合并

| 零件 | 代码里原来的值（类名） | 统一后 |
| --- | --- | --- |
| 大写小标题 | `.col-eyebrow`（带 18/20/10 内距与两端对齐）、`.dp-eyebrow`、`.dp-section-title`、`.pv-eyebrow`、`.pv-sec-title`、`.roles-head`、`.lane-label`、`.pv-why-t` | `.eyebrow` + `.spread` / `.plain` / `.warn` / `.orange`（内距交给外层） |
| 分节 | `.dp-section` 14px/gap 9、`.pv-sec` 12px/gap 8、`.set-block.ruled` 16px/gap 10 | `.section` 16px / gap 8 |
| 面板标题 | `.dp-title` 18/1.3、`.pv-title` 17/1.32、`.sheet-title` 18/1.3 | `.title` 18/1.3 |
| 空状态标题 | `.dp-empty-title` 22px、`.canvas-empty-title` 26px | `.display` 24px |
| 状态词 | `.status-word`（默认 `--muted`）、`.va-word`（无默认色） | `.status-word` |
| 按钮 | `.btn` 32px/内距 14/12.5px、`.dp-gh` 内距 6·10/11.5px、`.pv-gh` 内距 3·8/11px | `.btn` 32px/内距 16 与 `.btn.sm` 24px/内距 8 |
| 图标按钮 | `.gear` 30×30 有框 r7、`.chev` 20×20 透明框 r5、`.zoom-btn` 26 高 r13 无框 | `.iconbtn` 32px + `.sm` 24px + `.bare` / `.round` / `.on` |
| 关闭按钮 | `.dp-close`、`.pv-close`（两者样式完全相同） | `.iconbtn.close` 24px |
| 链接 | `.dp-link`、`.linkbtn`（悬停变色 + 下划线转 currentColor）、`.pv-link`（悬停只变色） | `.link`，悬停变色 + 下划线转 currentColor |
| 列表行 | `.rel` 系（悬停变深 + 下划线）、`.pv-rel` 系（悬停只变深） | `.row` 系，悬停变深 + 下划线 |
| 类型 / 主机标签 | `.pv-kind`（9.5px 描边圆角 9）、`.hs`（11px 描边圆角 6 高 24） | `.pill.tag`（+ `.hot` / `.dashed`） |
| 主机离线态 | `.hs.missing`、`.hs.silent`、`.hs.down`、`.hs.unlaunchable`（四个类样式完全相同） | `.pill.tag.dashed` 一个类 |
| 卡片标题 | `.card-title` 13px、`.card-title.map` 14px、`.card-title.decision` 12px + muted、`.card-title.container` 单行省略 | `.card-title` 13px、`.decision` 只保留 muted、`.one-line` 单行省略 |
| 任务行选中 | `.task.on` + `.task-title.on` 两个类 | `.task.on .task-title` 一条后代规则 |
| 进度条 | `.bar` 3px + `.card-bar` 2px（各自的 fill 类） | `.bar` / `.bar.thin` + `.bar-fill` |
| 斜线警示条 | `.readstate.failed`（内距 3·8、r4）、`.refused`（内距 10·12、r6） | `.hatch-bar` / `.hatch-bar.block` |
| 画布图例 | `.legend` 内距 6·10、r6、gap 6·14、10px、`position:absolute` 定位写在类里 | `.legend` 内距 8·12、r8、gap 8·16、11px，定位交给外层 |
| 键值块 | `.pv-run`（内距 9·11、r8、底 .035、键列 88px、11px）、`.pv-detail`（内距 8·10、r6、底 .035、键列 78px、10px） | `.kv` 内距 8·12、r8、底 `--fill`、键列 88px、11px |
| 事件块 | `.va-block` + `.va-bhead`（底 .025 / hover .055、内距 7·10）+ `.va-body` `.va-ev` `.va-t` `.va-n` `.va-x` `.va-chev` | `.log-block` + `.log-head`（`--fill` / `--fill-strong`、内距 8·12）+ `.log-body` `.log-ev` `.log-t` `.log-n` `.log-x` `.log-chev` |
| 事件块警示边 | `rgba(235,108,54,.4)`（`.va-block.warn`） | `--orange-line` `.45` |
| 浮动工具条 | `.zoom` 34px 高、r17、内距 4、`--shadow-1` @.06、`.zoom-level` 42px、`.zoom-sep` | `.toolbar` 32px 高、`--r-pill`、`.toolbar-value` `.toolbar-sep` |
| 空状态 | `.dp-empty`（内距 40·26、12.5px）、`.canvas-empty`（内距 24、居中、12.5px）、`.tasks-empty`（内距 4·20、12px） | `.empty` / `.empty.center` / `.empty.inline` + `.empty-text` |
| 读取状态 | `.readstate` 10.5px、左内距 14 | `.readstate` 11px、左内距 12 |
| 灯数列表 | `.lamps-count` gap 14、12px + `.lc-item` + `.lc-n`（与 `.counter` 系重复） | `.counters.loose` + `.counter.plain` + `.counter-n` |
| 链接行 | `.dp-origin`（gap 0·6、10.5px、上外距 −4）、`.pv-links`（gap 0·6、10.5px） | `.links` gap 0·6、11px（外距交给外层） |
| 画布底 | `.canvas` 把网点、底色、`cursor: grab`、`overflow` 写在一个类里 | `.canvas-surface` 只管底色与网点（`--canvas-dot`），交互与滚动交给外层 |

### 数值

| 零件 | 原来 | 统一后 |
| --- | --- | --- |
| 步骤标签高度 | 18px（`.pill`） | 20px |
| 计数标签高度 | 26px（`.counter`） | 24px（与 `.btn.sm` 同档） |
| 下拉框高度 | 30px（`.sel`） | 32px（与 `.btn` 同档） |
| 卡片选中 | `.card.on` 边框 1.5px，四边内距各减 0.5px 补偿 | 边框仍 1px，只换墨色 + `--shadow-2`，删掉补偿内距 |
| 下拉框内描边 | `inset 0 0 0 0.5px`（`.sel.changed` `.sel.bad`） | `inset 0 0 0 1px` |
| 卡片内距 | `11px 13px 10px 15px`（`.card`） | `12px 12px 12px 16px` |
| 任务行内距 | `12px 18px 13px 17px`（`.task`） | `12px 16px` |
| 步骤标签底色 | `.18`（working、waiting）、`.16`（review、verify） | `.18` |
| 橙色浅底 | `.10`（`--orange-tint`）、`.16`（`.counter.hot:hover`）、`.18`（`.lamp.orange` 光晕） | `.10` `--orange-tint` / `.18` `--orange-tint-strong` |
| 斜线纹理 | 135° 6/12px @5%（`.readstate.failed` `.refused`）、135° 5/10px @7%（`.sel.bad`） | 135° 6/12px @5% `--hatch` |
| 阴影 | `0 2px 8px @.06`（`.zoom`）、`0 4px 16px @.14`（`.card.on`）、`0 24px 64px @.28`（`.sheet`） | `--shadow-1` `@.08` / `--shadow-2` / `--shadow-3` |
| 间距 | 3 / 5 / 7 / 9 / 11 / 13 / 14 / 15 / 17 / 18 / 22 / 26 / 28 / 30 / 34 | 归入 2 / 4 / 6 / 8 / 12 / 16 / 20 / 24 / 32 / 40 |
| 连线线宽 | 1.4（`.e-pulse`）、1.6（`.e-trunk` `.e-expand`）、1.8（`.e-block`）、2.2（`.e-block.flow`）、2.4（`.e-block.hot`）、2.6（`.e-beam.still` `.flow.hot`） | 1.5 `--stroke-thin` / 1.8 `--stroke` / 2.4 `--stroke-bold` |
| 连线透明度 | .28（`.e-block.flow`）、.4（`.flow.hot`）、.85（`.e-block.blocked` `.e-beam.still`） | .3 `--o-flow` / .45 `--o-flow-hot` / .85 `--o-solid` |
| 连线端点 | `rgba(45,49,66,.38)`（`.e-port.done`） | `--rule-strong` `.30` |
| 图例圆角 | 1.5px（`.legend-bar`） | 999px `--r-pill`（与进度条同档） |

### 硬编码颜色 → 变量

| 原来 | 类名 | 统一后 |
| --- | --- | --- |
| `#a8afbd` | `.lane-label` | `--faint` `#a3aabb` |
| `#8a92a6` | `.card-run` | `--soft` `#7a8399` |
| `#fbfbfa` | `.topbar` `.sheet-foot` | `--panel-2` |
| `#e6e3df` | `body` `.settings-root` | `--desk` |
| `#1f2231` | `.btn.primary:hover` | `--ink-hover` |
| `#ffffff` | `.pill.landed` `.btn.primary` | `--on-ink` |
| `rgba(255,255,255,.86)` | `.legend` | `--panel-veil` |
| `rgba(29,32,48,.46)` | `.scrim` | `--scrim` |
| `rgba(20,22,34,.28)` | `.sheet` 阴影 | `--shadow-3` |
| `#000000` | `.settings-root` | `--ink`（弹窗文字不再用纯黑） |
