# 任务板：区域与状态

由仓库 `prototypes/task-board/553/UI/README.md` 的 `## State list` 生成，只由仓库改。

### 顶栏

- morning：一夜之后，四盏灯都有计数，"需要你"可点
- twenty-tickets：一个 spec 二十张票时的计数
- bad-data：读 GitHub 失败，写"读 GitHub 失败 · 下面是 HH:MM 的数据（N 分钟前）"
- empty：还没有任务，计数全为零

### 任务列表

- morning：一夜之后，多个任务，各带灯与进度
- twenty-tickets：一个 spec 二十张票的任务
- bad-data：读 GitHub 失败时仍显示上一次的数据
- empty：还没有任务

### 画布

- morning：一夜之后，展开的 map 与 spec，灰、绿、红三种阻塞线
- twenty-tickets：一个 spec 二十张票沿阻塞链铺开
- bad-data：坏数据（阻塞成环、读不到的阻塞方）
- empty：还没有任务
- nothing-selected：有任务，没有选中任何卡片

### 详情

- morning：一夜之后，选中一张在跑的 ticket
- twenty-tickets：二十张票里选中的一张
- bad-data：坏数据下选中的一张
- empty：还没有任务
- ticket-returned：票被交回，灯为橙
- ticket-bounced：合不进 base branch，写出冲突文件或没过的检查
- ticket-closeout：收口那一轮新开的票
- ticket-waiting：等槽位
- ticket-review：reviewer 正在评审
- ticket-queued：尚未派发
- ticket-landed：已落地
- ticket-fault：开了 `fault` 后停下
- ticket-missing-blocker：前置不在这棵树里，写 `unknown`
- spec：选中一个 spec，右栏是汇总
- map：选中一张 map，右栏是汇总
- decision：选中一张决策票
- nothing-selected：什么都没选中

### 本机配置

- mine：本机配置合法
- fresh：新机器，初始值里的 grok 没装
- retired：选中的 model 本机已经没有
- paseo-off：runner 是 paseo，Paseo 没开
- changed：打开后被别处改过
- edited：改了几处，还没保存，底栏列出改动
- incomplete：换了 host 之后有格子空着等选，不能保存
- scanning：正在重新扫描
- saved：保存成功
- refused：保存被拒
