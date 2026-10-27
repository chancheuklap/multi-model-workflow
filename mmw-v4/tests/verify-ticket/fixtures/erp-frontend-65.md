## Parent

#58, Implementation Decisions sections 3 and 4

## What to build

1. 填满 `/products/listings`：页头、列表（列照原型，后三列是 SKU 区间）、「新增上架」按钮（`listing:write`）；关键词搜索框（占位「搜索 名称 / 抖店商品ID / SKUID / 供应商」，请求带 `keyword`，参数照 erp-backend `regulations/api/product-listing-queries.md`）也在这里做；店铺、上架日期、状态筛选，待补和导出由下一张 ticket 做。AC1 验证。
2. 新增上架弹窗：先搜（`GET /v1/listings/copy-candidates`），没搜过前「没有这件货，新建」不能点；新建打开侧边栏。复制由后面的 ticket 做。AC1、AC2 验证。
3. 编辑侧边栏五个标签（基本信息、货源与拿货成本、SKU、保本 ROI 记录、同款）；本 ticket 做基本信息、货源与拿货成本里新货源的选供应商和报价（包邮价或产品价 + 快递费，每行「确定」）、SKU 的「从货源导入」和 SKUID、售价（输入框无障碍名称「抖店 SKUID」「售价」），保本 ROI 当场用和后端相同的算式算（[erp-backend #133](https://github.com/agentflow-hq/erp-backend/issues/133) 第 11 节），一次「保存」一个请求。必填项框变红、写「必填」、跳到出错的标签；`400 VALIDATION_FAILED` 合成一条提示。AC1、AC3、AC4 验证。
4. 金额是字符串，按字符串显示两位小数，不转浮点（spec 第 3 节）。AC5 验证。
5. 别的页面打开某次上架用地址 `/products/listings?listing=<上架编号>&tab=source`（`tab` 取 `basic`、`source`、`sku`、`roi`、`same`）：本页读到就直接打开那次上架的侧边栏和那个标签，不受列表筛选和店铺范围限制（`GET /v1/listings/:id` 不限范围）；调用方只 `router.push`（this ticket's decision：原型靠共享内存跳转，没有地址可照抄）。AC6 验证。
5. 接口放 `src/api/listings.ts`。

6. 共用请求 `src/api/erp.ts` 的 `ApiError` 带上后端 400 返回的 `errors`（每项 `{field, message}`，没有时为空数组），原有的状态码、`code`、`message` 和未登录、无权限处理保持不变；本 ticket 的字段标红和跳到第一个出错的标签页读它。

7. 选好店铺后马上显示这家店的负责人（只读），照原型：读 `GET /v1/listings/shop-options` 每条的 `owner`（`{account_id, display_name}` 或 `null`；`display_name` 为 `null` 时显示账号编号），不写「保存后自动填写」。这个字段由 [erp-backend #193](https://github.com/agentflow-hq/erp-backend/issues/193) 加；单元测试照这个形状替换接口。

8. `src/api/erp.ts` 另导出一个取文件的请求（成功时返回 `Blob`），和 `request` 共用同一套网络错误、非 JSON 错误响应、状态码、`code`、`message`、字段错误和未登录处理；本 ticket 的导出和 #68 的供应商货源导出都用它（[#87](https://github.com/agentflow-hq/erp-frontend/issues/87)）。

## Read first

- [#58](https://github.com/agentflow-hq/erp-frontend/issues/58) Implementation Decisions 第 4 节（baseline）。
- `efforts/product-listing/prototypes/84/UI/winner/listing.js`、`drawer.js`、`source-card.js`：页面的样子和文字（baseline）。
- `.agents/skills/verify-erp/features/product-listings.md`（baseline）。
- [erp-backend #133](https://github.com/agentflow-hq/erp-backend/issues/133) 第 7–11 节（baseline）；[erp-backend #107](https://github.com/agentflow-hq/erp-backend/issues/107)「接口」各表和「出错时返回什么」（baseline）。
- `TESTING.md`「Layers」「External boundaries and how they are stubbed」「Putting the system into a state」：视图和接口适配测试的写法。
- `.agents/skills/verify-erp/SKILL.md`「Launch」「Drive」：浏览器验收测试怎么跑。

## Seam

浏览器验收在 `tests/e2e/erp/`（先例 `smoke.e2e.ts`），本 ticket 的验收测试已写好、在 `design` 目标通过，开发时只改产品代码，不改测试。`product` 目标后面是本地环境工具起的真实 Account 和 ERP 后端，来自旁边在 `development` 上的 checkout（`ERP_BACKEND_DIR`、`ACCOUNT_BACKEND_DIR`），它们要已经合进 erp-backend #133 和 account-backend #50 的 ticket。测试自己通过页面建数据（`tests/e2e/erp/helpers/product-pages.ts`）。 视图和接口适配在 `test/*.spec.ts`，先例 `test/management-views.spec.ts`、`test/erp-api.spec.ts`：`erpApi` 或 `fetch` 的 spy 返回字面量数据，会话写进 Pinia，权限码每个用例自己选。

## Owns

- src/views/products/ListingsView.vue
- src/components/listings/**
- src/api/listings.ts (new)
- src/api/erp.ts
- test/listing-create-view.spec.ts (new)

## Acceptance criteria

- [ ] AC1: 新建一次上架（新供应商、包邮价 3.20、售价 49.90、服务费率 10、预估退货率 15），SKU 表和列表里保本 ROI 是 1.41
  CHECK: pnpm install --frozen-lockfile --silent && npx e2e run listing-create.e2e.ts --config tests/e2e/erp/e2e.config.ts --target product --trace on --output .e2e/listing-create.e2e
  EXPECT: /Tests\s+2 passed \(2\)/
  TIMEOUT: 1200
  EVIDENCE: pending
- [ ] AC2: 没输入关键词时「没有这件货，新建」不能点
  CHECK: pnpm vitest run test/listing-create-view.spec.ts -t "requires a search before creating"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending
- [ ] AC3: 售价 49.90、拿货成本 3.20、服务费率 10、预估退货率 15 时 SKU 表显示保本 ROI 1.41；售价 10、拿货成本 9.50 时显示「亏损」
  CHECK: pnpm vitest run test/listing-create-view.spec.ts -t "computes break-even roi like the backend"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending
- [ ] AC4: 保存返回 `VALIDATION_FAILED` 带两项必填时，提示「有 2 项必填项未填写」，侧边栏跳到第一个出错的标签
  CHECK: pnpm vitest run test/listing-create-view.spec.ts -t "shows validation errors on their tabs"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending
- [ ] AC5: 接口返回 `"3.20"` 时页面显示 3.20，不经过浮点
  CHECK: pnpm vitest run test/listing-create-view.spec.ts -t "shows money strings as they come"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending
- [ ] AC6: 打开 `/products/listings?listing=7&tab=source` 时侧边栏打开第 7 次上架的「货源与拿货成本」
  CHECK: pnpm vitest run test/listing-create-view.spec.ts -t "opens a listing named in the address"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending




