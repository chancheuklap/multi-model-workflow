# 模型角色映射

## 红线：写者 ≠ 审查者

每一道审**至少有一个视角的审查者与作者不是同一个模型**。

同一个模型的那个视角可以加派，但不能是唯一。任何审查者都不得是产出自己的那个会话。

**几个视角**和**每个视角派谁**是两个维度，不要混。几个视角由 `/mmw-review` 定，每个视角派哪个模型由这张表定。

| 审哪一道 | 被审的产物谁写的 | 几个视角 | 每个视角派谁 |
| --- | --- | --- | --- |
| ① spec 审 | Claude 主 agent（和用户对谈出来的，派不出去） | 2 | 两个视角都派 Codex |
| ② plan 审 | Codex 写计划工人 | 2 | 两个视角都派 Claude |
| ⑤ final 终审 | Codex 写码工人 | 3 | 每个视角派一个 Claude 加一个 Codex |
| ⑥ 合并集成审 | Codex 写码工人 | 不分视角，七个角度 | 一个 Claude 加一个 Codex，各走全套 |

③ 逐份验收和 ④ 合同门不派审查者，主 agent 自己做。

spec 的最终判定是用户敲的那道人工审批关卡，不是主 agent。

判断权在主 agent，不在审查者。**主 agent 全程不写代码。**

## 角色

| 角色 | 谁干 | 模型 | 档位 | 权限 |
| --- | --- | --- | --- | --- |
| 写码工人 | Codex headless | `gpt-5.6-terra` | high | 可写 |
| 写码工人 · 高风险档 | Codex headless | `gpt-5.6-sol` | medium | 可写 |
| 写计划工人 | Codex headless | `gpt-5.6-sol` | high | 只写计划与 issue |
| Codex 审查者 | Codex headless | `gpt-5.6-sol` | xhigh（① spec 审降 high） | 只读 |
| Claude 审查者 | Claude 会话内 subagent | 继承主 agent | — | 只读 |
| 编排与判定 | Claude 主 agent | 继承会话 | — | 写 spec，不写代码 |

**高风险档什么时候用**：这次要动的是计费、权限、数据迁移，或其他改错了不可逆的地方。由主 agent 判断后选档，不靠工人自己升级。

## 调用形态

- Codex headless：`codex exec`，模型和档位用 `-m <模型> -c model_reasoning_effort=<档位>` 显式钉。
- Codex 审查者一律 `--sandbox read-only`，审查者不许动代码。
- 审查者和写计划工人的方法论不进提示词，装在它自己的技能目录里（`/mmw-dispatching-agents` 旁边那个安装脚本干这件事）。审查者的提示词只给任务名、审什么、材料、是不是复审。
- Codex 会话续接（`codex exec resume`）不继承原来的护栏和模型档，追问时整套重新固定。
- 不用 `codex review`。
- 派给 headless 工人的 brief 要自包含：工人要用的规矩写进提示词，或者写进它读得到的仓库内文件。
- 派发前自检：brief 里提到的每个仓库内路径真实存在，缺了当场报错。

## 型号会过时

上表的型号是当前可用的值，不是约束。换型号只改这份文件，技能正文不出现任何型号。

Codex 报 `model is not supported when using Codex with a ChatGPT account`，八成是本机型号缓存旧了，不是这张表错。先让用户在 Codex 里刷一次，再看 `~/.codex/models_cache.json` 的 `models[].slug` 里有没有这个型号。**确认表真的过期之前不要改这张表，更不要动用户的 `~/.codex/config.toml`。**
