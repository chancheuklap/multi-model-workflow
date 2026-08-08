# ADR 格式

ADR 位于 `mmw domain dirs` 返回的 `adr` 路径中，并使用连续编号，例如 `0001-slug.md`、`0002-slug.md`。

按需创建 `adr` 路径，也就是只在需要第一份 ADR 时创建。

## 模板

```md
# {决定的简短标题}

{1 至 3 句话：上下文是什么、我们作出了什么决定，以及为什么。}
```

就这些。一份 ADR 可以只有一个段落。价值在于记录**确实作出了一项决定**以及**作出决定的原因**，不在于填满各个章节。

## 可选章节

只在这些章节确实能增加价值时加入。大多数 ADR 不需要它们。

- **Status** frontmatter（`proposed | accepted | deprecated | superseded by ADR-NNNN`）——重新审视决定时有用
- **Considered Options**——只有被否决的选项值得记住时才加入
- **Consequences**——只有需要明确说明不明显的下游影响时才加入

## 编号

运行 `mmw domain adr-next`，取得现有最大编号之后的下一个四位编号。

如果多条 decision ticket 结果分支可能同时创建 ADR，结果分支先使用 `draft-<ticket 编号>-<slug>.md`。结果分支集成到拥有 Wayfinding map 的任务分支后，任务分支重新运行 `mmw domain adr-next`，按顺序分配正式编号，并提交重命名。草稿文件不占用正式编号。

## 何时提议 ADR

以下三项必须全部成立：

1. **难以逆转**——以后改变主意的成本不可忽略
2. **缺少上下文时令人意外**——未来读者会查看代码并疑惑：“他们到底为什么这样做？”
3. **来自真实取舍**——确实存在其他选项，而且你因为具体理由选择了其中一个

如果一项决定容易逆转，就不要记录；你以后只会直接逆转它。如果它并不令人意外，就没有人会疑惑原因。如果不存在真实的其他选项，除了“我们采用了显然的做法”以外，没有其他值得记录的内容。

### 符合条件的内容

- **架构形状。** “我们使用 monorepo。”“write model 采用 event sourcing，read model 被投影到 Postgres。”
- **bounded context 之间的集成模式。** “Ordering 和 Billing 通过 domain event 通信，不使用同步 HTTP。”
- **带来 lock-in 的技术选择。** 数据库、消息总线、鉴权提供方、部署目标。不是每个库；只记录那些更换需要一个季度的选择。
- **边界和范围决定。** “Customer data 由 Customer bounded context 拥有；其他 bounded context 只通过 ID 引用它。”明确说明“不采用什么”与明确说明“采用什么”同样有价值。
- **有意偏离显然路径。** “因为 X，我们使用手写 SQL，不使用 ORM。”任何理性读者都会假定相反做法的情形都属于这一类。它们能防止下一位 engineer 去“修复”一项有意为之的内容。
- **代码中不可见的约束。** “由于合规要求，我们不能使用 AWS。”“由于 partner API contract，响应时间必须低于 200ms。”
- **否决理由并不明显的备选方案。** 如果你考虑过 GraphQL，却因为细微理由选择 REST，就记录它；否则，六个月后还会有人再次提议 GraphQL。
