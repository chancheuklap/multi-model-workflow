# 人工验收清单

spec「Testing Decisions」里需要真实票与 Herdr 会话的部分。离线测试（`tests/run.sh`）只覆盖 models.md 解析、前置检查的报错路径、frontier 判定；下面每一项都要在真实仓库里跑，跑完把结果记在本次落地的 spec issue 评论里。herdr 控制类命令的断言基于其 JSON 输出字段；读屏仅限 blocked 时取问题文本这一处。

## ① 单票穿行

- [ ] 一张真实小票（`ready-for-agent` + `worker:junior`），在 Herdr 会话里运行技能，全程无人工介入跑到 PR 开好
- [ ] landing-closeout 的 tracer bullet 检查项全部成立：票已关闭、下游依赖已解除、票分支存在且 commit 引用票号、PR 已开、关卡逐条勾选且带 EVIDENCE、复验判决评论存在且绑定 commit
- [ ] 全程无一次向用户提问（编排者会话与工人 pane 都没有）
- [ ] 票评论里有四条留痕：派给谁（宿主 kind、模型串、agent 名、worktree 路径）、判决、分诊结果、重试原因（没有重试就写「无」）

## ② 依赖对

- [ ] 两张有原生阻塞关系的票；上游收尾（关闭）后，frontier 查询的输出（`scripts/frontier.py` 的 stdout）出现下游票号
- [ ] 下游票被自动派发，简报第 3 段含上游票的产出摘录
- [ ] 刻意安排一对「看似无关实则同文件」的票：规划者把它们判为串行（计划评论「### 并行分组」里不同组）

## ③ 过夜批

- [ ] 一批真实票跑整夜；晨检：PR 数 = 通过票数，停车 issue 数 = 停车次数，每票评论里四条留痕完整，无一次向用户提问
- [ ] 通知只收到两类：每次停车一条、循环终止一条

## 停车路径

- [ ] 一张故意含未决问题的票：工人进入 `blocked`（`herdr agent get` 的状态字段），编排者读屏取到问题文本
- [ ] 停车 issue 正文四段齐全（Question / Options / Consequences / Default），标签 `blocked:decision`，`gh api …/issues/<n>` 的父子关系指向任务父 issue
- [ ] 推送通知到达手机

## 复验轮次上限

- [ ] 一张故意修不好的票：第一次复验 fail → 回原工人修一轮 → 第二次复验（同一个复验者 subagent 续用）fail → 停车，不出现第三次复验
- [ ] 票评论里两条判决都绑定各自的 commit

## 失败分类与升级链

- [ ] 初级工人两败（同票）→ 高级工人接手（票的定级标签只升不降）→ 高级再败 → advisor 被派发 → 仍无解 → 停车
- [ ] Herdr 报 `unknown` 期间工人仍在 commit：编排者没有把它当死亡（不重派、不停车）
