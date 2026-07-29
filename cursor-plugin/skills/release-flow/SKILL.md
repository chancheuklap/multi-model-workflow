---
name: release-flow
description: "出包 / 打包 / 发布某个产品时主动使用(如「出个小黄鸭的包」「打包小鹦鹉」)。你(主线程 Agent)是判断层,驱动通用 release-flow 引擎:跑阶段 → 诊断 → 自愈(P2 重生 / P1 修复 / P0 停) → 收敛到安装包就绪,或带精确定位停在需要人的那一步。引擎零项目知识,只认仓库登记的一份 adapter manifest。"
---

# Release Flow · 出包自愈入口

主线程入口。**你是判断层**:自然语言触发一次出包后,你按引擎状态连续完成机械驱动,不盯屏、不手工排查。引擎是确定层(状态机 / 分级 / path-gate / 熔断全在里面),你只做「跑一步 + 诊断 + 把结果喂给引擎」,不重写分级、不碰安全逻辑。

`mmw` ≡ `bash "${SCRIPTS}/mmw.sh"`;`mmw release X` = 通用引擎。下面 Step 0 一次定位得出绝对路径。

## Step 0 · 定位引擎,再跑 `release where`(它自带指路)

```bash
MMW_ROOT=""
if [ -n "${MMW_ENGINE_ROOT:-}" ] && [ -f "$MMW_ENGINE_ROOT/scripts/mmw.sh" ]; then
  MMW_ROOT="$MMW_ENGINE_ROOT"
fi
if [ -z "$MMW_ROOT" ]; then
  for cand in \
    "$HOME/.cursor/multi-model-workflow-engine" \
    "$(pwd | sed -n 's|\(.*multi-model-workflow\)/.*|\1/cursor-plugin|p')" \
    "$(pwd)/cursor-plugin"
  do
    [ -f "$cand/scripts/mmw.sh" ] || continue
    MMW_ROOT="$cand"
    break
  done
fi
MMW="$MMW_ROOT/scripts/mmw.sh"
printf 'mmw       = %s\nSKILL_DIR = %s\n' "$MMW" "$HOME/.cursor/skills/release-flow"
```

若 `$MMW` 不存在，先跑 `bash cursor-plugin/scripts/install-local-surface.sh`，或设 `MMW_ENGINE_ROOT`。

`mmw X` ≡ `bash "$MMW" X`(每个新 shell 用回显的绝对路径)。然后无脑先跑:

```bash
bash "$MMW" release where
```

- **报 `STAGE:` / `RETRY-STAGE:` / `PAUSED:` / `SUCCESS:` / `CORRUPT:` / `FAILED-STAGE:` / `NO-STAGES:`**(已有 release state)→ 不重开。直接读 `${SKILL_DIR}/references/drive-loop.md`：它从当前 state 连续驱动至安装包就绪，或读取回执交回判断层。
- **报 `ERROR: 无 release-state(先 release init)`(退非零)**→ 没有在飞的 loop → 进 Step 1 起一次新的。

## Step 1 · 登记(买票)→ 起 loop → 交给 drive-loop

1. **认产品**:从对话认出要出哪个产品(「小黄鸭」→ `duck`、「小鹦鹉」→ `parrot`、「小刺猬」→ `hedgehog`;产品↔代号见项目 PROJECT.md)。判不准就问一句收窄。

2. **取仓库登记的那份票(adapter manifest)**:仓库按适配合同把 conform 的 manifest 登记在约定位置。在**当前仓库**找该产品那份(约定:`*.release-adapter.json`,读其 `product` 字段匹配):
   ```bash
   grep -rl '"product": *"<代号>"' --include='*.release-adapter.json' .
   ```
   找不到 = 该仓库没为这个产品登记出包 → 告诉用户「该产品未适配出包」,停,别硬造。

3. **起 loop**(引擎校验 manifest 合规才落状态,不合规 fail-loud 请人改):
   ```bash
   bash "$MMW" release init --manifest <找到的 manifest 绝对路径>
   ```

4. **交给驱动方法论**:读 `${SKILL_DIR}/references/drive-loop.md`，从 init 后的 state 连续机械驱动；只在 `DONE` 或引擎 surface 时停止。**本文到此为止,不重复循环细节。**

## 边界

- 入口只做:断点恢复 / 认产品 / 取票 / 起 loop → 交 drive-loop。**循环怎么跑、P0/P1/P2 怎么处置、何时推进修复轮次、断点续传、回执交人全在 `references/drive-loop.md`**,到那步再读。
- **你是判断层,不是执行层里的手**:引擎管安全(path-gate / 熔断 / 分级),你不重写。你只把每一步的诊断结果如实喂给引擎,让它裁决。
- 出包是**跨机器**的:你在 Mac 驱动 loop,stage(真出包动作)按 manifest 定义的跑法落地(agentflow = Win-PC 构建机),你照现有真机路子支使,不自己在 Mac 瞎跑构建。
