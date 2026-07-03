# codex-skills

给 **Codex Worker** 用的 skill 源(Codex 读不到 Claude 的 `plugin/`,所以派给 Codex 的纪律 / 方法得自包含在这里)。plugin 派 Codex 时,prompt **只给 stage / worktree / 文档路径 + 指向对应 skill**,方法本体在 skill 里渐进加载(开工前不占 Codex context),**不在 prompt 里重复**。

## 安装(软链进 Codex 自动扫描的 skill hub)

Codex 自动扫描 skill hub `~/.agents/skills/`(与 `/tdd`、`write-design-doc` 等同一套,靠扫描发现、**不需要写 `~/.codex/config.toml`**)。把两份 skill 软链进去即可:

```bash
ln -s "$(pwd)/codex-skills/worktree-build"  ~/.agents/skills/worktree-build
ln -s "$(pwd)/codex-skills/worktree-review" ~/.agents/skills/worktree-review
```

装好后 Codex 侧 `worktree-build` / `worktree-review` 可用,与已装的 `/tdd`(worktree-build 硬依赖)配合。**装是硬前提**:没装则派发失败可见(Codex 报找不到 skill),不搞"没装也能跑"的降级。

## worktree-build(build 阶段落地)

plugin build 阶段派 Codex 进 worktree 落地一份计划时用。

- `SKILL.md` — 落地总纲(5 步循环 + 必读三文档 + 收工回执契约 + 边界)。
- `references/discipline.md` — 防过度设计/兜底、契约类型、登记+迁移(开工读一次)。
- `references/tests.md` — 测试对标仓库治理文档、测公开行为/mock/权威层(写测试前读)。
- `references/when-stuck.md` — 3-strike / 计划冲突 / 缺输入(卡住才读)。

## worktree-review(审闸 review 阶段)

plugin 审闸(design/plan/final/merge-impl)派 Codex 独立审一份产物时用。`review.sh` 打印的协调帮手 brief 里,Codex prompt **只给 stage + 视角 + Source**,指向本 skill;**不给任何 plugin 内路径**。③合同门(plan-impl)是 Claude 机器核、不派 Codex,不在此。

- `SKILL.md` — 审查总纲(确认 stage+负责哪路视角 → 读方法 → 读 stage 角度 → 只读边界 → Return Contract)。
- `references/method.md` — 共享审查纪律(只读边界 / 不信自述 / 方向-方法-地基五问 / 防幻觉四件套 / Finding 字段 / 分级 / Return Contract / 禁用红线),开工读一次。
- `references/{design,plan,final,merge}.md` — 各 stage 审查角度,按被派的 stage 读一份。
