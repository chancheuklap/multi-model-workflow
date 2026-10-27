## Parent

#58, Implementation Decisions section 6

## What to build

1. 改名称窗口（`supplier:manage`）：新名称必填；和别家相同不能改；疑似的要确认「不是同一家，继续改名」；提示「改名后「X」自动成为别名，按它照样能搜到。」。AC1、AC2 验证。
2. 别名：「＋ 添加别名」回车保存，标签上的叉删除；合并：选被合并的和保留的，确认后转入；停用 / 恢复合作。AC3 验证。
3. 「查看全部」货源侧边栏：「X 供应的货源」、搜同款名称、表格列照原型、按现用于从多到少、每页 50 个、「导出 xlsx」；有 `listing:read` 的点一行打开那次上架（优先自己店铺的）的「货源与拿货成本」，用 `router.push('/products/listings?listing=<编号>&tab=source')`。AC4 验证。
4. 「上传对账单」（`reconciliation:write`）用 `router.push('/products/supplier-reconciliations?upload=<供应商编号>')` 转到供应商对价、选好这家。

5. 货源导出走共用的 `src/api/erp.ts`：本 ticket 在里面加一个成功时返回 `Blob` 的请求，和 `request` 共用网络错误、非 JSON 错误、状态码、`code`、`message` 和未登录处理；`exportSources` 改用它（[#87](https://github.com/agentflow-hq/erp-frontend/issues/87)）。别的 ticket 也可能改这个文件，合并时照常解决冲突。

## Read first

- [#58](https://github.com/agentflow-hq/erp-frontend/issues/58) Implementation Decisions 第 6 节（baseline）。
- `efforts/product-listing/prototypes/84/UI/winner/supplier.js`（baseline）。
- `.agents/skills/verify-erp/features/suppliers.md`（baseline）。
- [erp-backend #133](https://github.com/agentflow-hq/erp-backend/issues/133) 第 15 节第 4–6 点（baseline）。
- `TESTING.md`「Layers」「External boundaries and how they are stubbed」「Putting the system into a state」：视图和接口适配测试的写法。
- `.agents/skills/verify-erp/SKILL.md`「Launch」「Drive」：浏览器验收测试怎么跑。

## Seam

浏览器验收在 `tests/e2e/erp/`（先例 `smoke.e2e.ts`），本 ticket 的验收测试已写好、在 `design` 目标通过，开发时只改产品代码，不改测试。`product` 目标后面是本地环境工具起的真实 Account 和 ERP 后端，来自旁边在 `development` 上的 checkout（`ERP_BACKEND_DIR`、`ACCOUNT_BACKEND_DIR`），它们要已经合进 erp-backend #133 和 account-backend #50 的 ticket。测试自己通过页面建数据（`tests/e2e/erp/helpers/product-pages.ts`）。 视图和接口适配在 `test/*.spec.ts`，先例 `test/management-views.spec.ts`、`test/erp-api.spec.ts`：`erpApi` 或 `fetch` 的 spy 返回字面量数据，会话写进 Pinia，权限码每个用例自己选。

## Owns

- src/api/erp.ts
- src/views/products/SuppliersView.vue
- src/components/suppliers/**
- src/api/suppliers.ts
- test/supplier-manage-view.spec.ts (new)

## Acceptance criteria

- [ ] AC1: 改名后按原名称照样搜得到这家
  CHECK: pnpm install --frozen-lockfile --silent && npx e2e run supplier-rename.e2e.ts --config tests/e2e/erp/e2e.config.ts --target product --trace on --output .e2e/supplier-rename.e2e
  EXPECT: /Tests\s+2 passed \(2\)/
  TIMEOUT: 1200
  EVIDENCE: pending
- [ ] AC2: 新名称和别家的别名相同时保存不能点，并写明「已是」那家的名称或别名
  CHECK: pnpm vitest run test/supplier-manage-view.spec.ts -t "blocks a rename that clashes with another supplier"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending
- [ ] AC3: 合并确认后调用合并接口，列表不再有被合并的那家
  CHECK: pnpm vitest run test/supplier-manage-view.spec.ts -t "merges one supplier into another"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending
- [ ] AC4: 供应的货源侧边栏写「共 N 个货源，现用于 N 次上架。」，按现用于从多到少
  CHECK: pnpm vitest run test/supplier-manage-view.spec.ts -t "lists the supplier sources by use"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending

