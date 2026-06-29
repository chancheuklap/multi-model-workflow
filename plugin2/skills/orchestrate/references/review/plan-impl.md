# ③ 落地合同门(contract-gate · 机器核,不派 Codex 判断)

> ③ 不是 Codex 审 loop——它跟 TDD 每步验重叠,降成**便宜机器合同门**:只核"全 Pack 提交"+"声明的跨 plan 合同兑现",两个都机器可核。代码质量 / 正确性 / 边界归 ④final,不在这判。重判预算砸 ④。

一份 plan 全部 Pack 提交后起本门(`mmw review start --stage plan-impl`,`kind=contract-gate`)。主线程逐条机器核,不开 Codex:

## 核什么(两项,都机器可核)

1. **全 Pack 提交**:plan 的每个 Task Pack 都有对应提交(`Pack N.M`),`mmw loop step` 全 done。缺提交 = 没落完,回落地补。
2. **跨 plan 合同兑现**:对设计文档 `## Cross-Plan Contract Anchors` 里**每条**跨 plan 合同,机器核它在合并后的代码里真兑现:
   - **provider** 声明的接口 / 类型 / 端点 / schema 真存在(`grep`/`Read` 到定义,给 `file:line`)。
   - **consumer** 真按该接口对接(调用点签名对得上)。
   - schema / 合同**版本号**一致;新字段配套 **migration** 在位;新增可被外部引用之物入**登记**(registry / catalog)。

## 怎么走

```bash
mmw loop step add --id <pack-id> ...                       # 列本 plan 待提交的 Pack
mmw loop checklist add --item "<一条跨 plan 合同>" --source <design:line>   # 逐条合同
# 逐条 grep/Read 机器核兑现 → 坐实就 cover(给证据)
mmw loop checklist cover --item <i> --evidence <file:line>
# 全 Pack 提交 + 合同清单全 cover → exit-check DONE → handoff pass
```

## 出口

- 全 Pack 提交 + 合同全兑现 → `mmw handoff --conclusion pass`(进下一 plan 或 verify)。
- 合同没兑现(provider/consumer 对不上、版本不一致、缺迁移/登记)→ 回本 plan 落地补(落地自己的 2 轮)。
- 合同**根上**就错(设计的跨 plan 合同本身不成立)→ 升级:`mmw handoff --conclusion needs-redirection`。

> 机器核要 `file:line` 证据才 cover,核不出不算兑现。不在这做主观代码评审。
