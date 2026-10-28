---
date: 2026-10-28
amends: [0038, 0039]
---

# MMW v4 不再有 `TESTING.md`：没有技能写它、读它或检查它，一个仓库的测试怎么跑只看测试文件和 `scripts/check`

setup-mmw 不再写 `TESTING.md`，也不再把它缺失报成一项。写 spec、切票不再引用它，Tests 轴只按原则审测试，worker 改了测试做法也不再改它。setup-mmw 判断仓库要不要 `scripts/env` 时也不再读它。MMW 自己仓库根目录的 `TESTING.md` 删除。产品仓库里已有的 `TESTING.md` 从此没有技能读，留给各仓库自行处理。

## 要修的是什么

2026-10-28 在 dev 4112db428 上量过。根目录 `TESTING.md` 从 2026-10-10 的 2.5 KB 涨到 24 KB，2026-10-27 一天被改 43 次，其中约 20 KB 是逐个测试的造数据和造状态描述。spec #1312 和 #1349 的 21 张票里，Tests 轴只在 #1322 上靠它抓出真问题；其余提到它的，都是确认新加的那段和自己的测试对得上。它在 Owns 之外，审查员要为它写判断行，因此留下 #1371、#1342、#1367 三条登记，还让 #1325 落地冲突一次。主人的决定见 [#1393](https://github.com/chancheuklap/multi-model-workflow/issues/1393)。

## Considered Options

- **只留规则，删掉逐个测试的描述，规则变了才改。** 没有采用。主人选择整份删除。被删的规则里，"测试不断言技能文字和拒绝措辞"是 #1322 两条发现的出处；此后这类问题只靠 **principle-test-behavior-not-implementation** 判断。
- **让改测试的票在 Owns 里列上 `TESTING.md`（#1371 的建议）。** 否决。它只消除越界判断，文件本身仍随每张票增长，仍没有读者用得上。

## Consequences

- 本决定改写 0039 中 `TESTING.md` 随改动当场改的一项，和 0038 把 `TESTING.md` 列为常驻文件的一项。
- Tests 轴的 `documented-standard` 发现只能出自 ADR、词汇表等仓库确实记录的规则。
