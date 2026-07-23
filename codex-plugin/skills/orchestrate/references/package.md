# Package · 正式安装包阶段操作指南

> develop 任务在 ④终审通过后进入本阶段。这里不替负责人执行开发模式或安装后测试；它只把两次负责人确认、scope 解析和 S1 release 完成事实固化为不可绕过的交接条件。

先在任务 worktree 找到唯一的仓库 release-package scope，然后初始化一次运行态：

```bash
mmw package init --scope <repo-relative-scope>
mmw package where     # 每个状态位首行是 token,第二行 next= 是确切下一步
```

## 1. 依 `where` 执行

| `where` 首行 | 下一步 |
| --- | --- |
| `NO-PACKAGE` | 本次没有 Windows 产品目标。确认 `mmw package exit-check` 为 `DONE` 后执行外层 `mmw handoff --conclusion pass`。 |
| `PAUSED-HUMAN:development-mode-test` | 等负责人完成实际开发模式功能测试；通过后由负责人身份写入 `mmw package confirm --gate development-mode-test --by <负责人>`。未通过不确认，直接 `mmw handoff --conclusion needs-redirection --to-phase build`。 |
| `RELEASE product=<id> manifest=<path>` | 依序为这把 key 驱动 S1 release。先运行 `mmw release init --manifest <worktree-absolute-manifest>`，然后**读 `${SKILL_DIR}/../release-flow/references/drive-loop.md` 整份**——release 循环的驱动合同(`stage run` / `dispatch` / `round next` / PAUSED 处置 / receipt / resume)单源在那份里,不自建循环——照它驱动到 `mmw release exit-check` 输出 `DONE`。在 `mmw release close` 前运行 `mmw package record-release --product <id>`，再关闭该 release state。release-flow 首个 stage `verify_key` 是 build 阶段「动了打包面就更钥匙」提示(B6)的**出包前兜底**:钥匙对不上产品活状态就在 Mac 当场 fail-loud、绝不上构建机;真撞 stale-key fail 说明落地时漏更了钥匙,按项目配钥匙规范补更后重跑。 |
| `PAUSED-HUMAN:installed-test` | 等负责人实际安装并从用户视角测试。通过后执行 `mmw package confirm --gate installed-test --by <负责人>`；未通过不确认，掉头回 build。 |
| `DONE` | 运行 `mmw package exit-check`，仅在输出仍为 `DONE` 时执行外层 `mmw handoff --conclusion pass`。 |

## 2. 成功边界

`record-release` 是正式 package 成功点：S1 已成功产出正式安装包，且其完整性与产物扫描已经通过。`installed-test` 是进入 closing 前的负责人手动工作流检查点，不是引擎自动 E2E，也不改变 release 成功的定义。

S1 的 P1 自愈如果产生新提交，会按 S1 path-gate 与 post-fix-gate 保护，并打包当时功能分支的 `HEAD`。这类提交与分支其余改动一起在 closing 审阅；不会宣称之前的 build ④终审已在该新提交上重跑。

## 3. 运行态边界

`package-state.json` 只属于当前 worktree。它首次初始化时固化 `base_commit..HEAD` 的目标；运行中目标变化会拒绝覆盖。只有从 package 以 `needs-redirection --to-phase build` 返回时，外层 flow 才会关闭旧 state，让新的 build、④终审和 package 周期以新 `HEAD` 重新初始化。
