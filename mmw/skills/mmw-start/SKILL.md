---
name: mmw-start
description: 开一个任务：起名、建工作树、写状态、进去。
argument-hint: "<需求>"
disable-model-invocation: true
---

用户敲了这条，就是要做一件新东西：任务开在探路，往下走完整条主干。

需求聊到能起出任务名就建树，深入的对话放进探路做——建树之前聊的每一轮都在盘外，关掉会话就没了。

## 怎么做

1. **起任务名**：动作加对象，短横线连写，只用小写字母、数字和短横线，像 `add-oauth-login`、`split-billing-ledger`。`update`、`refactor`、`task-1` 这类泛称隔一个月认不出是哪件事。

2. **建树之前把任务名念给用户，等他改或者点头。**它建了树就写进分支名与目录名，再改要拆掉重来。

3. 跑这一句：

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/task.sh" new <任务名> mmw-wayfind
   ```

   忽略清单、工作树、`.mmw/task.json`、`.mmw/sidelines.md` 由它一次落齐，输出头四行是任务名、工作树路径、分叉点、起点。

4. `EnterWorktree({ path: "<上一步回的工作树路径>" })`。这个任务往后每一步都在那棵树里干：状态、旁路清单、代码改动都在那儿，留在主仓库下一份技能读不到状态。

5. 把用户的需求原话写进 `.mmw/task.json` 的 `note`。它没有别的地方存得下，新会话敲 `/mmw` 只念得出这一句。

6. 读 `mmw-wayfind`，接着干。

---

## 线下 · 不是技能内容

**`${CLAUDE_PLUGIN_ROOT}` 在技能正文里会被换成插件的安装目录**（官方插件参考的替换表：Skill and agent content — anywhere the placeholder appears）。旧插件那段读 `installed_plugins.json` 找激活安装位的定位块因此不搬，命令直接写绝对路径。

**为什么开任务分成两个入口**：探路那条要往下走完整条主干，`mmw-fix` 那条从取证起步、改完就收尾，两条从第一步起就不一样。塞进一份技能得先摆一张判据表再分岔，读的人每次都要先读一遍与自己无关的那一半。

**来源**：`plugin/scripts/prepare.sh`（315 行）——建工作树、从当前 HEAD 分叉、回执点名 `EnterWorktree` 照它；它第 8 行「路由由 LLM 当场判，不在本脚本」与这里脚本只校验拼写的分工一致。两个入口对应旧插件 `routes.json` 里 `develop` 与另外两个场景预设的分界，只取「一开始就分开」这一点，不取预设的阶段序列。

**没搬的**：入口能力判定那六种治理能力与「须给用户原话当证据」——敲了这个命令就是要用；三十九字段任务档案；场景预设的阶段序列与强制走完。
