---
date: 2026-09-09
amends: [0003, 0006, 0014]
---

# 工具箱不再交付 subagent：用 host 自带的通用 subagent

MMW 只交付技能。`mmw-v2/agents/` 整个目录连同 `assemble.py`、`reviewer`、`claim-checker` 都删掉了，各 host 的 `agents/` 目录（含 `~/.grok/roles/`）成为退役位置，`install.sh` 每次运行都从里面摘掉本仓库留下的软链。需要派活的技能改口要 host 自带的通用 subagent。

## 要修的是什么

一个 subagent 定义文件的全部内容是：一份提示词正文、一个 description、一份工具清单、一个 model 与一档 effort。前两样技能自己就能带；后三样是这套组装系统存在的唯一理由，而它们各自都已经不划算：

- **model 与 effort 要为每个 agent 在每个 host 上各写一行。** `reviewer` 和 `claim-checker` 两个 agent 在 `models.md` 里占了九行，全是 `—`。九行的用途只是让组装出来的定义文件里有一个 model 字段，而 subagent 本来就跑在起它那个会话的模型上。
- **五个 host 的定义文件格式互不相同**，所以同一份正文要按 host 换五种壳，五种壳各有一份生成物要与源保持一致，于是又要一个 `--check`。整条链上没有一步是产品需要的。
- **工具清单只在两个 host 上写得出来。** `claude` 与 `pi` 收 `tools` 列表，`cursor`、`codex`、`grok` 收的是一个沙箱档位；三份 reference file 开头那句 `You are read-only. You change no file` 才是五个 host 上都成立的那道约束。

## Considered Options

- **只删 `claim-checker`，`reviewer` 留着。** 否决。`reviewer` 是九行里的四行、组装系统的最后一个用户，留着它就要留整条链：`assemble.py`、`out/` 下六份生成物、六处 host 软链、`install.sh` 里那一段、`--check`，以及 `models.md` 里 `permissions` 取两个值这件事。
- **把 `assemble.py` 原地留下，只删两个 agent 目录。** 否决。它的 `main()` 扫不到 agent 就报错退出，`install.sh` 会跟着回 1。
- **把 `assemble.py` 整个删掉。** 否决，因为它不止做组装。`parse_model_rows`、`profile_rows`、`create_agent_settings`、`apply_permissions` 是 `models.md` 的唯一解析器，`install.sh` 拿它写 Paseo 的 Agent profile，`dispatch.sh` 拿它拼 `create_agent` 的 settings——删了它，整夜的流水线一个 agent 都起不来。这四个函数搬到 `mmw-v2/skills/dispatch/scripts/models.py`。
- **顺手把 `permissions` 列删掉。** 否决。剩下的行全是 `bypass`，看起来这一列可以去掉，但它仍在回答"这一行落地成哪个权限档"，而删它要同时改 `models.md` 的解析（五格变四格）、`profile_rows`、`dispatch.sh` 的 `row_for_role` 与 `emit_create_json`、两个测试文件。这次改动的目的不是重新设计 `models.md` 的表结构，而每夜的流水线都押在这几个函数上。

## Consequences

- **三个 code-review axis subagent 不再有任何权限档或工具白名单拦着它们写文件**，拦住它们的是 `references/standards-reviewer.md`、`spec-reviewer.md`、`tests-reviewer.md` 开头那句 `You are read-only. You change no file`，以及 `references/session.md` 第 2 节要求"能限制工具的 host 就限成只读"。轴 subagent 再调一次本技能、带上 axis 名，不读绝对路径。这与 advisor 的处境相同（`0014-advisor-has-one-door.md`），理由也相同：五个 host 里只有两个收工具白名单。
- **三个 axis subagent 跑在 reviewer session 的 model 上**，即 `models.md` 里 reviewer 那一行的 `claude-opus-5` / `high`，而不再是原先四行各自的模型。想单独给 axis 换模型，得先给它一扇自己的门。
- **`models.md` 从十五行减到六行**，`permissions` 列只剩 `bypass` 一个值。
- **`models.py` 跟着 dispatch 技能的 symlink 走**，所以它在五个 host 上都在，被拷走的技能目录也自带它——`assemble.py` 原先要靠 `install.sh` 的路径反推才找得到。
- **`install.sh` 从装七样变六样**，`--check` 不再包含 `assemble.py --check`。工具箱的五层测试里"结构核对"那一层少了一个被测对象。
- **各 host 的 `agents/` 目录成为退役位置。** 装过上一代的机器上留着六处软链指向已删文件，host 扫到一条断链就是一个起不来的 agent，所以要跑一次 `bash mmw-v2/install.sh` 才算清干净；`--check` 在清干净之前会一直报 `残留`。
- **这一个决定同时作废了先前三份 ADR 里的句子。** `0014` 的「`assemble.py` 的补位机制不变，仍然由 reviewer 在 claude 上那一行用着」；`0006` 的「subagent 不走这条，仍按宿主各装一份」「subagent 那半边仍要加一行安装点和一份成品壳」，以及它把 0003 的散装说法留给 subagent 的那一句；`0003` 的「本篇『五个宿主各装一份』只对 subagent 仍然成立」与「九个交付面现在只剩技能与 subagent 两面」。三份各自的 `# ` 标题之上都有一段 `>` 注指回这里：它们同出一因，不是三个各自独立的错误。
