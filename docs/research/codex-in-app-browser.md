# Codex 内置浏览器接入 MMW 调查

## 结论

Codex 宿主的 UI/UX 探索、视觉验收和用户走查应优先使用 Codex 内置浏览器。项目已有的 Playwright 或 Puppeteer 仍负责可重复执行的回归测试。两者承担不同责任。

MMW 当前没有 Codex 专用浏览器动作。共享技能只在 bug 诊断和外部系统取证中提到 Playwright。界面原型、视觉合同、实施验收和终审已经定义了可观察结果，但没有规定 Codex 如何打开页面、向用户展示页面、保留标签页和采集证据。

## 能力与责任边界

| 工作 | Codex 内置浏览器 | 项目浏览器测试 |
| --- | --- | --- |
| 浏览现有页面和本地 Web 应用 | 负责 | 不要求 |
| 用户查看、操作和标记 mockup | 负责 | 不适用 |
| 指定 viewport 检查响应式布局 | 负责交互式验收 | 负责稳定回归 |
| 检查可见 DOM、交互、截图和 console | 负责现场证据 | 负责可重复断言 |
| 多轮自动回归和 CI | 不负责 | 负责 |
| bug 的 tight red loop | 可用于复现和定位 | 最终需要可重复执行的命令 |

OpenAI 官方文档确认，内置浏览器可以预览本地页面、让用户留下视觉反馈、对字体、间距和颜色进行细化标记，并让 Codex 操作页面和验证结果。内置浏览器使用独立 profile；需要现有 Chrome profile 时才使用 Chrome 扩展。[Browser](https://learn.chatgpt.com/docs/browser)

当前 Codex 会话还暴露了 viewport 覆盖、整页截图、DOM snapshot、按 ARIA role 定位、可见 DOM 操作、console 日志和页面资源清单。`codex_app__open_in_codex` 负责把浏览器标签页展示在 Codex 面板。浏览器控制与面板展示是两项独立动作。

## MMW 受影响流程

| 流程 | 当前合同 | Codex 目标状态 | 优先级 |
| --- | --- | --- | --- |
| `/mmw-prototype` 的界面原型 | 用户在浏览器里翻看变体；只要求地址和 `?variant=` 取值 | 主 agent 在内置浏览器打开全部相关 mockup，显示浏览器面板，保留标签页，等待用户标记和选择 | 最高 |
| `/mmw-grilling` 的 UI 讨论 | 先调查现状，再一次问一个决定 | 页面或 mockup 已存在时，先把全部相关页面交给用户标记；标记成为后续问题的证据 | 最高 |
| `/mmw-implement` 的逐份验收 | 主 agent 验证 ticket、测试和意图 | 界面 ticket 增加内置浏览器验收。主 agent 走通黄金路径和本次相关边界状态，再决定是否集成 | 最高 |
| `/mmw-review` 的终审 | 有界面时对照选中原型和视觉合同 | 主 agent 提供运行页面的截图、DOM 和 console 证据；审查者基于证据审查，不要求只读 subagent 控制浏览器 | 最高 |
| `/mmw-planner` 的验证语言 | 界面需要 DOM 断言、截图、响应式和人工走查 | 计划明确区分自动回归命令与 Codex 内置浏览器人工审批关卡 | 高 |
| `/mmw-to-spec` 的视觉合同 | 写 viewport、视觉规格、交互行为和状态变体 | 浏览器标记和选中页面成为视觉合同出处；每个 viewport 和状态写成可验收结果 | 高 |
| `/mmw-diagnosing-bugs` 的反馈 loop | headless Playwright 或 Puppeteer 是第 4 种 loop | 内置浏览器负责复现、截图、DOM 和 console 取证；Phase 1 完成前仍需收敛成可执行的 red loop | 中 |
| `/mmw-prototype` 的外部系统取证 | 优先使用项目已有 Playwright；没有入口时记录人工步骤 | 内置浏览器可补足交互式取证并保存截图、DOM 和 console；多轮测量仍使用可重复脚本 | 中 |

Codex 的宿主动作应留在物化层。Pi 和 Claude Code 继续使用各自现有浏览器入口。共享技能只保留 UI/UX 验收语义，Codex 物化产物写入内置浏览器的具体操作。

## UI/UX 浏览器合同

Codex 把页面交给用户走查时，应执行以下合同：

1. 先清点全部相关页面。多份 mockup 各占一个标签页，不能用一个标签页依次覆盖。
2. 使用 Codex 内置浏览器控制页面。使用 Codex 面板打开能力向用户展示页面。
3. 页面显示后读取实际可见状态。没有确认可见时，不能声称已经打开。
4. 只在视觉合同指定 viewport 或需要验证断点时覆盖 viewport。完成后恢复默认值。
5. 每个相关状态至少保存截图。交互异常时同时保存 DOM 和 console 证据。
6. 用户需要继续操作时，把标签页保留为 `handoff`。最终页面交付时保留为 `deliverable`。
7. `finalize` 是本回合最后一个浏览器动作。后续回合先接管现有标签页，不重复创建。
8. 页面交给用户后停止修改和导航。等待用户完成标记或给出选择。

## 指定 session 暴露的问题

Session `019fcfb9-ccb2-7392-9b26-ca9d1a93a61b` 提供了四类失败证据：

| 失败 | 可观察结果 | 需要固化的规则 |
| --- | --- | --- |
| 先选择 Playwright | 用户明确要求使用内置浏览器后才切换 | UI/UX 人工走查在 Codex 中默认使用内置浏览器 |
| 用一个标签页检查四份 mockup | 用户无法同时比较和逐页标记 | 先清点页面，每份 mockup 保留独立标签页 |
| 把标签页控制等同于面板可见 | agent 声称页面已经打开，用户实际看不到 | 浏览器控制与 Codex 面板展示分别验证 |
| 回合结束时没有正确保留全部页面 | 标签页被清理，用户两次要求重新打开 | 按任务状态使用 `handoff` 或 `deliverable`，并让 `finalize` 成为最后动作 |

该 session 还在两个调查 subagent 运行期间继续分析同一批 mockup。这个重叠执行问题已经由提交 `06ee7e63` 修复：Codex 每个派发点都会要求主 agent 等待，禁止重做 subagent task。

## 验证方式

后续实现应在 Codex App 真实宿主完成以下验收：

1. 打开至少四份本地 mockup，并在同一 Browser 面板中保留四个独立标签页。
2. 回合结束后，用户仍能打开、切换和标记全部页面。
3. 下一回合接管已有标签页，不新增重复页面。
4. 对一个响应式页面验证两个 viewport，并在完成后恢复默认 viewport。
5. 对加载、空、错误和成功状态分别采集截图；错误状态同时采集 console。
6. 派出调查 subagent 后，主 agent 不再执行相同调查，只等待报告并验证关键出处。

## 未确认边界

- 公开文档没有承诺每个 Codex 后台 Worktree 任务都具备 Browser plugin。浏览器验收应由当前可见的主 agent 负责，后台 `worker` 只交回运行方式和自动测试结果。
- Developer mode 可以提供完整 Chrome DevTools Protocol 能力，但它受用户设置、组织策略和单次批准约束。基础 UI/UX 流程不能依赖它始终开启。
- 当前会话的内置浏览器接口与公开文档对文件上传的描述不完全一致。MMW 不应把自动文件上传写成基础浏览器合同。
