# unlazy

源目录：`mmw-v2/upstream-unlazy/`

上游是 `Leonxlnx/unlazy`（MIT），独立于另外两个 subtree，自己一个：

```
git subtree pull --prefix mmw-v2/upstream-unlazy https://github.com/Leonxlnx/unlazy main --squash
```

整个仓库都拉进来，verify-ticket 只用其中的判定引擎：`scripts/gate-check.mjs`、`scripts/gate-lint.mjs`、`scripts/lib/`。技能目录里的 `mmw-v2/skills/verify-ticket/scripts/gate-check/` 只放指向这三样的相对 symlink（`../../../../upstream-unlazy/scripts/…`）。host 装的是技能目录的 symlink，内层 symlink 按技能目录的真实位置解析，所以能走到 subtree。`stop-hook.mjs`、`install-hooks.mjs`、`dispatch-check.mjs` 不接进技能目录，持有 verify-ticket 的 agent 看不到它们。上游把这三样改名、合并或拆分时，跟着改 symlink。

## 总原则

上游面对的是一份随别人的仓库一起到来的账本：所以每条 `CHECK:` 先要人审批一次，多个 agent 按 scope 分工、抢 lease，Stop hook 拦住没做完就想停的 agent。

我们的 `CHECK:` 是本仓库主 agent 写在用户自己 tracker 的票上的，每次运行从票正文生成一份临时账本，只用判定：跑 `CHECK:`、判两个条件、写 `EVIDENCE:`、打印汇总行。

所以取舍按改动落在哪一层分：

- 改**判定本身**（判据状态、exit 0 与 `EXPECT:` 两个条件、evidence 与定义的绑定、超时、输出上限、regex worker、读账本的防护）→ **收上游**。
- 改**审批** → **弃上游**，那套代码在这里保持删除。
- 改 scope、lease、Stop hook、安装器、模板 → 照收，我们不用，也不接进技能目录。
- 改**失败要不要写 evidence** → **弃上游，保我们的**。

## 逐段意图

### scripts/gate-check.mjs

| 段落 | 我们的意图 |
| --- | --- |
| 审批机制：`--approve`、`~/.unlazy/approved` 目录及其属主与 no-follow 检查、每条判据的审批记录和锁、`APPROVAL REQUIRED` / `NOT RUN` 路径 | 整套删掉，`CHECK:` 写什么跑什么。理由见下面「审批为什么删」。运行时 oracle 签名留着，它在判据运行途中被改时丢弃那次结果；函数名 `oracleSignature`，上游叫 `approvalOracleSignature`。上游再改审批代码 → 弃上游 |
| `insertOrUpdateEvidence`：判据没有 `EVIDENCE:` 行时插在哪 | 插在 `attrEnd`，即整条命令之后；命令写在围栏代码块里时，在围栏的收尾行之后，不插进命令中间 |
| 写回循环里失败的那一支；`failureEvidenceFor` | 失败也写 evidence，不写 `pending`：exit code（有 signal 或 error 时一并写）、`EXPECT:` 是否匹配、输出的 sha256 与字节数、shell、cwd、`path=` 指纹，最后是控制台 `FAIL` 行同样的输出摘要。字段和顺序与通过行一致，不带 `automatic-evidence` 前缀：那个前缀把一次通过绑定到产生它的定义，失败不通过任何东西。上游只在判据已勾或 evidence 过期时才写失败（`mustWriteFailure`），写的是 `pending`；这个条件在这里删掉，每次失败都写。理由：reverify 把一条 met 的判据跑红时若写 `pending`，红了一次不复现就再也解释不了，因为输出只在没人留存的 stdout 上（2026-09-10 实测，#320、#327）。判定不变：勾选框仍是唯一权威，`gateState` 和 `verify-ticket.py` 的计数都只把已勾的判据算作 met |

### scripts/lib/gates.mjs

| 段落 | 我们的意图 |
| --- | --- |
| `parseGates` 读 `CHECK:` 的那一段 | 紧跟在 `CHECK:` 下面的围栏代码块就是这条命令；其他围栏照上游整块跳过。上游每个属性只读一行，其余悄悄丢掉，多行命令会只把前半截交给 shell。`CHECK:` 下面接一行裸文本报错，并指向围栏代码块的写法，读者不用猜命令在哪结束。每条判据另记 `attrEnd`：最后一个属性之后的行号，命令写在围栏里时是围栏收尾行之后 |

### scripts/gate-lint.mjs

| 段落 | 我们的意图 |
| --- | --- |
| `manual-gate` | 从 warning 改为 error，并说明判据该去哪。上游允许一份账本里有人工判定的判据，超过一半才警告；这里一条没有 `CHECK:` 的判据只有写它的人自己能判，而验收标准存在就是为了避免这个。需要判断的交给 code review，它在另一个会话里跑；只有用户自己能看的，开一张单独的票 |

### tests/run-tests.mjs

| 段落 | 我们的意图 |
| --- | --- |
| `STOP_HOOK`、`INSTALL` 常量和用到它们的 15 条 `hook:` / `install:` 测试；runner 注入的 `--approve` 与 `UNLAZY_APPROVAL_DIR` | 删掉。它们测的是不接进技能目录的 Stop hook 和安装器，而且要靠审批才能跑 |
| 文件末尾两条 `evidence:` 失败记录测试 | 本仓加的，钉住上面「失败也写 evidence」 |
| 文件末尾四条：定义摘要的 golden vector 与状态表、改了 `CHECK:` 后旧 evidence 过期、长 transcript 截不断摘要、stdout 与 stderr 合并算输出上限 | 取自上游 `tests/hardening-tests.mjs`，去掉审批步骤，失败时期望写失败记录而不是 `pending`。上游改这几条原测试 → 跟着改这里的副本 |

上游 34 条里留 19 条，加上面 6 条，共 25 条。

### tests/lint-tests.mjs

| 段落 | 我们的意图 |
| --- | --- |
| `lint: shipped leaf and node templates satisfy the documented size policy` | 删掉。`templates/gates-leaf.md` 和 `gates-node.md` 里有人工判定的判据，这里 lint 报错；本仓的账本从票正文生成，从不用模板 |
| 三条用无命令判据演示「只是建议」的测试 | 改为断言它报错，并改用一份只有 warning 的账本 `WARNING_ONLY`；另加一条，钉住两种模式下都报错 |
| 终端转义（文本与 JSON）、字段膨胀有上限、finding 数量有上限这四条 | 给判据补上 `CHECK:` 和 `EXPECT:`，让它们仍只有 warning。finding 数量那条的总数随之变为 80 条 warning、省略 16 条（上游无命令判据时是 241 和 177） |

上游 29 条，删一条、加一条，共 29 条。

### 测试入口

`mmw-v2/tests/verify-ticket/run.sh` 只跑 `tests/run-tests.mjs` 和 `tests/lint-tests.mjs`。其余几份测试（`contract-tests.mjs`、`dispatch-tests.mjs`、`hardening-tests.mjs`、`stress-tests.mjs`、`self-check.mjs`）覆盖 scope、lease、Stop hook 与安装器、审批、Windows 文件身份和技能包结构，其中依赖审批的在这里会失败，不跑。

## 审批为什么删

上游的安全边界是：有人读过一份继承来的账本并审批一次（上游 `SECURITY.md` 第 3 行），因为在那里账本随别人写的仓库一起到来。这里的 `CHECK:` 是主 agent 写在用户自己 tracker 的票上的，`--lint` 在票发出之前检查写法，而票就是用户读的东西。没有任何东西是继承来的，所以没人读过那些审批记录：每次运行都传了 `--approve`。也没有东西复用它们：记录以账本的绝对路径为键，而账本每次都是新的临时文件。剩下的只有仓库外的一个目录，每个 host 的沙箱都得为它放宽。

## 未改

`README.md`、`SKILL.md`、`SECURITY.md`、`CHANGELOG.md`、`references/`、`templates/`、`agents/`、`research/`、`scripts/` 里除上面三个文件以外的脚本、`tests/` 里除上面两份以外的测试。
