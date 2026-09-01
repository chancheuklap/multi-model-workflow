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

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| §0 标题、第一句、第三句 | 上游把这一节写成每个新项目必过的 gate；本仓写成 settle which style guide：不停下来问品牌，直接用自带配色画，在交付物旁边一行说明用了哪套、四种改法是什么。送客户、送外部的场合仍然先问 |
| §0 末段「All-default tokens…trigger the gate」 | 跟着上一条改成走默认路径，否则同一节里两句话互相矛盾 |
| §1 末句「Above 9 nodes, it's probably two diagrams」 | 改成超过 9 个节点先找能嵌套的图型，再考虑第二张 |
| §3 rules of thumb 第三条 | 同上：超预算改成重选一个能嵌套的图型，整个主题留在一张画布 |
| §7 复杂度预算末句 | 三处拆图规则里最要紧的一处。改写成：重画成能嵌套的图型，预算改为**按层**计——每条带、每个容器各自不超，整张画布可以超；图型是为它自己的典型题材写的，需要弯折（Layers 的范例不画带间连线，不代表你的连线要拿掉）。确实是两个独立问题时才拆，并说明每张图回答哪个问题。各图型自己的上限（泳道数、实体数、轴数、系列数）是它们语法的物理极限，仍然绝对生效 |
| §6 rule 6、§9 检查清单两条 | `<repo-root>` 占位符改成 `repo-root/`，指 skill 目录里的那条 symlink。host 装的是 skill 目录的 symlink，`../../` 会算到 host 目录去，占位符没法解析 |

上游若把复杂度预算重写，认它的新数字，只把「超了就拆」重新替换成上面这套「先嵌套、按层计、独立问题才拆」。

### references/output-spec.md

| 段落 | 我们的意图 |
| --- | --- |
| 导入降复杂度第 6 步「Still over? Split into overview + detail. Splitting beats shrinking.」 | 同 §7：先嵌套、按层计，两个独立问题才拆 |

其余 52 个 reference 未改。里面还有多处拆图建议（`type-radar.md` 超过 5 条系列、`type-sequence.md` 的 alt 套 alt、`type-dp-security-matrix.md` 超过 6 个角色等），那些是各图型语法的物理极限，不是全局性问题，**照收上游**。

### repo-root（symlink）

`skills/diagram-design/repo-root -> ../..`。上游没有，本仓加的：host 里 skill 是 symlink，`../../scripts/` 会解析到 host 目录，多这一跳才到 subtree 根。上游若自己给出装成 skill 后的脚本路径方案，改用它的，删掉这条 symlink。

### 未改

frontmatter、§2、§3 选型表、§4、§5、§6 前五条规则、§8、§9 其余各条、§10、§11、§12，以及 `assets/`、`scripts/`、`commands/`、`prompts/`。
