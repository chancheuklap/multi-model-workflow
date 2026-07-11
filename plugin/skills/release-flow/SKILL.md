---
name: release-flow
description: "出包 / 打包 / 发布某个产品时主动使用(如「出个小黄鸭的包」「打包小鹦鹉」)。你(主线程 Agent)是判断层,驱动通用 release-flow 引擎:跑阶段 → 诊断 → 自愈(P2 重生 / P1 隔离修 / P0 停) → 收敛到产物,或带精确定位停在需要人的那一步。引擎零项目知识,只认仓库登记的一份 adapter manifest。"
---

# Release Flow · 出包自愈入口

主线程入口。**你是判断层**:自然语言触发一次出包,你驱动通用引擎逐步跑、后台自愈,不盯屏、不手工排查。引擎是确定层(状态机 / 分级 / path-gate / 熔断全在里面),你只做「跑一步 + 诊断 + 把结果喂给引擎」,不重写分级、不碰安全逻辑。

`mmw` ≡ `bash "${SCRIPTS}/mmw.sh"`;`mmw release X` = 通用引擎。下面 Step 0 一次定位得出绝对路径,**不依赖环境变量**,Claude / Droid 通用。

## Step 0 · 定位 plugin,再跑 `release where`(它自带指路)

```bash
if [ -n "${DROID_PLUGIN_ROOT:-}" ] || printf %s "$PATH" | grep -q '/.factory/bin'; then P=~/.factory/plugins; else P=~/.claude/plugins; fi
MMW="$(find "$P" -type f -path '*multi-model-workflow*/scripts/mmw.sh' 2>/dev/null | head -1)"
printf 'mmw       = %s\nSKILL_DIR = %s\n' "$MMW" "$(dirname "$(dirname "$MMW")")/skills/release-flow"
```

`mmw X` ≡ `bash "$MMW" X`(每个新 shell 用回显的绝对路径)。然后无脑先跑:

```bash
bash "$MMW" release where
```

- **报 `STAGE:` / `RETRY-STAGE:` / `PAUSED:` / `SUCCESS:`**(有在飞的 loop)→ 已有一次出包在飞(引擎单飞锁,`release init` 会拒绝并发)。**断点恢复**:直接读 `${SKILL_DIR}/references/drive-loop.md` 从当前状态续驱动,不重开。
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

4. **交给驱动方法论**:读 `${SKILL_DIR}/references/drive-loop.md`,按它从头驱动到 SUCCESS / PAUSED。**本文到此为止,不重复循环细节。**

## 边界

- 入口只做:断点恢复 / 认产品 / 取票 / 起 loop → 交 drive-loop。**循环怎么跑、P0/P1/P2 怎么处置、断点续传、回执交人全在 `references/drive-loop.md`**,到那步再读。
- **你是判断层,不是执行层里的手**:引擎管安全(path-gate / 熔断 / 分级),你不重写。你只把每一步的诊断结果如实喂给引擎,让它裁决。
- 出包是**跨机器**的:你在 Mac 驱动 loop,stage(真出包动作)按 manifest 定义的跑法落地(agentflow = Win-PC 构建机),你照现有真机路子支使,不自己在 Mac 瞎跑构建。
