# MMW 重建课 Resources

## Knowledge

- [pstack 原文，cursor/plugins `e43c7ee`](https://github.com/cursor/plugins/tree/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack)
  同一版作为子树放在 `mmw-v3/upstream-pstack/`。Use for: 一切关于 pstack 组件、结构、写法的说法，最终都以它为准。
- [pstack guide](https://github.com/cursor/plugins/blob/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack/docs/guide/README.md)
  作者写给使用者的 10 章指南。Use for: 作者本人对 mode、playbook、原则怎样被用的说明；第 2、8、9 章最相关。
- [poteto-mode/SKILL.md](https://github.com/cursor/plugins/blob/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack/skills/poteto-mode/SKILL.md)
  mode 技能原文。Use for: 每一节写什么、mode 怎样点名其他组件。
- [automate-me/SKILL.md](https://github.com/cursor/plugins/blob/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack/skills/automate-me/SKILL.md)
  pstack 自己生成一份个人 mode 的流程。Use for: 一份 mode 该有哪些节、什么不该写进 mode。
- [reflect/SKILL.md](https://github.com/cursor/plugins/blob/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack/skills/reflect/SKILL.md)、[correct/SKILL.md](https://github.com/cursor/plugins/blob/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack/skills/correct/SKILL.md)
  一条经验该落进哪个组件、错误该在哪一层修。Use for: 组件什么时候被创建。
- [Cursor 文档：Agent Skills](https://cursor.com/docs/context/skills)、[Subagents](https://cursor.com/docs/context/subagents)、[Plugins](https://cursor.com/docs/plugins)
  宿主对 SKILL.md 字段、子代理定义、插件组件的官方说明。Use for: frontmatter 字段的确切含义。
- mattpocock/skills 原文，作为子树放在 `mmw-v3/upstream-mattpocock/`（上游 `d81f3a1`）
  Use for: MMW v2 依赖的上游技能。

## Wisdom (Communities)

- [cursor/plugins 的 Issues](https://github.com/cursor/plugins/issues)
  pstack 所在仓库。Use for: 原文没写清的地方（例如 `mode`、`reminder` 两个字段）问作者。

## Gaps

- Cursor 文档没有说明 SKILL.md 的 `mode` 与 `reminder` 字段。
- MMW v2 的设计理念没有一份成文的总说明，要从现役源文件和 ADR 里读出来。
