// Same five tasks as fixture_app.queue.TASKS and as the baseline's data/fixtures.js
// wb.tasks(wb.projects[0]); thumbs follow projects[0] (thumb / sideThumb).
window.FIXTURE_TASKS = [
  { taskId: "running-main", name: "商品主图生成任务", meta: "今天 16:18 · 3 / 5 张", state: "running", stateText: "进行中", thumb: "thumb-cleaner" },
  { taskId: "completed-main", name: "商品主图生成任务", meta: "07-16 10:42 · 3 套 · 3 张成图", state: "ready", stateText: "已完成", thumb: "thumb-cleaner" },
  { taskId: "partial-main", name: "商品主图生成任务", meta: "07-12 19:07 · 1 / 3 张已交付", state: "partial", stateText: "部分完成", thumb: "thumb-cleaner-alt" },
  { taskId: "failed-main", name: "商品主图生成任务", meta: "07-11 14:22 · 0 / 3 张已交付", state: "failed", stateText: "失败", thumb: "thumb-cleaner-alt" },
  { taskId: "completed-main-old", name: "商品主图生成任务", meta: "07-09 09:31 · 2 套 · 2 张成图", state: "ready", stateText: "已完成", thumb: "thumb-cleaner" }
];
