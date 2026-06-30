# ③ 落地合同门(contract-gate · 机器核,不派 Codex 判断)

> ③ 不是 Codex 审 loop——降成**便宜机器合同门**:全 plan 合并后跑**一次**,只核"声明的跨 plan 合同兑现"。代码质量 / 正确性 / 边界归 ④final,不在这判。重判预算砸 ④。
> **全 Pack 提交不在这核**——build 的执行 loop `exit-check` DONE 已保证(B4)。跨 plan 合同要等所有 plan 在场才能核,所以 ③ 跑一次、不 per-plan。

全 plan 合并后起本门(`mmw review start --stage plan-impl`,`kind=contract-gate`)。主线程逐条机器核,不开 Codex、不列 pack:

## 核什么(只一项:跨 plan 合同兑现)

对设计文档 `## Cross-Plan Contract Anchors` 里**每条**跨 plan 合同,机器核它在合并后的代码里真兑现:
- **provider** 声明的接口 / 类型 / 端点 / schema 真存在(`grep`/`Read` 到定义,给 `file:line`)。
- **consumer** 真按该接口对接(调用点签名对得上)。
- schema / 合同**版本号**一致;新字段配套 **migration** 在位;新增可被外部引用之物入**登记**(registry / catalog)。

## 怎么走(只走 checklist,不加 step)

```bash
mmw loop checklist add --item "<一条跨 plan 合同>" --source <design:line>   # 逐条合同
# 逐条 grep/Read 机器核兑现 → 坐实就 cover(给 file:line 证据)
mmw loop checklist cover --item <i> --evidence <file:line>
# 合同清单全 cover → exit-check DONE(无 step,steps 空即满足)→ handoff pass
```

## 出口

- 合同全兑现 → `mmw handoff --conclusion pass`(进 verify ④终审)。
- 合同没兑现(provider/consumer 对不上、版本不一致、缺迁移/登记)→ `mmw handoff --conclusion needs-redirection --to-phase build`(回落地补)。
- 合同**根上**就错(设计的跨 plan 合同本身不成立)→ `mmw handoff --conclusion needs-redirection --to-phase design`。

> 机器核要 `file:line` 证据才 cover,核不出不算兑现。不在这做主观代码评审。
