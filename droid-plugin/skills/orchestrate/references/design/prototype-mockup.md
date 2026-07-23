# Design · prototype 迭代（触发时只读这一份）

> 触发：设计涉及 UI/UX，或存在多状态、复杂转移、并发、回滚、时序等非平凡状态模型。纯后端且状态逻辑简单时跳过。
>
> prototype 是 design 阶段内层循环，不是新阶段。`task.json.prototype` 记当前轮次，`docs/design/<slug>/prototype/README.md` 逐轮记反馈、改动、验证和结论。每次进入或恢复都先跑 `mmw where`，照它给的 `load / do / then` 继续。

## 资产边界

- 逻辑原型持续放在 `docs/design/<slug>/prototype/`；UI 候选持续放在 `docs/design/<slug>/mockup/`。它们是正式设计资产，原地迭代并随设计提交，不另起临时原型、临时分支或新目录重做。
- 当前轮的截图、测试输出等验证证据放在 `docs/design/<slug>/prototype/runs/<三位轮次>/`，如第 2 轮放 `runs/002/`。
- `prototype/README.md` 由 `mmw prototype` 追加维护，不手改、不覆盖。源码保留当前形态，历史版本由 Git 保存。
- 大型供应商/API/性能取证属于 `evidence-campaign.md`，不混进本循环。

## 开始或恢复

先跑：

```bash
mmw where
```

按输出处理：

- `prototype_status=active`：读 `prototype_log`、`prototype_artifacts`、`prototype_question` 和 `prototype_run`，在现有产物上完成当前轮；禁止重新 start。
- `prototype_status=accepted`：把 `prototype_selected` 回灌设计文档。收到新反馈需要再改时，用文末的重新打开命令。
- `prototype_status=superseded`：照 `then` 回 propose，禁止继续修旧原型。
- `prototype_untracked=...`：照 `then` 给出的完整 `start --adopt` 命令接管全部旧产物，禁止删除后重建。
- 没有 prototype 状态且本设计触发原型：登记唯一验证问题；一个循环只验证一个能判真假的问题。

```bash
mmw prototype start \
  --kind <logic|ui|mixed> \
  --question '<本轮循环要判真的问题>' \
  --run '<可重复执行的运行或预览命令>'
```

## 每轮怎么做

1. 先读日志与现有产物，只做回答当前验证问题所需的最小改动；保留已经确认的状态、交互、视觉和文案。
2. 运行 `prototype_run`。逻辑原型覆盖成功、失败、空、非法转移、并发和回滚中实际存在的边界；UI 原型覆盖目标 viewport、加载、空、错误、成功和部分完成中实际存在的状态。
3. 把当前产物和运行结果呈现给用户走查。记录用户的原话或明确假设，不替用户宣布定稿，不并行进入 plan/build。
4. 把本轮事实一次写入 checkpoint。`--artifact`、`--evidence` 可重复；所有路径用 worktree 相对路径。
5. checkpoint 成功后立即把本轮源码、mockup、README 和证据作为同一个 Git commit 提交；不夹带本轮无关文件。下一轮继续修改同一份源码，不复制版本目录。

继续下一轮：

```bash
mmw prototype checkpoint \
  --feedback '<用户反馈或本轮假设>' \
  --change '<基于上一轮实际改了什么>' \
  --result '<怎么验证、结果是什么>' \
  --artifact docs/design/<slug>/<prototype|mockup>/<文件> \
  --evidence docs/design/<slug>/prototype/runs/<轮次>/<证据文件> \
  --verdict continue
```

用户明确接受当前候选后定稿；`--selected` 只列后续 plan/build 应采用的最终产物，可重复：

```bash
mmw prototype checkpoint \
  --feedback '<用户确认内容>' \
  --change '<本轮实际改动>' \
  --result '<最终走查结果>' \
  --artifact docs/design/<slug>/<prototype|mockup>/<文件> \
  --selected docs/design/<slug>/<prototype|mockup>/<最终产物> \
  --verdict accepted
```

验证证明选定方向本身不成立时：

```bash
mmw prototype checkpoint \
  --feedback '<击穿方向的事实>' \
  --change '<本轮实际改动>' \
  --result '<验证结果>' \
  --verdict superseded
```

然后照回执运行回 propose 的 `mmw handoff`，不在旧方向上另造一版。

accepted 后收到新反馈，先只登记重新打开，不提前填写尚未发生的改动或结果：

```bash
mmw prototype checkpoint --feedback '<新反馈>' --verdict continue
```

## 原型质量

### 状态与流程

prototype 是实现种子。状态机、reducer、schema、type shape 使用仓库语言和业务命名；每个合法转移和被拒绝的非法转移都可执行验证。不得用只为演示 happy path 的假逻辑代替真实状态边界。

### UI 与 mockup

用已装的前端设计与界面审计 skill 生成、打磨 HTML；结构与视觉是实现起点，技术栈在 build 时按仓库规范改造。

质量门：先区分 marketing/app/hybrid；定义色彩变量；不用默认字体栈；标签可见；标题贴对应区块；空状态有上下文与主操作；键盘、ARIA、触控尺寸、对比度和正文字号符合可访问性要求。禁用紫/靛渐变模板、三列图标圆圈、装饰圆圈、全居中、统一大圆角、装饰 blob/波浪、emoji 充当设计元素、彩色左边框卡片、套话 hero 和千篇一律等高节奏。

## accepted 后回灌

- 把选中逻辑原型的状态、合法/非法转移、schema 和结论写进设计文档；每条行为对应可执行验收。
- 把选中 mockup 的每个界面元素、状态、交互和文案原子级拆成 acceptance criteria；视觉契约写布局、间距、配色和组件，并指向具体 selected 文件。
- 冲突时以用户确认的 selected 产物为准，反写设计文档对齐。
- 未选中的候选留作迭代历史，不传给 plan/build。回灌完成后才走 design self-check、设计预审和 `/approve-design`。
