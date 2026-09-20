# 201-trigger-after

## 改了什么

一行的 `trigger` 在同一 scene 上不再被默认为唯一。精确的角色和 accessible name 命中多于一个具名节点时，行要写 `after`（读序上前一个具名节点，`{ role, name }`），与 `volatile_values` 同一字段；`after` 的钉住走同一匹配函数，trigger 本身按精确名，和 `get_by_role(..., exact=True)` 同一份名单。驱动按它缩小结果，取不到唯一一个就报错，不再静静取第一个。lint 只在精确对命中多于一个且没有 `after` 时报 ERROR。

## 哪些产物失效

- screen contract：任意一行的 `trigger` 在它列出的某个 scene 的 target tree 里精确命中多于一个节点、且没有 `after` 的，lint 从绿变红。接线判据和 `open` 链在同样的行上从点到 DOM 里第一个同名控件，变成报错退出。
- target trees 随 screen contract 一起：`after` 的值从该 scene 树里触发器上一行的角色和名字抄。

## 怎么迁

对 lint 报出的每一行，打开那一行 `scenes` 里出问题的那个 scene 的 `.aria`，看该 `trigger` 的两个（或多个）命中，把要点的那一个的上一行具名节点写成 `after: { role: …, name: … }`，与 `trigger` 同级。改完 lint 应不再报这一行；判据重跑应点到 `after` 钉住的那一个。
