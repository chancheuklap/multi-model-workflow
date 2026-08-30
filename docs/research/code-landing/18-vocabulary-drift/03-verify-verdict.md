# 03 — 跑验收标准、复验、VERDICT

审计范围：`CONTEXT.md`、`mmw-v2/skills/verify-ticket/`（SKILL.md、scripts/、tests/）、`mmw-v2/agents/verifier/`、`mmw-v2/agents/assemble.py`、`mmw-v2/upstream/skills/engineering/implement/SKILL.md`、`mmw-v2/skills/dispatch/SKILL.md` 与 `models.md`、`mmw-v2/merge-notes/implement.md`。

两处已实测通过、不算发现，先记下：`python3 mmw-v2/agents/assemble.py --check` 退出 0（`mmw-v2/agents/verifier/out/` 与 `body.md` + `agent.json` + `models.md` 一致）；`gate-check/tests/run-tests.mjs` 与 `lint-tests.mjs` 各 19/19 通过，与 `UPSTREAM.md:24`、`UPSTREAM.md:25` 声明的 19 例吻合。

---

## 发现 1：`hook.py pretool` 到底做什么——CONTEXT.md 说它跑 `--closeout` 的 dry run 并按退出码放行，脚本说它什么都不跑、只拒绝

- 类型：脚本与文档不符（并波及两处代码注释）
- 后果：读 CONTEXT.md 的人会以为 `gh issue close` 被拦时脚本已经替他判过草稿，于是去找「哪一条没过」；实际拿到的是一句固定话术，草稿从未被读过。反过来，`verify-ticket.py` 与 `test_closeout.py` 把「首行要自带问题总数」这条设计建在「hook 转述 closeout 的 stderr 首行」之上，而这条转述链根本不存在。
- 证据：
  - `CONTEXT.md:378` 「The host-side enforcement of the closing gate: when a command tries to close a ticket or swap its label, it runs the dry run and refuses on a non-zero exit.」
  - `mmw-v2/skills/verify-ticket/scripts/hook.py:14-16` 「It refuses rather than checks. A worker typing `gh issue close` has by definition not been through `--closeout`, so there is no draft of its to check; a gate that guessed one and let the command through when the guess passed would produce exactly the outcome it exists to prevent」
  - `mmw-v2/skills/verify-ticket/tests/test_hook.py:4-5` 「The gate runs no command and reads no file, so there is nothing here to stub out.」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:820-821` 「The pretool hook that stands between a worker and `gh issue close` relays only the first line of this, so the first line carries the count and the way to read the rest.」
  - `mmw-v2/skills/verify-ticket/tests/test_closeout.py:402-403` 「The pretool hook between a worker and `gh issue close` relays only stderr's first line, so that line has to say how many problems there are and how to read the rest.」
- 建议正名：以 `hook.py:14-16` 为准改 `CONTEXT.md:378`（「拒绝，不检查」）。`verify-ticket.py:820-821` 与 `test_closeout.py:402-403` 里「hook 转述 closeout stderr 首行」的理由要换成真实理由（宿主自身对 stderr 的截断，或就写「首行自足是给人读的」），待用户拍板选哪条理由。

---

## 发现 2：`--preflight` 到底核对几项——四、五、六三个数并存

- 类型：分岔
- 后果：worker 按 `implement/SKILL.md:8` 只预期四项，被第五项（`ready-for-agent` 标签缺失）或第六项（票在别人名下）挡住时，找不到对应的说法，会怀疑脚本坏了；写票的人按 `CONTEXT.md:326` 的五项去准备票，仍会漏掉标签这一项。
- 证据：
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:8` 「It checks the branch, the working tree, the ticket's state and its blockers, and claims the ticket for you when all four pass.」（四项）
  - `CONTEXT.md:326` 「The start-of-work guard. Checks branch, working tree, ticket state, blockers and assignee; only then claims the ticket.」（五项，无标签）
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:752-753` 「Every one of these ends in `stop`. The four conditions are set up before a worker exists」（四项）
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:761-787` 实际六个 `NOT_READY:`：branch、dirty、state、`"ready-for-agent" not in labels`、blockers、assignee
  - `mmw-v2/skills/verify-ticket/tests/test_preflight.py:105` 「    ALL_SIX = (」，而同文件 `test_preflight.py:1` 「The opening guard: four conditions」、`test_preflight.py:99` 「Each of the four conditions is set up before a worker exists」
- 建议正名：以脚本的六项为准（branch / 工作区 / 票状态 / `ready-for-agent` 标签 / blockers / assignee），同步改 `implement/SKILL.md:8`、`CONTEXT.md:326`、`verify-ticket.py:752`、`test_preflight.py:1` 与 `:99`。

---

## 发现 3：`ALL MET` 与 `HANDOFF REQUIRED:` 各有两种语法——一种是 gate-check 的汇总行，一种是收尾评论的首行

- 类型：命名撞车 + 分岔
- 后果：`self-run` 评论的第二行就是 `ALL MET (1 met)` / `HANDOFF REQUIRED: 1 abandoned (met: 0, unmet: 1)`；worker 照抄它作为草稿首行，`--closeout` 一定拒绝——`ALL MET` 要求逐字相等，`HANDOFF REQUIRED:` 要求的是另一套括号内容。两种写法同名同前缀，读者无从分辨自己手上的是哪一种。
- 证据：
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-check.mjs:685` 「  console.log("ALL MET (" + totalMet + " met" + verifyNote + ")" + where);」
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-check.mjs:689-690` 「  console.log("HANDOFF REQUIRED: " + totalAbandoned + " abandoned (met: " + …」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:35` 「SUMMARY_RE = re.compile(r"^(ALL MET|UNMET:|HANDOFF REQUIRED:)")」——这两行原样被抄进 `self-run` / `reverify` 评论（`verify-ticket.py:713`、`:735-743`）
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:437` 「    if first != "ALL MET" and not handoff:」，`verify-ticket.py:49-50` 「HANDOFF_RE = re.compile(\n    r"^HANDOFF REQUIRED:\s*(\d+)\s+abandoned\s*\(([^)]*)\),\s*(\d+)\s+unmet,\s*(\d+)\s+met of\s*(\d+)\s*$")」
  - `CONTEXT.md:283-288` 只登记了收尾评论那一种：「**`ALL MET`**: One of the two possible first lines」「**`HANDOFF REQUIRED`**: The other first line, in full `HANDOFF REQUIRED: <n> abandoned (<kinds>), <m> unmet, <k> met of <total>`」
  - 实测一条真实全过 `self-run` 评论：第一行 `self-run`，第二行 `ALL MET (1 met)`
- 建议正名：待用户拍板。两条路——（甲）在 `CONTEXT.md`「Running the criteria」下补一个词条，把 gate-check 的汇总行单独命名（例如 `gate-check 汇总行`）并写清它与收尾评论首行不是一回事；（乙）在 `verify-ticket.py` 里给汇总行加前缀再写进评论，让两者字面不再相同。

---

## 发现 4：`UNMET: <n> (met: <m>)` 被当成「`self-run` / `reverify` 评论的第二行」，但全过时第二行是 `ALL MET (<n> met)`，`board.py` 因此数不出 `<met>/<total>`

- 类型：断点 + 脚本与文档不符
- 后果：一张票全部标准通过、pane token 又已过期（TTL 24h）时，看板的 `ac` 列显示 `-`，看板读者以为这张票一条都没跑。测试用的是一条 gate-check 永远不会打印的假评论，所以这条断点测不出来。
- 证据：
  - `CONTEXT.md:227-228` 「**`UNMET: <n> (met: <m>)`**:\nThe second line of a `self-run` or `reverify` comment.」
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-check.mjs:684-686` 「if (effectiveUnmet === 0 && totalAbandoned === 0) {\n  console.log("ALL MET (" + totalMet + " met" + verifyNote + ")" + where);\n  process.exit(0);」——全过时根本不走 `UNMET:` 那一支（`gate-check.mjs:695-696`）
  - `mmw-v2/skills/dispatch/scripts/board.py:220-228` 「def counted_ac(ticket: dict) -> str:\n    \"\"\"`<met>/<total>` off the newest self-run or reverify comment, or `-`.\"\"\"」，其中 `board.py:199` 「UNMET_RE = re.compile(r"^UNMET:\s*(\d+)\s*\(met:\s*(\d+)\)")」
  - `mmw-v2/skills/dispatch/tests/test_board.py:67-69` 「SELF_RUN_ALL_MET = "\n".join([\n    "self-run",\n    "UNMET: 0 (met: 5)",」——这一行 gate-check 不会打印
  - 实测：把真实的全过评论喂给 `board.counted_ac`，返回 `'-'`
- 建议正名：以 gate-check 为准。`CONTEXT.md:227-228` 改成「第二行是 gate-check 的汇总行，三种形状之一」；`board.py:199` 的正则要同时认 `ALL MET (<n> met)` 与 `HANDOFF REQUIRED: … (met: <m>…)`；`test_board.py:67-69` 的样本换成真实输出。

---

## 发现 5：VERDICT 的 `level` 有五个值、被称作「verifier 唯一要判的那一项」，但整条流水线没有任何一处读它

- 类型：断点
- 后果：一张票可以带着 `verifier-failed` 或 `type-check-only` 的 VERDICT 以 `ALL MET` 关掉。`CONTEXT.md:258` 承诺「改行为的票不能靠 type-check-only 过」，但没有任何门执行这句；`implement/SKILL.md:33` 又禁止第二次派 verifier，所以修完之后也没有新的 VERDICT 来覆盖旧的。写 level 的人以为它是判据，读票的人以为票上的 level 代表最终状态，两边都会误判。
- 证据：
  - `CONTEXT.md:245-246` 「**level**:\nThe one field of `VERDICT` the verifier has to judge, chosen from five values.」；`CONTEXT.md:257-258` 「**`type-check-only`**: A level: only a type check passed. A ticket that changes behaviour does not pass on this.」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:51` 「VERDICT_RE = re.compile(r"^VERDICT\s+([0-9a-fA-F]{7,40})\b")」——只捕获 commit，`last_verdict`（`verify-ticket.py:421-428`）只返回 commit
  - `mmw-v2/skills/verify-ticket/SKILL.md:69` 「`ALL MET` is held to two more: the ticket carries the verifier's `VERDICT`, and the draft accounts for every commit since it.」——只要求「有一条 VERDICT」，不看 level
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:33` 「If it reports failures, fix and rerun step 1; never dispatch the verifier a second time.」
- 建议正名：待用户拍板。（甲）承认 level 是给人读的，把 `CONTEXT.md:258` 那句「A ticket that changes behaviour does not pass on this」改成不像强制条款的写法；（乙）让 `draft_problems`（`verify-ticket.py:510-521`）在首行 `ALL MET` 时同时检查 level，并给 `verifier-failed` 之后的重跑安排一条产生新 VERDICT 的路。

---

## 发现 6：`self-reported` 只在 CONTEXT.md 里存在，而且和脚本给出的唯一出路互相矛盾

- 类型：幽灵词 + 断点
- 后果：worker 派不出 verifier 时，照 CONTEXT.md 会自己写一条 `VERDICT … by self-reported`；`--closeout` 认这条 VERDICT，于是票以 `ALL MET` 关掉，而「不是自己判自己」这条底线正好被绕开了。脚本本意是让它走 `HANDOFF REQUIRED`。
- 证据：
  - `CONTEXT.md:269-270` 「**`self-reported`**:\nWhat the `by` field of `VERDICT` degrades to when no subagent could be dispatched.」（全仓仅此一处）
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:513-516` 「problems.append("the ticket carries no `VERDICT <commit> <level> …` line, so nothing but this ticket's own author says the work is done. Dispatch the verifier; if it cannot run, close out as `HANDOFF REQUIRED` instead and say so")」
  - `mmw-v2/skills/verify-ticket/SKILL.md:70-72` 「`HANDOFF REQUIRED` is held to neither — it claims nothing was finished, so it is the way out of anything you cannot fix yourself, including a verifier that never ran.」
- 建议正名：删掉 `CONTEXT.md:269-271` 整个词条；派不出 verifier 的唯一出路是 `HANDOFF REQUIRED`。

---

## 发现 7：VERDICT 的 commit 长度——文档要求 40 位全长，正则收 7 位起，测试用 15 位

- 类型：脚本与文档不符
- 后果：verifier 若写了短 commit，脚本照收；但 `Post-verdict:` 那一关靠 `git rev-parse HEAD` 的前缀匹配判断「verdict 是否还在 HEAD 上」（`verify-ticket.py:517`），短 commit 提高了误判为「已在 HEAD」的概率，于是该写的 `Post-verdict:` 不写也能过。
- 证据：
  - `CONTEXT.md:242` 「The verifier's judgement comment, written `VERDICT <full 40-character commit> <level> by <model> — <one line>`.」
  - `mmw-v2/agents/verifier/body.md:21` 「`<commit>` is all 40 characters of what `git rev-parse HEAD` just printed」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:51` 「VERDICT_RE = re.compile(r"^VERDICT\s+([0-9a-fA-F]{7,40})\b")」
  - `mmw-v2/skills/verify-ticket/tests/test_closeout.py:247` 「        comments = ("VERDICT 0000000deadbeef unit-test-verified by opus",」（15 位）
- 建议正名：以 `body.md:21` 的 40 位为准，把 `VERDICT_RE` 收紧成 `[0-9a-fA-F]{40}`，并改掉 `test_closeout.py:247` 的短 commit 样本。

---

## 发现 8：verifier 被称为「read-only subagent」，但它装配出来的三个宿主配置都是可写档

- 类型：命名撞车
- 后果：`read-only` 在 `assemble.py` 里是 `sandbox` 键的一个字面值，verifier 用的是另一个值。读 CONTEXT.md 的人会以为 verifier 靠沙箱保证不改仓库，于是不把 `body.md` 里那四条禁令当回事；实际那四条禁令是唯一的保证。
- 证据：
  - `CONTEXT.md:27-28` 「**verifier**:\nThe read-only subagent a worker dispatches to re-run every acceptance criterion and write one `VERDICT`.」
  - `mmw-v2/agents/verifier/agent.json:4` 「  "sandbox": "workspace-write",」
  - `mmw-v2/agents/verifier/out/cursor.md:5` 「readonly: false」；`mmw-v2/agents/verifier/out/grok.role.toml:2` 「default_capability_mode = "execute"」；`mmw-v2/agents/verifier/out/codex.toml:6` 「sandbox_mode = "workspace-write"」
  - `mmw-v2/agents/assemble.py:16-18` 「agent.json 顶层可选键 sandbox 决定 Cursor、Codex、Grok 三家的沙箱档位，缺省 read-only。写 workspace-write 的 agent 才跑得起会写文件的命令」
  - 对照 `mmw-v2/agents/advisor/out/cursor.md:5` 「readonly: true」——真正的 read-only subagent 长这样
- 建议正名：`CONTEXT.md:28` 去掉 read-only，改用 `body.md:35` 那句自己的措辞（环境可改、仓库不可改）。

---

## 发现 9：linter 的问题标签，CONTEXT.md 列了五个，其中三个不是真标签，真标签漏了八个

- 类型：脚本与文档不符
- 后果：写票的人按 `CONTEXT.md:357` 去 grep `[cycle]`、`[dangling]` 找不到；看见 `[unexplained-edge]`、`[tautological-check]`、`[weak-expect]`、`[path-read-as-regex]`、`[unmeasured-number]`、`[activity-not-outcome]`、`[mostly-manual]`、`[parse]` 时查不到定义，不知道该修还是该留。
- 证据：
  - `CONTEXT.md:357` 「**`cycle` / `dangling` / `dollar-without-m` / `manual-gate` / `shared-state`**:」，`CONTEXT.md:358` 「The problem tags the linter reports.」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:981-985` 只产出三个方括号标签：「        print("  ERROR " + finding + "  [dollar-without-m]")」「        print("  WARN  " + finding + "  [shared-state]")」「        print("  WARN  " + finding + "  [unexplained-edge]")」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:859-861`（cycle / dangling 的实际打印）「        for error in errors:\n            print(error)」——没有方括号标签，正文是 `cycle detected: …` 与 `dangling dependency: …`（`verify-ticket.py:562`、`:599`）
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-lint.mjs` 的 rule 名：`tautological-check`（:118）、`weak-expect`（:123）、`path-read-as-regex`（:128）、`manual-gate`（:133）、`unmeasured-number`（:137）、`activity-not-outcome`（:143）、`mostly-manual`（:149）、`parse`（:103）
  - `mmw-v2/skills/verify-ticket/tests/test_lint_writing.py:87` 「class TestUnexplainedEdge(unittest.TestCase):」——`unexplained-edge` 有测试、有文档注释，唯独没进 CONTEXT.md
- 建议正名：`CONTEXT.md:357-359` 按 gate-lint.mjs 的 rule 名 + `verify-ticket.py` 那三个补全；`cycle` / `dangling` 不是标签，另起一句说它们是票图检查打印的整行。

---

## 发现 10：`--closeout --check-only` 按 SKILL.md 那样写会直接报用法错误

- 类型：脚本与文档不符
- 后果：worker 照 SKILL.md 敲，拿到 `error: argument --closeout: expected one argument`，以为脚本坏了。脚本自己在拒绝信息里给的写法是对的，两处不一致。
- 证据：
  - `mmw-v2/skills/verify-ticket/SKILL.md:39` 「`--closeout --check-only` reports on the draft and changes nothing.」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:823-824` 「rest = (f" Run `verify-ticket.py {number} --closeout {draft_path} --check-only` " f"to see the other {len(problems) - 1}." …」
  - 实测 `python3 …/verify-ticket.py 77 --closeout --check-only` → 「verify-ticket.py: error: argument --closeout: expected one argument」
- 建议正名：`SKILL.md:39` 改成 `--closeout <draft> --check-only`。

---

## 发现 11：「拒绝的理由是 stderr 上的一行」——实际是 1 + N 行

- 类型：脚本与文档不符
- 后果：只读首行的人以为问题就一个，改完再跑再被拒，进入一次修一个的循环；而这正是脚本注释里点名要避免的（`verify-ticket.py:821-822`）。
- 证据：
  - `mmw-v2/skills/verify-ticket/SKILL.md:40-41` 「A refused draft changes nothing either way: the reason is one line on stderr, and the ticket is untouched.」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:827-828` 「        for problem in problems[1:]:\n            sys.stderr.write("also: " + problem + "\n")」
  - `mmw-v2/skills/verify-ticket/tests/test_closeout.py:428-429` 「        self.assertGreater(len(lines), 1)\n        self.assertTrue(all(l.startswith("also: ") for l in lines[1:]), lines)」
- 建议正名：`SKILL.md:40-41` 改成「首行给出问题总数，其余每行以 `also:` 开头」。

---

## 发现 12：`CWD:` 是账本的第四个属性，但 CONTEXT.md 没登记它，`STALE` 的定义也只提 `CHECK:`

- 类型：断点 + 幽灵词
- 后果：`STALE` 出现时，票上写的是「CHECK/EXPECT/CWD/shell signature changed」，读者去 CONTEXT.md 查 `CWD` 查不到，也不知道 `EXPECT:` 或 `CWD:` 的改动同样会作废结果，只会去看 `CHECK:` 有没有被改。写票的人也不知道 `CWD:` 这个属性可以用。
- 证据：
  - `CONTEXT.md:211-212` 「**`STALE`**:\nWhat the gate checker reports when the signature of a `CHECK:` no longer matches the one it started with, so the result is discarded.」
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-check.mjs:605` 「        console.log("  STALE " + qualify(result.file, result.gate.id) + ": CHECK/EXPECT/CWD/shell signature changed; result not written");」
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/lib/gates.mjs:46` 「const ATTR_RE = /^(\s+)(CHECK|EXPECT|EVIDENCE|CWD):\s?(.*)$/;」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:53` 「ATTR_LINE_RE = re.compile(r"^\s+(CHECK|EXPECT|EVIDENCE|CWD):")」
  - `CONTEXT.md` 全文 grep 无 `CWD`；`mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md` 全文 grep 无 `CWD`
- 建议正名：`CONTEXT.md` 的「Acceptance criteria」段补一条 `CWD:` 词条；`CONTEXT.md:212` 改成「CHECK / EXPECT / CWD / shell 四者的签名」。

---

## 发现 13：`PASS AC:AC<n>` 被登记为「re-run 之后打印的逐条状态」，实际每次运行都打印，且同一族还有 `RUN` / `FAIL` / `STALE` / `UNMET` 四个没登记

- 类型：脚本与文档不符
- 后果：读者看见 `self-run`（不是 re-run）的输出里也有 `PASS AC:AC1: …`，会怀疑自己跑错了命令；看见 `RUN  AC:AC2` 或 `FAIL AC:AC2` 时查不到定义。
- 证据：
  - `CONTEXT.md:231-232` 「**`PASS AC:AC<n>`**:\nThe compact per-criterion status printed after a re-run.」
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-check.mjs:561` 「    console.log("  PASS " + qualify(result.file, result.gate.id) + ": " + result.gate.title);」——在 `results` 循环里，`--reverify` 与否都走这里
  - 同族未登记的四个：`gate-check.mjs:544`「  console.log("  RUN  " + …」、`:564`「    console.log("  FAIL " + …」、`:605`（STALE）、`:649`（UNMET）
  - `mmw-v2/skills/verify-ticket/tests/test_verify_ticket.py:122` 「        self.assertNotIn("RUN  AC:AC2", printed)」——`RUN` 已经是被测试固定住的字面串
- 建议正名：`CONTEXT.md:232` 去掉「after a re-run」，并把这条改写成一族（`RUN` / `PASS` / `FAIL` / `STALE` / `UNMET`，都带 `AC:<id>` 限定名）。

---

## 发现 14：两个 `_Avoid_` 死词仍在活文件里

- 类型：幽灵词
- 后果：`models.md` 用 `orchestrator` 指的正是 CONTEXT.md 里的 `main agent`；改模型表的人会以为表里少了 main agent 一行而去补。`merge-notes` 用 `verifier 子代理` 指 `verifier`，中文读者会以为是另一个角色。
- 证据：
  - `CONTEXT.md:13` 「_Avoid_: coordinator, 编排者, orchestrator, 出票的主 agent, 落地 agent」 对 `mmw-v2/skills/dispatch/models.md:3-4` 「Every agent this pipeline sends out is here except the\norchestrator, which is the session you started yourself from the CLI.」
  - `CONTEXT.md:29` 「_Avoid_: 复验者, verifier 子代理, subagent verifier」 对 `mmw-v2/merge-notes/implement.md:15` 「→ 派 verifier 子代理（prompt 只有 `verify #<n>`，不派第二次）→」
- 建议正名：`models.md:4` 的 `orchestrator` 换成 `main agent`；`merge-notes/implement.md:15` 的「verifier 子代理」换成 `verifier`。

---

## 发现 15：`The environment is yours; the repository is not.` 这个字面词条，源文件里没有句号

- 类型：脚本与文档不符（字面串词条）
- 后果：CONTEXT.md 第 5 行自己立的规矩是「名字本身就是文件里那个字面串的词，只有一个名字——那个串」。带句号的版本在源文件里搜不到；照 CONTEXT.md 去 grep 的人会以为这句被删了。
- 证据：
  - `CONTEXT.md:273` 「**`The environment is yours; the repository is not.`**:」，`CONTEXT.md:274` 「The line in the verifier's definition file that draws its boundary」
  - `mmw-v2/agents/verifier/body.md:35` 「## The environment is yours; the repository is not」（无句号，是一个 `##` 标题而不是一行正文）
- 建议正名：`CONTEXT.md:273` 去掉句号，`:274` 的「The line」改成「The heading」，并把「definition file」落到具体路径 `mmw-v2/agents/verifier/body.md`。

---

## 发现 16：`UPSTREAM.md` 说 vendored 的 `gate-check.mjs` 是 701 行，实际 700 行

- 类型：脚本与文档不符
- 后果：拉上游、解冲突的人拿这个数当核对依据（`AGENTS.md` 规定改了上游技能就要更新 merge-note），对不上会以为文件被人动过。
- 证据：
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md:20` 「894 lines upstream, 701 here.」
  - 实测 `wc -l mmw-v2/skills/verify-ticket/scripts/gate-check/gate-check.mjs` → `700`（上游快照 `docs/research/code-landing-refs/unlazy/scripts/gate-check.mjs` 实测 894，这一半是对的）
- 建议正名：把 701 改成 700。
