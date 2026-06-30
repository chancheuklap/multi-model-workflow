# ④ final review

所有 plan 合并后审整个分支。不重复阶段③(不再逐 Pack 对 acceptance),专审单 plan 看不到的:plan 之间的缝隙 / plan A 碰坏 plan B / 整条意图闭环。

**Source**:源意图(最初 design + 全部 issue)· 待审产物(整分支相对 base 的全 diff)

## 基线 1 回归 + 意图 + 跨 plan
- 回归扫描:全 diff 过一遍,有没有破坏既有功能 / 既有调用点。
- 意图覆盖:回最初 design + issue(有 UI 则 Read mockup 文件,视觉权威源),逐条提取可验证 intent;阶段③验过的做一行确认;plan 之间缝隙漏的按 implementation / design / context / unverifiable gap 归类。
- 跨 plan 集成:plan A 碰坏 plan B 没;跨 plan 合同 / 数据流 / 共享状态 / migration 顺序 / import 一致;多个各自正确的 plan 合起来有无矛盾(无共享面 → 一行"已确认独立";回归扫描和意图覆盖仍必做)。

## 基线 2 独立代码审计
不看 plan,全新眼光审整段 diff:
- 正确性:逻辑错 / off-by-one / null / 类型不匹配 / 边界。
- 安全:injection / auth bypass / 数据泄漏 / insecure defaults / OWASP top 10。
- 二阶故障:A 失败时 B 优雅处理(propagation / retry / rollback)。
- 集成 / 回归:跨文件协调;破坏既有功能没。
- 设计对齐:实现匹配 design 声明 intent。
- 边界:空态 / 错误路径 / retry·rollback / 竞态 / 测试没覆盖的。
- 禁用捷径:见 `quartet.md` 附录。
- 只为具名风险查 diff 外代码,不漫游。

两基线都:不信任 plan / pack summary,独立验证。

## 终审报告(④过后主线程写,钉给 closing)

④final 收敛、无开口 Critical 后,主线程写一份终审报告到 `docs/<slug>-final-review.md`(照 `mmw where` 的 `then` 钉 `--produced`),closing 照单读它收口。三段:

1. **终审结论**:verdict + 两基线各自结果(回归/意图/跨 plan;独立代码审)+ 放行的 waived 项(环境/账号 gate,带 owner)。
2. **意图清单逐条**:最初 design + issue 提取的每条可验证 intent → 达成/未达成 + 证据(`file:line` 或测试名)。
3. **业务语言交付摘要**(给项目负责人看,**不用技术术语**):
   - **新增能力**:每条是一个用户可感知的行为变化(「用户现在可以用手机号登录,15 秒内完成」),不列函数名 / 文件路径 / 类名。
   - **验证证据**:这些能力怎么被证明可用(跑了哪些验收、什么结果)。
   - **残余风险**:已知没覆盖的、留给后续的、需要人盯的(诚实列,不藏)。

   Good:「用户现在可以用手机号登录,15 秒内完成」 / Bad:「实现了 PhoneAuthProvider 并集成到 AuthStrategy pipeline」。
