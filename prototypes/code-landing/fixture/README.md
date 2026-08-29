# 测试台：虚构的票 + 测试小仓库

改 `#60` 的每一处（第 2–10 节），都拿这里的东西跑一遍那一处，看票上出现了什么。这个目录里没有任何要发布的产品代码。

## 三条命令

```sh
cd prototypes/code-landing/fixture
uv run pytest -q                                  # 8 passed
python3 -m http.server 8765 --directory site      # 实现页 http://127.0.0.1:8765/index.html?scenario=default
python3 -m http.server 8766 --directory baseline  # 基线页 http://127.0.0.1:8766/Component · 任务队列.dc.html
```

基线页不联网：`support.js` 原本从 unpkg 取的 React、ReactDOM、Babel 三个脚本已经放进 `baseline/vendor/`，`support.js` 里的三个地址改成了 `./vendor/…`（文件内容与 unpkg 上的一致，`support.js` 里的 SRI 哈希照原样保留，能校验通过）。

## 两张虚构的 issue

| issue | 是什么 |
| --- | --- |
| [#76](https://github.com/chancheuklap/multi-model-workflow/issues/76) | `[fixture] spec: 任务队列侧栏的任务计数与空态`——按 `to-spec` 模板写的虚构 spec，两个编号小节 + Testing Decisions |
| [#77](https://github.com/chancheuklap/multi-model-workflow/issues/77) | `[fixture] 任务队列侧栏：任务计数与空态`——虚构的票，Parent 指向 #76 |

两张都不贴 `ready-for-agent`：它们不是活，不派给任何人。票做脏了（评论、勾选、标签被改）就照 #77 的正文重开一张同样内容的。

#77 的四条验收标准各测一种情况：

| 标准 | 形态 | 现在跑会怎样 |
| --- | --- | --- |
| AC1 | `CHECK` 是 pytest 命令 | 过 |
| AC2 | `EXPECT: count 6` 与实际输出 `count 5` 故意不符 | 不过 |
| AC3 | 只有 `MANUAL:` 行，没有命令 | 不跑 |
| AC4 | `CHECK` 调 `visual-parity.py` | 工具在 #60 第 2 节才做，做好后应当过（见下） |

## 目录里有什么

| 路径 | 用途 |
| --- | --- |
| `src/fixture_app/text.py` | `slugify`——被 `queue.py` 的两个函数调用；测「改函数前 grep 每个调用方」那句用它 |
| `src/fixture_app/queue.py` | `task_slug`、`scene_slug`（两个调用方）、`queue_summary`（计数与空态） |
| `tests/` | `uv run pytest` 的测试，8 条 |
| `site/` | 实现页，`?scenario=default` 与 `?scenario=queue-empty` 两种 |
| `baseline/` | 基线目录：组件页 `Component · 任务队列.dc.html`、`styles/`、`data/`、`support.js`、`vendor/` |
| `baseline/scenes.json` | 场景清单：`default`（五个任务）、`queue-empty`（空态），各带页面与 props |

## 实现页与基线现在差多少

2026-08-29 用 Playwright 在 1440×900 下量过：像素差 **0.0%**、ARIA 树 diff **0 行**、控制台 0 条 error，全程离线（拦掉了所有 https 请求）。`site/index.html` 用的是与基线同一份 `styles/tokens.css` 和 `styles/product-workbench.css`，DOM 结构照 `Component · 任务队列.dc.html` 的模板展开，任务数据与 `baseline/data/fixtures.js` 的 `wb.tasks(wb.projects[0])` 同名同序。

所以 #77 的 AC4 是一条**应当通过**的 UI 验收标准；把 `--scenes` 里的场景换错（拿 `queue-empty` 的基线比 `default` 的实现）就是现成的负控制。

基线目录的非默认场景还没有各自的页面：Claude Design 的场景是 Tweaks 面板上的 props，不是 URL 参数（`prototypes/code-landing/ui-gate/EXP/README.md` 的 Open 一段）。`scenes.json` 把「场景名 → 页面 + props」写成了数据，等 `visual-parity.py` 决定用哪种方式渲染非默认场景。
