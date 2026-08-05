# Deepening

给定一簇 shallow module 的依赖情况，怎么安全地把它 deepen。用的是 [SKILL.md](SKILL.md) 那套词汇——**module**、**interface**、**seam**、**adapter**。

## 依赖分类

评估一个 deepening 候选时，先给它的依赖分类。分到哪一类，决定了 deepen 之后的 module 隔着 seam 怎么测。

### 1. 进程内

纯计算、内存状态、没有 I/O。永远可以 deepen——把这几个 module 合并，直接隔着新 interface 测。不需要 adapter。

### 2. 本地 I/O

系统拥有的本地 I/O 使用真实测试实例：Postgres 使用测试数据库，文件系统使用临时目录。deepen 之后的 module 隔着新 interface 测，不给数据库或文件系统另写测试替身。这条 seam 是内部的，module 的外部 interface 上不开 port。

### 3. 远端但自有（Ports & Adapters）

自家的服务，隔着一道网络边界（微服务、内部 API）。在这条 seam 上定义一个 **port**（interface）。逻辑归 deep module 所有，传输层作为 **adapter** 注入。测试连接真实测试服务，并走生产使用的 HTTP、gRPC 或队列 adapter；不写内存 adapter 代替自家服务。

建议的措辞形状：*「在这条 seam 上定义一个 port，HTTP adapter 连接真实测试服务与生产服务。逻辑坐在一个 deep module 里，测试仍走自家服务的真实代码。」*

### 4. 真外部（Mock）

你控制不了的第三方服务（Stripe、Twilio 等）。deepen 之后的 module 把这个外部依赖当成注入的 port 接进来，测试提供 mock adapter。

## seam 纪律

- **同一进程内只有一个 adapter 时，这条 seam 通常是假的。** 至少两个 adapter，或者 seam 两侧独立部署、独立变化，才开这个 port。测试 adapter 不用于凑数。
- **内部 seam 与外部 seam。** 一个 deep module 可以有内部 seam（私有的，只供 module 内部协作，不作为测试入口），也有 interface 上那条外部 seam。测试只跨 module 的 interface，不把内部 seam 暴露成测试入口。

## 测试策略：替换，不要叠加

- 一旦在 deepen 之后的 module 的 interface 上有了测试，原来压在 shallow module 上的单元测试就成了废物——删掉。
- 新测试写在 deepen 之后的 module 的 interface 上。**interface 就是测试面**。
- 测试断言隔着 interface 能观察到的结果，不断言内部状态。
- 测试要活过内部重构——它们描述行为，不描述实现。一个测试非得跟着实现一起改，它就测到 interface 后面去了。

**挪 seam 属于设计决定，不是落地时当场拍的。** deepen 一簇 module 就是在挪 seam。新 seam 落在哪、旧测试哪些跟着删，一并写进 spec、跟用户谈定之后再动手——判据见 `/mmw-tdd`。派出去的 `worker` 没有人可问，在这里要停。
