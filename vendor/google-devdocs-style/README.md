# Google developer documentation style guide

Google 官方开发者文档风格指南的**结构化摘要**，共 69 页，覆盖原指南导航列出的全部子页面。

来源、许可（CC BY 4.0）和「这是摘要不是原文」的说明见 [ATTRIBUTION.md](ATTRIBUTION.md)。

---

## 先看这几页

按对 MMW 的价值排序。理由见每页里的 `## MMW note`，以及本文件末尾的适用边界。

| 页 | 为什么 |
| --- | --- |
| [Prescriptive documentation](03-general-principles/prescriptive-documentation.md) | must / can / might / We recommend 的准确含义，以及为什么 **should 是歧义词**。任何写给"不能反问的执行者"的文档都适用 |
| [Sentence structure](04-language-and-grammar/sentence-structure.md) | **条件写在指令前面**。一条规则，整页 |
| [Procedures](06-formatting-and-organization/procedures.md) | 给人照着做的步骤怎么写。**`/mmw-wizard` 可整页照搬** |
| [Notices](06-formatting-and-organization/notices.md) | Note/Caution/Warning 分级，以及**读者会跳过 notice，所以必需信息不能放进去** |
| [Global audience](03-general-principles/global-audience.md) + [Dates and times](06-formatting-and-organization/dates-and-times.md) | **`/mmw-to-questionnaire` 适用** —— 那是唯一一个读者是陌生真人的产物 |
| [Command-line syntax](08-computer-interfaces/command-line-syntax.md) | 方括号、花括号、省略号**会把可复制的命令弄坏** |
| [Word list](02-key-resources/word-list.md) | 274 条禁用词与替换词，随时查 |

---

## 全部页面


### 介绍 · `01-introduction/`

| 页 | 管什么 | |
| --- | --- | --- |
| [Philosophy](01-introduction/philosophy.md) | 这份指南自己声明**不**做什么。先读这页，避免拿它去解决它管不了的问题 | ⚠️ 附 MMW note |
| [Highlights](01-introduction/highlights.md) | 全指南最常引用的规则，一页扫完 |  |
| [What's new](01-introduction/whats-new.md) | 变更记录；少数几处解释了规则背后的理由 |  |

### 关键资源 · `02-key-resources/`

| 页 | 管什么 | |
| --- | --- | --- |
| [Word list](02-key-resources/word-list.md) | **274 条禁用/避免/慎用的词**，各自的替换词。查一个词能不能用 | ⭐ 最常查 |
| [Product names](02-key-resources/product-names.md) | 产品名的大小写、缩写、前面加不加 the |  |
| [Text-formatting summary](02-key-resources/text-formatting.md) | 粗体、斜体、代码字体、下划线各自的唯一用途 |  |

### 通用原则 · `03-general-principles/`

| 页 | 管什么 | |
| --- | --- | --- |
| [Prescriptive documentation](03-general-principles/prescriptive-documentation.md) | **must / can / might / We recommend 的准确含义，以及为什么禁用 should** | ⭐ 最该借 |
| [Timeless documentation](03-general-principles/timeless-documentation.md) | 不写会过期的词。ADR、术语表这类长寿命文档适用 | ⭐ 长寿命文档 |
| [Writing for a global audience](03-general-principles/global-audience.md) | 读者英语水平不一、文档要翻译时的写法 | ⭐ 发给外部真人的文档 |
| [Voice and tone](03-general-principles/voice-and-tone.md) | 像懂行的朋友，不像手册也不像段子手 |  |
| [Writing accessibly](03-general-principles/accessibility.md) | 方向词、链接文字、alt 文本、颜色不能单独承载信息 |  |
| [Inclusive language](03-general-principles/inclusive-language.md) | 该换掉的词：性别化、能力歧视、master/blacklist 这类 |  |
| [Jargon](03-general-principles/jargon.md) | 行话什么时候能用；**与 leading words 冲突，见文件内 MMW note** | ⚠️ 附 MMW note |
| [Excessive claims](03-general-principles/excessive-claims.md) | 别做无法核实的断言：最快、最好、保证 | ⚠️ 附 MMW note |
| [Future features](03-general-principles/future-features.md) | 不要预告还没发布的东西 |  |
| [Third-party content](03-general-principles/third-party-content.md) | 别复制别人的内容——改写并给链接 |  |

### 语法 · `04-language-and-grammar/`

| 页 | 管什么 | |
| --- | --- | --- |
| [Sentence structure](04-language-and-grammar/sentence-structure.md) | **条件写在指令前面。** 整页只有这一条规则 | ⭐ 最该借 |
| [Second person](04-language-and-grammar/second-person.md) | 用 you 不用 we；祈使句的用法 |  |
| [Active voice](04-language-and-grammar/active-voice.md) | 谁在做这个动作必须写清楚 |  |
| [Present tense](04-language-and-grammar/present-tense.md) | 用现在时；will 和 would 什么时候才允许 |  |
| [Pronouns](04-language-and-grammar/pronouns.md) | 指代必须清楚；单数 they；that 和 which 的区别 |  |
| [Abbreviations](04-language-and-grammar/abbreviations.md) | 首次出现要不要展开；**e.g. / i.e. 一律禁用** |  |
| [Capitalization](04-language-and-grammar/capitalization.md) | 标题用句首大写，不用标题式大写 |  |
| [Contractions](04-language-and-grammar/contractions.md) | 否定式缩写鼓励用——don't 比 do not 更不容易看漏 |  |
| [Articles](04-language-and-grammar/articles.md) | 别为了简短省掉冠词，标题里也不行 |  |
| [Pluralization](04-language-and-grammar/pluralization.md) | 代码名和缩写不能直接加 s |  |
| [Possessives](04-language-and-grammar/possessives.md) | 产品名和代码名不能变所有格 |  |
| [Prepositions](04-language-and-grammar/prepositions.md) | 介词结尾没问题；哪个 UI 元素配哪个介词 |  |
| [Anthropomorphism](04-language-and-grammar/anthropomorphism.md) | 别把软件写成人 | ⚠️ 附 MMW note |
| [Verbs in reference documents](04-language-and-grammar/reference-verbs.md) | API 参考用第三人称：Creates，不是 Create |  |

### 标点 · `05-punctuation/`

| 页 | 管什么 | |
| --- | --- | --- |
| [Commas](05-punctuation/commas.md) | 串行逗号必须用 |  |
| [Colons](05-punctuation/colons.md) | 冒号引出列表时前面必须是完整句子 |  |
| [Dashes](05-punctuation/dashes.md) | 破折号不加空格；连接号一律不用 |  |
| [Hyphens](05-punctuation/hyphens.md) | 前缀、复合修饰语、数字范围的连字符规则 |  |
| [Periods](05-punctuation/periods-and-end-punctuation.md) | 句号与括号引号的先后 |  |
| [Parentheses](05-punctuation/parentheses.md) | 重要信息不要放括号里——读者会跳过 |  |
| [Semicolons](05-punctuation/semicolons.md) | 尽量不用；屏幕阅读器可能不读出来 |  |
| [Quotation marks](05-punctuation/quotation-marks.md) | 一律用直引号 |  |
| [Ellipses](05-punctuation/ellipses.md) | 一般不用；UI 标签里的省略号要去掉 |  |
| [Slashes](05-punctuation/slashes.md) | 除代码外尽量不用；and/or 也不用 |  |

### 格式与组织 · `06-formatting-and-organization/`

| 页 | 管什么 | |
| --- | --- | --- |
| [Procedures](06-formatting-and-organization/procedures.md) | **给人照着做的步骤怎么写。wizard 技能可整页照搬** | ⭐ 最该借 |
| [Notes and other notices](06-formatting-and-organization/notices.md) | **Note/Caution/Warning 分级，以及绝不能塞进 note 的东西** | ⭐ 最该借 |
| [Lists](06-formatting-and-organization/lists.md) | 三种列表的用途；平行结构与标点 |  |
| [Headings and titles](06-formatting-and-organization/headings-and-titles.md) | 句首大写；任务型标题用动词原形 | ⚠️ 附 MMW note |
| [Paragraph structure](06-formatting-and-organization/paragraph-structure.md) | 一段一个意思，要点放段首 |  |
| [Tables](06-formatting-and-organization/tables.md) | 什么时候用表格；表格前必须有完整介绍句 |  |
| [Writing examples](06-formatting-and-organization/examples.md) | 举例用 for example / such as，绝不用 e.g. |  |
| [Dates and times](06-formatting-and-organization/dates-and-times.md) | **日期必须无歧义** —— 问卷 deadline 适用 | ⭐ 发给外部真人的文档 |
| [Numbers](06-formatting-and-organization/numbers.md) | 什么时候写数字什么时候写单词 |  |
| [Units of measurement](06-formatting-and-organization/units-of-measure.md) | 数字与单位之间用不间断空格 |  |
| [Figures and other images](06-formatting-and-organization/images.md) | alt 文本、截图、图注 |  |
| [Italics with terms](06-formatting-and-organization/italics-with-terms.md) | 只有两种情况用斜体 |  |
| [Footnotes](06-formatting-and-organization/footnotes.md) | 尽量不用脚注 |  |
| [Mathematical notation](06-formatting-and-organization/mathematical-notation.md) | 数学符号、变量、指数 |  |
| [Phone numbers](06-formatting-and-organization/phone-numbers.md) | 例子里必须用保留号段 |  |

### 链接 · `07-linking/`

| 页 | 管什么 | |
| --- | --- | --- |
| [Cross-references and linking](07-linking/cross-references.md) | 链接文字要能脱离上下文读懂；什么时候不该加链接 |  |
| [Headings as link targets](07-linking/headings-as-link-targets.md) | 锚点怎么写，改标题时怎么不弄断旧链接 |  |

### 计算机界面 · `08-computer-interfaces/`

| 页 | 管什么 | |
| --- | --- | --- |
| [Command-line syntax](08-computer-interfaces/command-line-syntax.md) | **方括号花括号不能出现在可直接复制的命令里** | ⭐ 最该借 |
| [Placeholder formatting](08-computer-interfaces/placeholders.md) | 占位符全大写下划线；多个占位符跟 Replace the following: |  |
| [Code in text](08-computer-interfaces/code-in-text.md) | 哪些用代码字体；代码名不能当英文动词或复数 |  |
| [UI elements and interaction](08-computer-interfaces/ui-elements.md) | UI 元素怎么称呼、哪个动词配哪个控件 |  |
| [Code samples](08-computer-interfaces/code-samples.md) | 缩进、换行宽度、省略号、引出句 |  |
| [API reference code comments](08-computer-interfaces/api-reference-comments.md) | 类、方法、参数、返回值、异常的起句模式 |  |

### HTML 与 CSS · `09-html-and-css/`

| 页 | 管什么 | |
| --- | --- | --- |
| [HTML and semantic tagging](09-html-and-css/semantic-tagging.md) | 元素按语义用不按外观用 |  |
| [HTML formatting](09-html-and-css/html-formatting.md) | 文档源码的缩进、行宽、大小写 |  |
| [Markdown versus HTML](09-html-and-css/markdown-versus-html.md) | 两者选一，不要混用 |  |

### 命名 · `10-names-and-naming/`

| 页 | 管什么 | |
| --- | --- | --- |
| [Example domains and names](10-names-and-naming/example-domains-and-names.md) | 例子必须用保留域名、保留 IP、中性人名 |  |
| [Filenames](10-names-and-naming/filenames.md) | 小写、连字符；正文里怎么称呼文件类型 | ⚠️ 附 MMW note |
| [Trademarks](10-names-and-naming/trademarks.md) | 商标只能当修饰语 |  |

---

## 适用边界

这份指南是**给人类读者的技术文档**写的。MMW 有两类读者，规则不通用。

**对 agent 执行的技能正文，以下四条不要照搬：**

**→ 禁比喻和行话**（[Jargon](03-general-principles/jargon.md)、[Inclusive language](03-general-principles/inclusive-language.md)）。与 `writing-for-agents` 的 **leading words** 直接冲突。`tracer bullet`、`fog of war`、`blast radius` 在模型预训练里有强先验，是压缩手段。Google 的理由是翻译成本和非母语读者 —— **读者是模型时这条理由不成立**。

**→ 不解释规则的理由**（[Philosophy](01-introduction/philosophy.md)）。Google 明说读者要的是简短答案。但 agent 需要理由来判断规则没写到的情况。**MMW 必须反着来。**

**→ 标题里不用数字表示顺序**（[Headings](06-formatting-and-organization/headings-and-titles.md)）。Google 的理由是人靠视觉层级判断顺序。技能里的 `## 3. …` 是 agent 的完成度锚点，保留。

**→ 避免 never / always**（[Excessive claims](03-general-principles/excessive-claims.md)）。那条防的是对外宣传翻车。MMW 需要硬约束。

**这份指南真正适用的，是 MMW 里读者为人的落盘产物** —— spec、ticket、questionnaire、ADR、`CONTEXT.md`、agent brief、wizard 脚本、out-of-scope 记录、architecture 报告。

