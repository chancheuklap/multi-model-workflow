# Codebase Design

这个上下文提供 MMW 设计和重构代码时使用的共同结构语言。它的术语按调用关系定义，不按代码规模定义。

## Language

**module**：
任何具有 interface 和 implementation 的代码单元，可以是函数、类、包或跨层切片。
_Avoid_: 单元、组件、服务

**interface**：
调用方正确使用一个 module 必须知道的全部事实，包括签名、不变量、顺序、错误、配置与性能特征。
_Avoid_: API、签名

**implementation**：
module 内部隐藏在 interface 后面的代码与行为。
_Avoid_: adapter、interface

**depth**：
interface 提供的 leverage；调用方每学习一个单位的 interface 能驱动多少行为。
_Avoid_: implementation 行数比例、复杂度

**deep module**：
用小 interface 隐藏大量行为的 module。它给调用方 leverage，并把维护知识集中为 locality。
_Avoid_: 大模块、复杂模块

**shallow module**：
interface 复杂度接近 implementation 复杂度、主要把知识转交给调用方的 module。
_Avoid_: 小模块、薄 adapter

**seam**：
一个 module 的 interface 所在的位置；行为可以在 seam 的另一侧变化而不修改调用方。seam 的位置与其后使用哪个 adapter 是两个决定。
_Avoid_: 边界、测试点

**adapter**：
在一条 seam 上满足某个 interface 的具体角色实现。一个真实 seam 至少有两个可替换 adapter。
_Avoid_: implementation、服务

**leverage**：
调用方从 module depth 获得的能力收益。

**locality**：
维护者从 module depth 获得的知识集中性；改动、缺陷和验证集中在一个拥有行为的位置。
