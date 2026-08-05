# Skill Authoring

这个上下文定义 MMW 工作流如何被写成可预测技能并物化到不同宿主。它不重新定义各工作流拥有的业务术语。

## Language

**skill source**：
`mmw/skills/` 下拥有共享流程语义的技能文档。宿主产物不得成为反向修改 source 的权威依据。
_Avoid_: 物化技能、安装缓存

**物化技能**：
由 skill source 生成、已经替换宿主动作块的宿主专用技能。它必须与 source 的共享语义一致。
_Avoid_: skill source、手写宿主分支

**model-invoked skill**：
保留 `description`、可由 agent 根据请求自动调用的技能。它用持续 context load 换取自动发现。
_Avoid_: capability、tool

**user-invoked skill**：
没有 `description`、只能由用户显式调用的技能。它不产生持续 context load，但增加用户的 cognitive load。
_Avoid_: command、workflow

**description**：
技能的机器可读触发条件，也是 model-invoked skill 常驻上下文的顶层 context pointer。
_Avoid_: frontmatter、摘要

**context pointer**：
留在当前上下文中、说明何时读取某份未加载材料的引用。pointer 的措辞决定材料能否可靠加载。
_Avoid_: 普通链接、权威引用

**context load**：
model-invoked skill 的 description 持续占用模型上下文与注意力的成本。
_Avoid_: token 价格、文件长度

**cognitive load**：
用户为了记住 user-invoked skill 及其调用时机而承担的认知成本。
_Avoid_: context load、操作步骤数

**router skill**：
把请求分到其他技能、自己不执行目标工作的技能。
_Avoid_: menu、registry、业务实现技能

**information hierarchy**：
按即时需要程度排列 skill 内容的层级，依次是文件内步骤、文件内 reference 和 context pointer 后的 disclosed reference。
_Avoid_: 目录结构、排版

**leading word**：
用已有概念压缩并稳定 agent 行为的高信息词。它在 description 中帮助调用，在正文中帮助执行。
_Avoid_: keyword、口号

**completion criterion**：
让 agent 可以判定一个步骤何时真正完成的清晰且有要求的条件。
_Avoid_: 停止建议、后续步骤

**premature completion**：
agent 因注意到后续步骤而在当前步骤满足 completion criterion 前结束的失败模式。
_Avoid_: thin legwork、普通遗漏

**single source of truth**：
每项技能语义只存在于一个权威位置的状态。物化产物复制 source 内容不改变 source 的所有权。
_Avoid_: 重复说明、多个同等权威版本

**duplication**：
同一技能语义被写入多个权威位置的失败模式。
_Avoid_: leading word 重复、生成产物

**sediment**：
失去 relevance 的旧内容因为只增不删而逐层累积的失败模式。
_Avoid_: 所有历史背景、正常 reference
