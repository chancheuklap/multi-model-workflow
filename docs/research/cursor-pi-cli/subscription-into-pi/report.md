# 把 Cursor 订阅接到 pi CLI

查证日期：2026-08-25。下面说的 pi，是 Mario Zechner 那套终端 coding agent（命令是 `pi`），不是树莓派，也不是 Pi Network。Cursor 订阅指 Anysphere 的个人或团队付费计划，额度记在 Cursor 自己的 usage dashboard 上。

## 1. pi 本体接不了 Cursor 订阅

pi 的 `/login` 只接内置订阅。2026-08-24 的官方 `docs/providers.md` 列出的订阅是：ChatGPT Plus/Pro（Codex）、Claude Pro/Max、GitHub Copilot、xAI、OpenRouter、Radius。同一份文档没有 Cursor。README 的订阅列表更短，同样没有 Cursor。

官方给自定义 API / OAuth 的出口是扩展：`docs/custom-provider.md`。所以「把 Cursor 订阅接到 pi」不是改一份配置，而是装一个 pi 扩展，让它注册名为 `cursor` 的 provider。

## 2. 现在该用哪条路

2026 年社区走出三条路。认证方式和底层协议互不相同；装哪一个，pi 里就会出现一套 Cursor 模型。它们可以同时装在同一台机器上，但同一时刻通常只选一条来跑。

| 路径 | 认证 | 计费落在哪 | 协议 | 2026-08 是否还在更新 |
| --- | --- | --- | --- | --- |
| A. 官方 SDK 桥 | Cursor User API Key（或团队 service account key） | User API Key 记到该用户的计划；service account key 记到该团队。SDK 文档写：与 IDE、Cloud Agents 同一套定价、请求池和 Privacy Mode；花费出现在 usage dashboard 的 SDK 标签下 | `@cursor/sdk` 本地 agent loop（模型仍在 Cursor 云端） | 是，最新 2026-08-21 |
| B. 官方 CLI 包装 | `agent login`，或同一把 `CURSOR_API_KEY` | 走官方 Cursor CLI。CLI 认证文档没有单独写「CLI 额度池」；本次未找到官方句子说明 CLI 与 IDE 是否共用请求池 | 每个回合起 `agent` 子进程 | 主包 2026-06-18；fork 仓库 2026-08-08 还有 push |
| C. 逆向 AgentService | 浏览器 PKCE OAuth，或 `CURSOR_ACCESS_TOKEN` | 包 README 写的是订阅登录态本身；官方计费文档不覆盖这条路径 | 直连 `api2.cursor.sh` 的 gRPC / AgentService | 几个包停在 2026-03 到 2026-07 |

路径 A 是 Cursor 自己在 2026-04-29 开放的 SDK 用法：所有用户可用。SDK 文档的原句是：SDK 调用跟 IDE、Cloud Agents 走同一套定价、请求池和 Privacy Mode；User API Key 记到该用户的计划上（可能含计划内用量，也可能触发按量加购，以你账号当时的计费设置为准）。入口从编辑器换成一把 key，账还是记在同一份计划上。

路径 B 用的是 Cursor 官方 CLI。CLI 文档把浏览器登录标成推荐方式，API Key 留给脚本和 CI。扩展只是把 `agent` 当成子进程。

路径 C 自己实现 Cursor 内部协议。Cursor 服务条款 1.5(i) 禁止 reverse engineer、获取底层结构；可接受使用政策禁止 reverse engineer，也禁止绕过系统或保护措施。这些扩展能跑，但不在官方接入面里。可接受使用政策里还有一条禁止用 bot/script 等 automated or non-human means 访问服务——官方 SDK 和官方 CLI 本身就是脚本入口，论坛员工把官方 SDK 自动化当成预期用法，所以那一条不能单独拿来给路径 C 定罪。路径 C 真正踩到的是 reverse engineer / 底层结构这一层。

## 3. 推荐路径：官方 SDK + User API Key

包名 `pi-cursor-sdk`，作者 Mitch Fultz，仓库 [github.com/fitchmultz/pi-cursor-sdk](https://github.com/fitchmultz/pi-cursor-sdk)。npm 最新 **0.3.6**，发布时间 **2026-08-21**。过去一周约 1879 次下载，过去一个月约 8576 次，大约是第二名 CLI 包装器的十倍。GitHub 295 star，最后一次 push 2026-08-18。

它把 Cursor 的 agent loop 留在 `@cursor/sdk` 里，pi 负责选模型、会话、确认和显示。默认跑本地 runtime：文件在你的磁盘上读，推理仍走 Cursor 托管模型。

### 前置

- Node.js 22.19 或更高。
- pi 0.84.0 或更高。
- 一把 Cursor **User API Key** 或团队 **service account key**。Team Admin API Key 被 Cursor SDK 拒绝。

### 拿密钥

官方文档写：打开 [Cursor Dashboard → API Keys](https://cursor.com/dashboard/api)，建一把 user key。DeepakNess 2026-05-24 的截图指向 `/dashboard/integrations`。两边都指向 User API Key；本次没有登录 Dashboard 核对当前菜单名。Admin API 文档把 **Admin** 密钥格式写成 `crsr_` 前缀；User API Key 是否同一格式，本次没有从 User-key 文档或 Dashboard 核对。

不要用 Cursor 桌面登录，也不要用 `agent status` 里那份会话。`pi-cursor-sdk` README 写明：它**不**复用 Agent CLI 登录、Desktop 登录、或 `agent status` 显示的订阅/OAuth 状态。

### 安装和登录

```bash
pi install npm:pi-cursor-sdk
pi --model cursor/grok-4.6
```

进入 pi 之后：

1. `/login`
2. 选 **Use an API key**
3. 选 **Cursor**
4. 把 User API Key 贴进去

密钥写进 pi 自己的 `~/.pi/agent/auth.json`。也可以不进交互登录：

```bash
export CURSOR_API_KEY="your-key"
pi --model cursor/grok-4.6
```

如果启动时还没有 key，扩展会先注册一份兜底模型列表，让 `/login` 仍然能打开。登录后再跑 `/cursor-refresh-models`，从 Cursor SDK 拉完整模型目录。

### 冒烟（来自包 README，本次未在本机执行）

```bash
pi --list-models cursor

pi --model cursor/grok-4.6 --cursor-no-fast --no-session --mode json \
  -p "Reply exactly PI_CURSOR_MODEL_OK and nothing else."
```

期望：助手正文正好是 `PI_CURSOR_MODEL_OK`。缺 key 时，pi 会提示走 `/login`、`CURSOR_API_KEY` 或 `--api-key`。

### 选模型

`/model` 里挑，或命令行写 `cursor/<id>`。README 把 `cursor/grok-4.6` 标成当前推荐默认。Composer 2 / 2.5 可能默认开 fast；要关 fast，用 `--cursor-no-fast` 或模型别名 `:slow`。思考力度用 pi 的 `--thinking` 或模型后缀 `:medium` / `:high` / `:xhigh` / `:max`，扩展再映射到 Cursor SDK 的 `reasoning` / `effort` / `thinking` 参数。

### 别人跑过的用量

DeepakNess 在 2026-05-23 发过截图：Cursor $20 计划，用这套跑 Composer 2.5 Fast，1200 万 token，只占当月额度的 0.9%。他说关 fast 会更省。这是一个人、一个计划、一个星期的观测，不是官方费率表。官方说法只有：SDK 与 IDE 共用请求池，花费出现在 usage dashboard 的 SDK 标签下。

2026-08 仍有人在用。X 上 @geoqiao（2026-08-16）写自己用 `pi-cursor-sdk` 同时花公司 Cursor 额度和 Claude 额度；@hey_joe79（2026-08-20）写 “I use cursor subscription in pi via cursor sdk”。同周也有人报 API key 反复失效（@claytonlz，2026-08-20）。

## 4. 次选：包装官方 Cursor CLI

如果你已经在用 Cursor 官方 CLI（命令名 `agent`），不想再管第二把 SDK key，可以走这条。

当前更完整的包装是 [`@akepka/pi-cursor-cli-provider`](https://www.npmjs.com/package/@akepka/pi-cursor-cli-provider)（fork 自 `@netandreus/pi-cursor-provider`）。npm 最新 **0.10.1**，发布时间 **2026-06-18**；GitHub 仓库 `Strus/pi-cursor-cli-provider` 最后 push **2026-08-08**。过去一个月约 782 次下载。原包 `@netandreus/pi-cursor-provider` 停在 2026-02-21 的 0.1.4。

作者 Kepka 写选择 CLI 包装的理由：逆向 Cursor 内部 API「太 hacky」；他自己试过 ACP（Agent Client Protocol），认为 ACP 只暴露部分模型，且每种模型只有一种思考档。CLI 是 Cursor 自己提供的订阅入口。

### 步骤

1. 安装 Cursor CLI：`curl https://cursor.com/install -fsS | bash`
2. 登录：`agent login`（浏览器），或 `export CURSOR_API_KEY=...`
3. 装扩展：

```bash
pi install npm:@akepka/pi-cursor-cli-provider
```

4. 在 pi 里用 `/model` 选 Cursor 模型。`@akepka` 的 README 只写启动时自动发现模型；上游 `@netandreus` 写明发现命令是 `agent models`。本次没有打开 `@akepka` 源码核对它现在是否仍调用同一条命令。

每个 pi 回合会起一个 `agent --print --yolo --output-format stream-json` 子进程。第一回合送完整 transcript；之后用 `--resume <session-id>` 只送最新一句。工具执行发生在 Cursor CLI 里，不是 pi 的 read/edit/bash。token 计数是估计值，因为 CLI 不在回合结束时报精确用量。

第三条相关包装是 [`@0xkobold/pi-cursor`](https://www.npmjs.com/package/@0xkobold/pi-cursor)：用 `agent acp`（JSON-RPC over stdio）把任务委托给 Cursor Agent，而不是把 Cursor 注册成 pi 的模型 provider。停在 2026-03-24 的 0.1.0。ACP 模型覆盖不够用，是 `@akepka` 作者 Kepka 在自己 README 里的判断，不是这个包的作者声明。

## 5. 不推荐作默认：逆向 AgentService

这些扩展让你在 pi 里 `/login cursor`，浏览器走 Cursor 的 PKCE，然后本地把 OpenAI 形的请求译成 Cursor 的 protobuf/HTTP2。

| 包 | 最新 | 发布 | 做法 |
| --- | --- | --- | --- |
| `pi-oauth` | 0.0.1 | 2026-05-26 | `/login` → Use a subscription → Cursor；直连 AgentService，自称无 localhost 代理 |
| `@offbynan/pi-cursor-provider` | 0.6.0 | 2026-07-08 | fork `ndraiman/pi-cursor-provider`，本地 OpenAI 兼容代理 → `api2.cursor.sh` |
| `pi-cursor-provider`（ndraiman） | 0.1.11 | 2026-04-09 | 上游：PKCE + gRPC 代理 |
| `pi-cursor-oauth` | 0.2.0 | 2026-03-24 | `/login cursor`，`CURSOR_ACCESS_TOKEN` 兜底 |

`pi-oauth` 的 README 写：Cursor 打开 `cursor.com/loginDeepControl`，轮询登录，再调 `GetUsableModels`。协议代码注明来自对 Cursor 协议的研究（点名 `Yukaii/yet-another-opencode-cursor-auth`），并对照本地 `cursor-agent` CLI 包校验。`ndraiman` 的 README 写 OAuth 和 gRPC 代理改编自 `ephraimduncan/opencode-cursor`。

条款上的对应关系（不是法律意见，是原文对照）：

- [Terms of Service 1.5(i)](https://cursor.com/terms-of-service)（页面标注更新 2026-08-13）：禁止 reverse engineer、disassemble、获取 source / object code / underlying structure。
- [Acceptable Use Policy](https://cursor.com/acceptable-use-policy)（页面标注更新 2026-08-11）：禁止 reverse engineer；禁止绕过系统或保护措施；禁止用 bot/script 等 automated or non-human means 访问服务。

官方 SDK 和官方 CLI 是 Cursor 自己提供的自动化入口。路径 C 是社区对内部协议的再实现。r/PiCodingAgent 在 2026-05 有人转述「Cursor mentioned this is not allowed」——转述，不是官方帖，原文未找到。

## 6. 对照与未核实

过去一个月（2026-07-26 到 2026-08-24）npm 下载：

| 包 | 月下载 | 周下载（08-18–08-24） | 最新发布 |
| --- | --- | --- | --- |
| `pi-cursor-sdk` | 8576 | 1879 | 2026-08-21 |
| `@akepka/pi-cursor-cli-provider` | 782 | 182 | 2026-06-18 |
| `@netandreus/pi-cursor-provider` | 307 | — | 2026-02-21 |
| `@offbynan/pi-cursor-provider` | 298 | 50 | 2026-07-08 |
| `pi-cursor-provider` | 148 | — | 2026-04-09 |
| `pi-cursor-oauth` | 111 | — | 2026-03-24 |
| `pi-oauth` | 89 | — | 2026-05-26 |

下载量不是质量证明。它只说明：在上面列出的这些 npm 扩展里，2026 年 8 月的下载以 `pi-cursor-sdk` 为主。没装进 npm、或走别的安装方式的用法，这张表看不到。

**未在本机核实：**

- 没有执行 `pi install`，也没有用真实 Cursor 密钥跑第 3 节的冒烟命令。
- 没有打开登录后的 Cursor Dashboard，所以无法裁定密钥页现在叫 API Keys 还是 Integrations。
- 没有核对这些扩展是否违反你账号适用的 Cursor 合同；第 5 节只对照公开条款文本。
- Reddit 帖 `r/PiCodingAgent` 的完整评论树本次拉取返回 403，细节来自搜索引擎摘要。
