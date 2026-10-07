/* 顶栏的场景数据。每个 scene 一条，数字是从 data/board-*.js 的真实数据按 topbar.mjs 的
   fromBoard() 算出来的：四种灯各有多少张票，
   readText 是右端那句读取状态（读失败时写成"读 GitHub 失败 · 下面是 HH:MM 的数据（N 分钟前）"）。 */
window.TOPBAR_SCENES = {
  "morning": {"orangeN":3,"greenN":3,"hollowN":9,"inkN":9,"readFailed":false,"readText":"只读 · 07:39 读取","settingsOpen":false},
  "twenty-tickets": {"orangeN":2,"greenN":4,"hollowN":7,"inkN":7,"readFailed":false,"readText":"只读 · 07:39 读取","settingsOpen":false},
  "bad-data": {"orangeN":1,"greenN":1,"hollowN":3,"inkN":1,"readFailed":true,"readText":"读 GitHub 失败 · 下面是 07:12 的数据（28 分钟前）","settingsOpen":false},
  "empty": {"orangeN":0,"greenN":0,"hollowN":0,"inkN":0,"readFailed":false,"readText":"只读 · 07:39 读取","settingsOpen":false}
};
