/* 任务列表的场景数据。每个 scene 一条，行是从 data/board-*.js 的真实数据按
   board-logic.mjs 的 Board.aggregate / Board.progress 算出来的：
   lamp 是该任务所有 ticket 的聚合灯，done/total 是已落地数。 */
window.TASK_SCENES = {
  "morning": {
    "selected": 98,
    "rows": [
      {"n": 98, "kind": "map", "title": "落地流水线改造", "lamp": "orange", "done": 6, "total": 18},
      {"n": 77, "kind": "map", "title": "交接包比对", "lamp": "ink", "done": 3, "total": 3},
      {"n": 101, "kind": "map", "title": "子 issue 五种改名", "lamp": "hollow", "done": 0, "total": 3}
    ]
  },
  "twenty-tickets": {
    "selected": 210,
    "rows": [
      {"n": 210, "kind": "map", "title": "判活三层落地", "lamp": "orange", "done": 7, "total": 20}
    ]
  },
  "bad-data": {
    "selected": 300,
    "rows": [
      {"n": 300, "kind": "map", "title": "端口租约回收", "lamp": "orange", "done": 1, "total": 6}
    ]
  },
  "empty": {
    "selected": null,
    "rows": []
  }
};
