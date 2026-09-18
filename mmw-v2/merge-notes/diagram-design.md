# diagram-design

源目录：`mmw-v2/upstream-diagram-design/skills/diagram-design/`

上游是 `cathrynlavery/diagram-design`，独立于 `mmw-v2/upstream/`（那是 mattpocock 的），自己一个 subtree：

```
git subtree pull --prefix mmw-v2/upstream-diagram-design https://github.com/cathrynlavery/diagram-design main --squash
```

整个仓库都拉进来，不只是 `skills/`。`SKILL.md` 里的 `verify-geometry.py`、`verify-motion.py` 住在 repository root 的 `scripts/`，而且脚本内部按 `<repository root>/skills/diagram-design/assets/` 找资源；只取 `skills/` 那一层会让这两个校验永久缺失。

## 总原则

上游写给**做品牌交付物的设计师**：图要送给客户，所以每次先谈品牌，节点多了就拆成总览加细节，两张图各自干净。

我们要的是**读一次就看懂一个系统**：图不出门，全局性比每张图的干净更值钱。

所以取舍相反的只有两类：

- 改**怎么画**（图型、布局语法、连接线规则、设计系统、检查清单、导入导出）→ **收上游**。
- 改**画完给谁看**（拆图与否、先不先谈品牌）→ **弃上游，保我们的**。

通用约束：改动只落在必要的句子上，不重写段落；上游的图型 reference 一律不动。

## 谁调用它

`wait-what`（`VISUAL.md` 的 `## Draw the page`）和 `improve-codebase-architecture`（`SKILL.md` 第 2 步、`HTML-REPORT.md`）把页面样子与页上每张图整个交给这份技能，各自只加自己的内容要求，并各自免掉 §3 的「Confirm before drawing」。上游动到 §3 的确认步骤、§7 的页面结构、§8 的卡片、§12 的输出约束，或 `style-guide.md` 的颜色角色名（`accent`、`accent-tint`、`ink`、`muted`）时，照收上游，再读一遍这两处调用方，确认它们的说法没有和新规定相矛盾。

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| §0 标题、粗体首句、「Name the one you used…」一句 | 上游把这一节写成每个新项目必过的 gate；本仓写成 settle which style guide |
| §0「For a markerless project…」一段 | 上游写 pause and present the choices from `onboarding.md`；本仓写成不停下来问品牌，直接用自带配色画，在交付物旁边一行说明用了哪套、四种改法是什么 |
| §0「Branding first is the right call…」一段 | 本仓加的：送客户、送外部的场合仍然先问，问法照上游，指向 `onboarding.md` 与 `profiles.md` |
| §0 末段句尾「all-default tokens with no marker or header take the default path above」 | 本仓加的半句，跟着上两条走默认路径。`profiles.md` 里「all those values unchanged, run the first-time setup gate in `SKILL.md`」回指这一节，不必改 |
| §1 末句「Above 9 nodes, it's probably two diagrams」 | 改成超过 9 个节点先找能嵌套的图型，再考虑第二张 |
| §3 rules of thumb 第三条 | 同上：超预算改成重选一个能嵌套的图型，整个主题留在一张画布 |
| §7 复杂度预算末句 | 三处拆图规则里最要紧的一处。改写成：重画成能嵌套的图型，预算改为**按层**计——每条带、每个容器各自不超，整张画布可以超；图型是为它自己的典型题材写的，需要弯折（Layers 的范例不画带间连线，不代表你的连线要拿掉）。确实是两个独立问题时才拆，并说明每张图回答哪个问题。各图型自己的上限（泳道数、实体数、轴数、系列数）是它们语法的物理极限，仍然绝对生效 |
| §6「Arrow markers」代码块之后「When one page carries several diagrams…」一句 | 我们加的：三个箭头 marker 的 `id` 写死为 `arrow`、`arrow-accent`、`arrow-link`，一页放几张图（`improve-codebase-architecture` 的报告每张卡两张图）就出现重复 `id`，HTML 不合法，`self_check.py` 也不查。按 §12 给 `<title>` / `<desc>` 定的同一套 slug 前缀办。上游自己给出多图页的写法 → 用上游的，删这一句 |
| §6 rule 6、§9 检查清单两条 | `<repo-root>` 占位符改成 `repo-root/`，指 skill 目录里的那条 symlink。host 装的是 skill 目录的 symlink，`../../` 会算到 host 目录去，占位符没法解析 |

上游若把复杂度预算重写，认它的新数字，只把「超了就拆」重新替换成上面这套「先嵌套、按层计、独立问题才拆」。

### references/output-spec.md

| 段落 | 我们的意图 |
| --- | --- |
| 导入降复杂度第 6 步「Still over? Split into overview + detail. Splitting beats shrinking.」 | 同 §7：先嵌套、按层计，两个独立问题才拆 |

其余 55 个 reference 未改。里面还有多处拆图建议（`type-radar.md` 超过 5 条系列、`type-sequence.md` 的 alt 套 alt、`type-dp-security-matrix.md` 超过 6 个角色等），那些是各图型语法的物理极限，不是全局性问题，**照收上游**。

### repo-root（symlink）

`skills/diagram-design/repo-root -> ../..`。上游没有，本仓加的：host 里 skill 是 symlink，`../../scripts/` 会解析到 host 目录，多这一跳才到 subtree 根。上游若自己给出装成 skill 后的脚本路径方案，改用它的，删掉这条 symlink。

### scripts/verify-geometry.py 与 scripts/test-verify-geometry.py

| 段落 | 我们的意图 |
| --- | --- |
| `svg_spans`、`svg_index` 两个函数，`Rect` 多出的 `svg` 字段，`check` 里「不同 `<svg>` 跳过」那一句，文件头说明末段 | 我们加的：每个顶层 `<svg>` 是自己的坐标系，标签只和同一张图里的节点比。上游版本把整份文件的 `<rect>` 放进一个坐标系，一页多张图时把甲图的标签和乙图的节点算成重叠；`improve-codebase-architecture` 的报告每张卡两张图，照上游版本永远过不了。上游自己改成按图分开 → 用上游的，删掉我们这几处 |
| 测试里「mask and node in different diagrams on one page」「mask clipped inside the second diagram on a page」两条 | 我们加的，锁住上一条。第一条在上游版本上失败 |
| `CJK_MASK_MAX_H`、`labels_cjk`、`is_mask`，`Rect` 多出的 `cjk_label` 字段，文件头说明里「A plate up to 16 tall…」一条 | 我们加的：16px 高的底板，后面紧跟的第一段 `<text>`（在下一个 `<rect>` 之前）含中日韩文字时，也算标签。`style-guide.md` 规定中日韩箭头标签、eyebrow、图例的底板是 16px 高，而上游只认 8–14px，中文图里的标签一个都不检查，被方框盖住也报「0 finding」。英文标签的 14px 上限没动：上游测试「container header bar is not a mask」说明 16px 高、后跟英文的是容器标题条，照旧不算。上游自己支持中日韩标签 → 用上游的，删掉我们这几处 |
| 测试里六条「16px CJK / Hangul …」「16px rect followed by Latin text…」「CJK text after the next rect…」「18px rect with CJK text…」 | 我们加的，锁住上一条。前两条在上游版本上失败 |


### 未改

frontmatter、§2、§3 选型表、§4、§5、§6 前五条规则（「Arrow markers」加的那一句除外）、§8、§9 其余各条、§10、§11、§12，以及 `assets/`、`commands/`、`prompts/`，`scripts/` 里除上面两份之外的文件。
