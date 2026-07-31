---
name: mmw-start
description: 开一个任务：起名、建工作树、写状态、进去。改一处已知的地方，需求前面加 fix。
argument-hint: "[fix] <需求>"
disable-model-invocation: true
---

用户敲了这条，就是要把一件事立成任务。$ARGUMENTS 是他这次要做的事。

先把任务建起来，再往下细聊。建树之前聊的东西没有地方存，关掉会话就全丢了。

## 步骤

1. **看开头是不是 `fix`。**是，那个词后面的话才是需求，这件事走短路径；不是，整串都是需求，走主干。用户没写 `fix` 你就当他没写，这件事是大是小不由你替他判。

2. **起一个任务名。**动作加对象，全小写，短横线连写，例如 `fix-payment-retry`、`add-oauth-login`。名字要具体到隔一个月还认得出是哪件事——`update`、`refactor`、`task-1` 认不出。

3. **把任务名念给用户，等他改或者点头。**这个名字会写进分支名和目录名，建完树再想改就得拆掉重来。

4. **建树。**跑下面这句。最后一个参数：开头是 `fix` 填 `mmw-fix`，不是填 `mmw-wayfind`。

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/task.sh" new <任务名> <mmw-fix 或 mmw-wayfind>
   ```

   它一次建好工作树和 `.mmw/` 下的状态文件，然后打印四行：任务名、工作树路径、分叉点、起点。

5. **进工作树。**调 `EnterWorktree({ path: "<上一步打印的工作树路径>" })`。这个任务往后每一步都在树里做，状态、代码、旁路记录都存在那儿；留在主仓库的话，下一份技能读不到状态。

6. **把用户的原话写进状态。**打开工作树里的 `.mmw/task.json`，把 $ARGUMENTS 原样填进 `note` 字段。这句话别处存不下，下次新开会话，`/mmw` 就是靠它告诉用户这个任务在做什么。

7. **接着干。**开头是 `fix` 就读 `mmw-fix`，不是就读 `mmw-wayfind`。

---

## 线下 · 不是技能内容

**`${CLAUDE_PLUGIN_ROOT}` 在技能正文里会被换成插件的安装目录**（官方插件参考的替换表：Skill and agent content — anywhere the placeholder appears）。旧插件那段读 `installed_plugins.json` 找激活安装位的定位块因此不搬，命令直接写绝对路径。

**`fix` 只决定路由，不是一套预设的阶段序列**：带了就落 `mmw-fix`、往下按那一份走；没带就落探路、走主干。后面每一步照样靠用户敲命令走。

**补全提示只放占位符**：`[]` 可选、`<>` 必填，照官方示例与本机在跑的技能（`impeccable`、`save-x-article`）的形状写，不往里塞说明句。`fix` 是什么意思写在 `description` 里——这一份 `disable-model-invocation`，它的 `description` 不进模型上下文，就是给用户看的那一行。

**来源**：`plugin/scripts/prepare.sh`（315 行）——建工作树、从当前 HEAD 分叉、回执点名 `EnterWorktree` 照它；它第 8 行「路由由 LLM 当场判，不在本脚本」与这里脚本只校验拼写的分工一致。`fix` 这一层对应旧插件 `routes.json` 里 `develop` 与 `bug` / `small-change` 的分界，只取「一开始就分开」这一点；旧的两个场景在新插件里并成一条。

**没搬的**：入口能力判定那六种治理能力与「须给用户原话当证据」——敲了这个命令就是要用；三十九字段任务档案；场景预设的阶段序列与强制走完。
