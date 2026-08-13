# Deepening

给定一簇 shallow module 的依赖情况，怎么安全地把它 deepen。用的是 [SKILL.md](SKILL.md) 那套词汇——**module**、**interface**、**seam**、**adapter**。

## 依赖分类

评估一个 deepening 候选时，先给它的依赖分类。分到哪一类，决定了 deepen 之后的 module 隔着 seam 怎么测。

### 1. 进程内

纯计算、内存状态、没有 I/O。永远可以 deepen——把这几个 module 合并，直接隔着新 interface 测。不需要 adapter。

### 2. 本地可替身

有本地测试替身的依赖（Postgres 用 PGLite、文件系统用内存实现）。替身存在就可以 deepen。deepen 之后的 module 在测试套件里跑着替身来测。这条 seam 是内部的，module 的外部 interface 上不开 port。

### 3. 远端但自有（Ports & Adapters）

自家的服务，隔着一道网络边界（微服务、内部 API）。在这条 seam 上定义一个 **port**（interface）。逻辑归 deep module 所有，传输层作为 **adapter** 注入。测试用内存 adapter，生产用 HTTP、gRPC 或队列 adapter。

建议的措辞形状：*「在这条 seam 上定义一个 port，生产实现 HTTP adapter、测试实现内存 adapter，这样逻辑坐在一个 deep module 里，即便它部署时跨了一道网络。」*

### 4. 真外部（Mock）

你控制不了的第三方服务（Stripe、Twilio 等）。deepen 之后的 module 把这个外部依赖当成注入的 port 接进来，测试提供 mock adapter。

## seam 纪律

- **一个 adapter 只是假设有这条 seam，两个 adapter 才证明它真的存在。** 至少有两个 adapter 说得通（通常是生产加测试）才开这个 port。只有一个 adapter 的 seam 只是一层拐弯。
- **内部 seam 与外部 seam。** 一个 deep module 可以有内部 seam（私有的，只给它自己的测试用），也有 interface 上那条外部 seam。不要只因为测试用到了就把内部 seam 暴露到 interface 上。

## 测试策略：替换，不要叠加

- 一旦在 deepen 之后的 module 的 interface 上有了测试，原来压在 shallow module 上的单元测试就成了废物——删掉。
- 新测试写在 deepen 之后的 module 的 interface 上。**interface 就是测试面**。
- 测试断言隔着 interface 能观察到的结果，不断言内部状态。
- 测试要活过内部重构——它们描述行为，不描述实现。一个测试非得跟着实现一起改，它就测到 interface 后面去了。

**挪 seam 属于设计决定，不是落地时当场拍的。** deepen 一簇 module 就是在挪 seam。新 seam 落在哪、旧测试哪些跟着删，一并写进 spec、跟用户谈定之后再动手——判据见 `/mmw-tdd`。派出去的 `worker` 没有人可问，在这里要停。
