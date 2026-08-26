---
date: 2026-08-11
amends: []
---

# 技能源落点字面值的机械校验只判两条正则规则，不追求零例外

ADR 0005 规定技能正文只写类别名和 `mmw artifact path`，不写路径字面值。把这条规定变成机械校验时，判据定成两条正则规则：类别根字面值后紧跟一个 `<…>` 占位符段就失败；工作目录根的默认取值出现在技能源正文就失败，不论后面跟不跟占位符。固定类别根不带占位符地单独出现则通过。理由是机器分不出「散文里提到一个知识库」和「拼一条落点」这两种写法，而 `AGENTS.md` 禁止用豁免清单撑着的校验。

## Considered Options

- **零例外：技能源正文里出现任何一个类别根字面值就失败。** 否决。`mmw-triage` 有 20 行以上写着「读 `.out-of-scope/*.md`」这类句子，`mmw-to-spec`、`mmw-closing`、`mmw-reviewer`、`mmw-improve-codebase-architecture` 各有一行写着「读 `docs/adr/` 下相关的 ADR」。这些不带名字段，路径本身就是常量，改写它们换不来正确性。要放过它们就得列豁免清单，而按 `AGENTS.md`，靠豁免清单撑着的校验不算机械校验。它还会牵动 `mmw-triage/examples.md`，那是上游材料，改它要先走 `upstream-skill-fidelity`。
- **只要规则 1，不要规则 2。** 否决。`mmw/skills-src/mmw-start/resuming.md:13` 写着「审查记录目录是 `.reviews/`」，不带占位符，规则 1 抓不到它。但 reviews 根是工作目录根，取值读目标仓库配置，写死默认值本身就是错的。规则 2 补上这一类。
- **不做这类校验，交给审查者的语义判断。** 否决。落点字面值是可解析的语法事实，不是语义判断；已经有 30 处类别根、35 处 `<产物目录>`、28 行 `.scratch/`、10 行 `.reviews/` 说明人工判断挡不住它。

## Consequences

- 校验有一个已知的洞：固定类别根不带占位符地单独出现时不失败。这是有意留下的，不是遗漏。将来有人在技能源里写下 `docs/specs/` 而不跟占位符，测试不会红。
- 规则 2 命中六行不带占位符的现有写法：`wizard/SKILL.md:55`、`to-questionnaire/SKILL.md:31`、`mmw-diagnosing-bugs/SKILL.md:30` 三处同一句「`.scratch/` 在 `.gitignore` 里」，以及 `mmw-closing/SKILL.md:104,106`、`mmw-start/resuming.md:13`。改法是换用 `docs/context/artifact-location.md` 的术语「scratch 根」和「reviews 根」。
- 两份字面值清单从 `mmw/cli/artifacts.json` 与 `mmw/cli/mmw.default.json` 解析，测试里不手抄第二份。
- 这条校验新建 `mmw/cli/tests/test_skill_paths.sh`，不并进 `test_skill_refs.sh`。后者的合同是「引用指得到东西」，本条的合同是「落点只由命令回答」。两个合同放同一份文件里，将来删掉其中一个会连累另一个。
- 排除 `mmw/skills-src/mmw-setup/`，与 `test_skill_refs.sh` 现有做法一致。

来源：Wayfinder decision ticket #26「新归纳合同下机械校验能判定什么」，map #18「MMW 产物归纳与接线合同」。
