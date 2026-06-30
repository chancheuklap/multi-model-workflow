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
- 禁用捷径:跨边界用弱类型裸结构绕正式合同 / 新增可被外部引用之物不登记 / 绕数据校验与迁移机制 / 行为测在非权威层——命中即 finding,影响验收/数据/权限/账务/runtime/发布时升 Critical。
- 只为具名风险查 diff 外代码,不漫游。

两基线都:不信任 plan / pack summary,独立验证。
