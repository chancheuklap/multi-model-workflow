# spec 归档:GitHub Wiki

代码落地后，spec 与计划文档转成 GitHub Wiki，本地那两份随任务分支删掉。Wiki 从此是这份 spec 的唯一真相源。

任何时候打开 Wiki，看到的都是「这个仓库现在是怎么设计的」。它只有这一类内容，不夹带过程材料——map、审查留痕、终审报告都不进（去向见 `issue-tracker.md`）。

## 前提

Wiki 必须先在网页上手建一页，clone 地址才存在。检测：

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
git ls-remote "https://github.com/$REPO.wiki.git" >/dev/null 2>&1
```

失败就是还没初始化。**告诉用户去仓库的 `/wiki` 页建一页任意内容，不要试图绕过**——没有 API 能替他建。

推送鉴权走 git 凭据助手，`gh auth setup-git` 跑过一次即可，之后普通 `git push` 就能推。

## 落点

clone 到 `.worktrees/.wiki/`。`.worktrees/` 整个在 `.gitignore` 里，所以它不会污染任何任务分支。

第一次 clone，之后 pull，不用每次重拉：

```bash
[ -d .worktrees/.wiki ] && git -C .worktrees/.wiki pull \
  || git clone "https://github.com/$REPO.wiki.git" .worktrees/.wiki
```

Wiki 只有默认分支会发布。别在它上面开分支。

## 命名

**全部平铺在 Wiki 根目录，一份 spec 一页**，文件名 `Spec-<slug>.md`。

slug 就是 worktree 名、分支名、`docs/specs/<slug>/` 的目录名——同一个词贯穿四处。`phone-login` 这份 spec 的页面就是 `Spec-phone-login.md`。

不要建子目录。GitHub Wiki 的页面命名空间是平的：文件放进子目录也不改变标题和网址，页面名仍须全局唯一，唯一换来的是每个目录一个侧边栏，而网页编辑器改不了子目录的侧边栏。层级只能编进文件名，`Spec-` 前缀就是干这个的。

标题禁用 `\ / : * ? " < > |`，slug 用连字符。

## 一页放什么

| 段 | 内容 |
| --- | --- |
| 抬头 | 一句话说这份 spec 解决什么问题 |
| 落地信息 | 父 issue 链接、合并的 PR、落地日期 |
| spec 正文 | `docs/specs/<slug>/` 的定稿 |
| 计划章节 | 每张 ticket 一节，来自 `docs/plans/<slug>/` |
| 相关决策 | **只放链接**指回仓库的 `docs/adr/`，用完整 URL |

计划不单独开页。一份 spec 拆八张 ticket 就开八页，会碎成没人看的东西。

ADR 绝不复制进 Wiki——它在仓库里跟代码同一个提交演进，复制一份就立刻有两个版本各自漂移。

Wiki 不支持自动生成目录，长页面靠标题分节。页间链接用 `[[Spec-phone-login|手机号登录]]`。

## 导航

每次写入后重新生成这两个文件，一起提交：

- **`Home.md`**——一张表，每份 spec 一行：slug、一句话、落地日期、PR 链接。
- **`_Sidebar.md`**——Home 加 spec 页列表，按落地时间倒序。

GitHub 不会按目录自动生成导航树，没有 `_Sidebar.md` 时只有一个平铺的 Pages 列表。所以这两个文件不是可选装饰，是唯一的导航。

## 同一份 spec 再次改动

slug 相同就是同一份 spec 的演进：**覆盖那一页，在页尾追加一条修订记录**（日期、PR、一句话改了什么）。不要新开 `Spec-phone-login-v2`。

Wiki 本身是 git 仓库，旧版本天然留着，页面只呈现当前状态。

## 写入时机与顺序

收尾时自动生成页面内容，**推送前把 diff 给用户看、等他点头**。推送到 Wiki 是出站动作，要人确认；但忘了转就是永久丢失（本地文档紧接着要删），所以不能纯靠用户记得敲命令。

顺序不能反：

1. 推 Wiki
2. 核验（下一节三条）
3. 删本地 `docs/specs/<slug>/` 与 `docs/plans/<slug>/` 并提交
4. 合回上一层

## 核验

三条全过才允许删本地文档。任何一条不过就停下报告，不要继续。

1. `.worktrees/.wiki/Spec-<slug>.md` 存在且非空
2. `Home.md` 与 `_Sidebar.md` 里都有这一页的条目
3. 推送成功——`git -C .worktrees/.wiki rev-parse HEAD` 与 `git -C .worktrees/.wiki rev-parse @{u}` 一致

## 别的要知道的

- **没有 API。** `gh` 没有 wiki 命令，REST 也没有 wiki 端点。读写一律 clone 后走普通 git。agent 想查历史 spec，是 clone 再本地搜，不是 `gh`。
- **软上限 5000 个文件。** 一份 spec 一页，撞不到。
- **别装 Factory droid 的 `/install-wiki`。** 那条 CI 每次推到主线就从代码全量重生成 Wiki，跟我们这种一次追加一页、且丢了无法重生成的内容天然冲突。同一个仓库二选一。
