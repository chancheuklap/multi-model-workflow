# Pull report

## 设计检查

- 编辑器点不中的选择器：App · 任务板.dc.html <style>: [data-ui="任务列表.root"]  (attribute selector)
- 编辑器点不中的选择器：App · 任务板.dc.html <style>: [data-ui="画布.root"]  (attribute selector)
- 编辑器点不中的选择器：App · 任务板.dc.html <style>: [data-ui="详情.root"]  (attribute selector)
- 编辑器点不中的选择器：App · 任务板.dc.html <style>: [data-ui="本机配置.root"]  (attribute selector)

## 覆盖

- 带文字但没有 `data-ui` id：`App · 任务板.dc.html`（11 处）：span: ·；b: #150 contract；b: #151 decision；span.code: mmw:map；span.code: start；span.code: ~/.mmw/models.json；span.code: MMW_RUNNER；span: agent；span: host；span: model；span: effort
- 带文字但没有 `data-ui` id：`Component · 本机配置.dc.html`（8 处）：span.code: start；span.code: ~/.mmw/models.json；span.code: MMW_RUNNER；span: agent；span: host；span: model；span: effort；b: 没有保存。
- 带文字但没有 `data-ui` id：`Component · 画布.dc.html`（1 处）：span.code: mmw:map
- 带文字但没有 `data-ui` id：`Component · 详情.dc.html`（7 处）：span: ·；p.empty-text: 有了 map 之后，点画布上的卡，它的细节显示在这一栏。；b: #310 fault；span.counter-n: 3；span.counter-n: 2；span.counter-n: 6；p.empty-text: 画布上任意一张卡——map、spec、ticket 或 decision ticket——点一下，它的全部细节就在这一栏。

## 改动分类

- 分类：增删控件或改流转
- design page：`Component · 详情.dc.html`、`Component · 顶栏.dc.html`
- `data-ui` id 新增：无
- `data-ui` id 删除：`顶栏.running.sub`
- `scene` 取值变化：`Component · 详情.dc.html`；新增 无；删除 ticket-waiting。
- 合同行引用的文字变化：`detail.goto-blocked`：`#222 「不知道」与「死了」分开 held | #135 投递回执 held | #137 中继自检命令 held | #133 折叠接入中继 working #134 唤醒队列持久化 review #142 唤醒日志落盘 landed #139 槽位交还后叫醒 verify #138 离线时唤醒去向 verify #141 中继日志轮转 working #136 重试与退避 waiting` → `#222 「不知道」与「死了」分开 held | #135 投递回执 held | #137 中继自检命令 held | #133 折叠接入中继 working #134 唤醒队列持久化 review #142 唤醒日志落盘 landed #139 槽位交还后叫醒 verify #138 离线时唤醒去向 verify #141 中继日志轮转 working #136 重试与退避 working`
- 合同行引用的文字变化：`detail.goto-ticket-row`：`#132 中继进程骨架 landed #133 折叠接入中继 working #134 唤醒队列持久化 review #142 唤醒日志落盘 landed #139 槽位交还后叫醒 verify #138 离线时唤醒去向 verify #141 中继日志轮转 working #136 重试与退避 waiting #135 投递回执 queued #137 中继自检命令 queued` → `#132 中继进程骨架 landed #133 折叠接入中继 working #134 唤醒队列持久化 review #142 唤醒日志落盘 landed #139 槽位交还后叫醒 verify #138 离线时唤醒去向 verify #141 中继日志轮转 working #136 重试与退避 working #135 投递回执 queued #137 中继自检命令 queued`
- 合同行引用的文字变化：`board.goto-ticket-row`：`#132 中继进程骨架 landed #133 折叠接入中继 working #134 唤醒队列持久化 review #142 唤醒日志落盘 landed #139 槽位交还后叫醒 verify #138 离线时唤醒去向 verify #141 中继日志轮转 working #136 重试与退避 waiting #135 投递回执 queued #137 中继自检命令 queued` → `#132 中继进程骨架 landed #133 折叠接入中继 working #134 唤醒队列持久化 review #142 唤醒日志落盘 landed #139 槽位交还后叫醒 verify #138 离线时唤醒去向 verify #141 中继日志轮转 working #136 重试与退避 working #135 投递回执 queued #137 中继自检命令 queued`

## 本地改过的说明

- pull 前 design package 与上次提交一致。
