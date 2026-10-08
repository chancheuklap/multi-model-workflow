---
date: 2026-10-08
amends: []
---

# 每个仓库根目录的 `CODING_STANDARDS.md` 是它审查规则的唯一来源，由 setup-mmw 从模板抄入起头，此后只随本仓库的 retro 提案改；`TESTING.md` 由改变测试做法的改动当场改，retro 补漏

一个仓库被审查时，规则只有根目录这一份 `CODING_STANDARDS.md`。Standards 轴用它的 `## Code`，Tests 轴用它的 `## Tests`。两轴的提示词在轴文件之后放这份全文，取被审查那次提交的版本。Tests 轴的提示词再放根目录 `TESTING.md` 的全文，同样取那次提交。两份里缺了哪份，那个位置放一行说没有。

模板在 `mmw-v3/skills/setup-mmw/CODING_STANDARDS.md`，和 setup-mmw 的 `issue-tracker.md`、`triage-labels.md`、`domain.md` 并排。setup-mmw 接入仓库时，根目录没有 `CODING_STANDARDS.md` 就整份抄入，已有的不动。模板以后再改，已接入的仓库不跟。一条规则此后只经这个仓库自己的、主人批准的 retro 提案，写成根目录那份的一行。

`TESTING.md` 记这个仓库的测试是怎么跑的。改变测试做法的改动在同一个提交里改它。夜里，造那个机制的票在 **Owns** 里列出根目录 `TESTING.md`，并写上那一行。白天的小改动也在同一个提交里改。retro 的 `testing-fact` 去向补一次提交漏掉的事实。一条规则教训只进本仓库根目录的 `CODING_STANDARDS.md`。

## Considered Options

- **模板改动同步到已接入的仓库。** 否决。主人的决定 1，2026-10-08。每个仓库的规则只随这个仓库自己的证据改。模板以后的改动只影响以后接入的仓库。
- **`TESTING.md` 只在 retro 时更新。** 否决。同一夜里，一张票加了一层测试而不改 `TESTING.md`，后一张票照新做法写的测试会被 Tests 轴拿旧文件判成和 `TESTING.md` 矛盾，多返工一轮。这条无效意见还会被 retro 记到审查头上。见 spec #935 的 Problem Statement。改变测试做法的改动当场改 `TESTING.md`，retro 只补漏。

## Consequences

- `mmw-v3/skills/code-review/` 里没有通用的 `CODING_STANDARDS.md`。审查不把两份文件拼在一起，也不在两份冲突时挑一份。
- 写代码的 agent 不直接读 `CODING_STANDARDS.md`。`TESTING.md` 的读法不变。读它的仍是写 spec 的人、在 spec 之外写票的人，和审查的 Tests 轴。worker 从 spec 和票里拿到要写的那一行。
- `CONTEXT.md` 怎样保持为真，这次没有定。`docs/adr/0038-repository-files-are-layered-by-lifetime.md` 记下 `CODING_STANDARDS.md`、`TESTING.md` 和 `CONTEXT.md` 都还没有保持为真的机制。这一份补上前两份。
