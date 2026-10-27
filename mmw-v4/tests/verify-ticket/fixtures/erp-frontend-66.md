## Parent

#58, Implementation Decisions section 7

## What to build

1. 填满 `/products/supplier-reconciliations`，照原型 `recon.js` 和 [erp-backend #133](https://github.com/agentflow-hq/erp-backend/issues/133) 第 16 节：对价记录列表（筛供应商、上传日期；状态解析中 N% / 读取失败 / 待查看 / 已保存；每页 50 条）。AC2 验证。
2. 上传对账单（`reconciliation:write`）：选供应商、选文件；只收 xlsx 和 csv，其他按出错表提示（xls、et、ods、numbers 「请用 Excel 或 WPS 打开，另存为 xlsx 后再上传」，其余「请找供应商要 Excel 格式的对账单」）。AC1 验证。
3. 对应表头窗口：工作表、表头在第几行；十一项（九项加选填的订单号、商品标题，排在单号状态之后）各从下拉选一列，选项写列号、表头文字或「无表头」和前几个值，被别项选走的标灰，「系统预选」，SKUID 和省份、商品ID 的取出示例；必选校验「请选择：…」、「一列只能对应一项」；底部写自动跳过几行；「保存并开始读取」（spec 第 7 节）。AC3 验证。
4. 读取中每 2 秒问一次进度，显示「已读 N / M 行」，总行数没数完时「正在打开文件」，可关掉稍后再看。AC4 验证。
5. 地址带 `?upload=<供应商编号>` 时直接打开上传窗口并选好这家（供应商库的「上传对账单」这样跳过来）。供应商下拉用供应商库那张 ticket 已有的列表调用，不改 `src/api/suppliers.ts`。AC5 验证。
6. 地址带 `?supplier_id=<供应商编号>` 时列表的供应商筛选已选好这家，只列这家的对价记录（供应商库详情的「查看全部」这样跳过来，照原型 `supplier.js` 的 `allRecs`）；和 `?upload=` 可以各自单独出现。AC6 验证。
7. 接口放 `src/api/reconciliations.ts`。

8. 对账单上传走共用的 `src/api/erp.ts` 的 `request`：本 ticket 让它在请求体是 `FormData` 时不加 JSON 的 `Content-Type`，JSON 请求和未登录处理不变；去掉上传自己的 `fetch`（[#89](https://github.com/agentflow-hq/erp-frontend/issues/89)）。别的 ticket 也可能改这个文件，合并时照常解决冲突。

## Read first

- [#58](https://github.com/agentflow-hq/erp-frontend/issues/58) Implementation Decisions 第 7 节（baseline）。
- `efforts/product-listing/prototypes/84/UI/winner/recon.js`（baseline）。
- `.agents/skills/verify-erp/features/supplier-reconciliations.md`（baseline）。
- [erp-backend #133](https://github.com/agentflow-hq/erp-backend/issues/133) 第 16 节、[erp-backend #107](https://github.com/agentflow-hq/erp-backend/issues/107)「供应商对价」一表、出错表和补充评论「对账单怎么读」（baseline）。
- `TESTING.md`「Layers」「External boundaries and how they are stubbed」「Putting the system into a state」：视图和接口适配测试的写法。
- `.agents/skills/verify-erp/SKILL.md`「Launch」「Drive」：浏览器验收测试怎么跑。

## Seam

浏览器验收在 `tests/e2e/erp/`（先例 `smoke.e2e.ts`），本 ticket 的验收测试已写好、在 `design` 目标通过，开发时只改产品代码，不改测试。`product` 目标后面是本地环境工具起的真实 Account 和 ERP 后端，来自旁边在 `development` 上的 checkout（`ERP_BACKEND_DIR`、`ACCOUNT_BACKEND_DIR`），它们要已经合进 erp-backend #133 和 account-backend #50 的 ticket。测试自己通过页面建数据（`tests/e2e/erp/helpers/product-pages.ts`）。 浏览器测试只验证文件格式被拒：原型只认三家样例对账单，读表头以后的步骤两个目标走不出同一条路，由视图测试验证（this ticket's decision）。视图和接口适配在 `test/*.spec.ts`，先例 `test/management-views.spec.ts`、`test/erp-api.spec.ts`：`erpApi` 或 `fetch` 的 spy 返回字面量数据，会话写进 Pinia，权限码每个用例自己选。

## Owns

- src/api/erp.ts
- src/views/products/ReconciliationsView.vue
- src/components/reconciliations/** (new)
- src/api/reconciliations.ts (new)
- test/recon-upload-view.spec.ts (new)

## Acceptance criteria

- [ ] AC1: 上传 xls 对账单被拒，提示「只能上传 xlsx 或 csv 文件，这个是 xls 文件。」
  CHECK: pnpm install --frozen-lockfile --silent && npx e2e run recon-upload.e2e.ts --config tests/e2e/erp/e2e.config.ts --target product --trace on --output .e2e/recon-upload.e2e
  EXPECT: /Tests\s+2 passed \(2\)/
  TIMEOUT: 1200
  EVIDENCE: pending
- [ ] AC2: 对价记录里解析中的一行写「解析中 40%」
  CHECK: pnpm vitest run test/recon-upload-view.spec.ts -t "shows parsing progress in the list"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending
- [ ] AC3: 对应表头没选件数和发货时间时提示「请选择：件数、发货时间」；订单号和商品标题不选也能保存
  CHECK: pnpm vitest run test/recon-upload-view.spec.ts -t "requires the mandatory mapping items only"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending
- [ ] AC4: 读取中的对价每 2 秒问一次进度，显示「已读 120 / 300 行」
  CHECK: pnpm vitest run test/recon-upload-view.spec.ts -t "polls reading progress every two seconds"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending
- [ ] AC5: 打开 `/products/supplier-reconciliations?upload=5` 时上传窗口已打开、供应商选的是第 5 家
  CHECK: pnpm vitest run test/recon-upload-view.spec.ts -t "opens the upload for the supplier in the address"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending
- [ ] AC6: 打开 `/products/supplier-reconciliations?supplier_id=5` 时供应商筛选选的是第 5 家，列表只请求这家的对价记录
  CHECK: pnpm vitest run test/recon-upload-view.spec.ts -t "filters the list to the supplier in the address"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending

