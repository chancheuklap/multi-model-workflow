window.CHAMELEON = window.CHAMELEON || {};
window.CHAMELEON.wallet = { balance: 20, rechargedBalance: 12480 };
window.CHAMELEON.billingDebt = {
  count: 100,
  due: 3240,
  entries: [
    { name: "山野净洗洁精", note: "商品主图生成任务 · 今天 16:18", amount: 90 },
    { name: "自由模式", note: "自由生成记录 · 今天 15:42", amount: 60 },
    { name: "绒雾身体乳", note: "商品主图生成任务 · 昨天 21:18", amount: 30 }
  ]
};

window.CHAMELEON.projects = [
  { key: "cleaner", name: "山野净洗洁精", id: "PRJ-240716-C08", art: "art-cleaner", subjectCount: 2, taskCount: 4, artTop: "最近使用", statusClass: "status running", statusLabel: "1 个任务进行中", updated: "5 分钟前更新" },
  { key: "lotion",  name: "绒雾身体乳",   id: "PRJ-240629-D04", art: "art-bag",     subjectCount: 1, taskCount: 3, artTop: "全部完成", statusClass: "status done",    statusLabel: "任务已完成",     updated: "昨天 21:18 更新" },
  { key: "tea",     name: "暮山冷泡茶",   id: "PRJ-240618-F21", art: "art-kettle",  subjectCount: 2, taskCount: 2, artTop: "全部完成", statusClass: "status done",    statusLabel: "任务已完成",     updated: "07-28 09:31 更新" },
  { key: "lamp",    name: "暖光护眼台灯", id: "PRJ-240805-A17", art: "art-lamp",    subjectCount: 1, taskCount: 0, artTop: "尚无任务", statusClass: "status new",     statusLabel: "刚刚创建",       updated: "今天 10:42 更新", noArtLabel: true }
];
(function () {
var loginScenarios = {
      "app-checking": {
        state: "checking",
        tone: "progress",
        eyebrow: "登录变色龙商品图助手",
        title: "正在确认登录状态",
        description: "请稍候。确认完成后，应用会继续下一步。",
        detail: "检查期间不会显示商品项目、自由模式或鸭豆余额。"
      },
      "app-login-required": {
        state: "login-required",
        tone: "neutral",
        eyebrow: "需要登录",
        title: "登录变色龙商品图助手",
        description: "登录会在卡皮巴拉浏览器页面完成。这里不需要输入激活码、许可证或机器凭证。",
        detail: "卡皮巴拉会处理账号登录、许可证分配和当前电脑确认。",
        primaryLabel: "登录",
        primaryAction: "start-login"
      },
      "app-awaiting-browser": {
        state: "awaiting-browser",
        tone: "progress",
        eyebrow: "等待浏览器登录",
        title: "请在卡皮巴拉页面完成登录",
        description: "应用会自动检查登录结果。回到本窗口时会立即检查一次。",
        detail: "如果登录页面没有显示，可以重新打开当前登录页面。",
        primaryLabel: "重新打开登录页面",
        primaryAction: "reopen-login"
      },
      "app-capybara-unreachable": {
        state: "capybara-unreachable",
        tone: "danger",
        eyebrow: "无法连接卡皮巴拉",
        title: "登录页面暂时无法打开",
        description: "本机未能建立登录请求，或系统浏览器没有打开登录页面。",
        detail: "请检查网络连接后重试。当前不会显示任何客户组织数据。",
        primaryLabel: "重试",
        primaryAction: "start-login"
      },
      "app-login-failed": {
        state: "login-failed",
        tone: "danger",
        eyebrow: "登录失败",
        title: "这次登录没有完成",
        description: "本机启动或登录回调没有完成。当前登录结果不会进入商品项目库。",
        detail: "重新登录会建立新的登录请求，并打开新的卡皮巴拉页面。",
        primaryLabel: "重新登录",
        primaryAction: "restart-login"
      },
      "app-login-incomplete": {
        state: "login-incomplete",
        tone: "warning",
        eyebrow: "登录未完成",
        title: "登录等待已经结束",
        description: "原登录记录已经过期，或应用已经停止等待原登录结果。",
        detail: "重新登录会建立新的登录请求。应用不会静默停在当前页面。",
        primaryLabel: "重新登录",
        primaryAction: "restart-login"
      },
      "app-account-change-blocked": {
        state: "account-change-blocked",
        tone: "warning",
        eyebrow: "换号受阻",
        title: "暂时不能使用另一账号",
        description: "当前客户组织还有 3 笔账务没有收口。完成处理前，其他账号不能替换当前身份。",
        detail: "重新登录原账号不受这项门禁阻止。登录后可以继续处理原客户组织的账务。",
        primaryLabel: "重新登录原账号",
        primaryAction: "restore-original-account"
      },
      "app-upgrade-required": {
        state: "upgrade-required",
        tone: "warning",
        eyebrow: "需要更新应用",
        title: "请联系管理员更新应用",
        description: "当前版本是 0.9.4，最低支持版本是 1.0.0。这个版本无法使用当前服务配置。",
        detail: "请联系管理员获取新版安装包。更新完成前不能进入商品项目库。"
      }
    };
var serviceStatusScenarios = {
      "app-service-unavailable": {
        state: "service-unavailable",
        tone: "error",
        label: "服务不可用",
        title: "服务配置不完整",
        detail: "变色龙暂时不能开始新的生成任务。已有商品项目和商品任务仍可查看。"
      },
      "app-service-config-sync": {
        state: "service-config-sync",
        tone: "warning",
        label: "服务配置同步中",
        title: "正在同步服务配置",
        detail: "应用正在重新获取服务配置。完成前不能开始新的生成任务。",
        recoverAutomatically: true
      }
    };
  loginScenarios["app-login-blocking"] = loginScenarios["app-login-required"];
var globalFeedbackScenarios = {
      "ux-realtime-disconnected": {
        state: "realtime-disconnected",
        tone: "warning",
        label: "正在恢复连接",
        title: "正在恢复实时连接",
        detail: "当前仍显示最后一次可信的任务和图片状态。连接中断不会把任务标记为失败。"
      },
      "ux-realtime-consistent": {
        state: "realtime-consistent",
        tone: "ready",
        label: "服务正常",
        title: "实时状态已恢复",
        detail: "当前页面已经显示服务端最新的任务和图片状态。较早的状态不会覆盖当前结果。"
      },
      "ux-safe-error": {
        state: "safe-error",
        tone: "error",
        title: "这次操作没有完成",
        detail: "生成服务暂时无法处理这次请求。当前内容已经保留，请按页面中的原有入口重试。"
      }
    };
  window.CHAMELEON.loginScenarios = loginScenarios;
  window.CHAMELEON.serviceStatusScenarios = serviceStatusScenarios;
  window.CHAMELEON.globalFeedbackScenarios = globalFeedbackScenarios;
})();

window.CHAMELEON.freeRuns = [
  { id: "FREE-QUEUED", state: "queued", time: "今天 16:18", ratio: "3:4", requested: 2, prompt: "把商品放在清晨的厨房台面上，保留包装完整。", inputName: "商品图片_洗洁精.jpg", removeLogo: false, itemStates: ["pending", "pending"] },
  { id: "FREE-RUNNING", state: "running", time: "今天 15:42", ratio: "4:3", requested: 2, prompt: "深色书桌与暖色台灯，突出安静专注的夜间阅读氛围。", inputName: "暖光台灯.jpg", removeLogo: false, itemStates: ["delivered", "generating"] },
  { id: "FREE-COMPLETED", state: "completed", time: "今天 14:26", ratio: "3:4", requested: 4, prompt: "柔和晨光下的浴室台面，保留瓶身完整，背景干净并带少量水汽。", inputName: "身体乳.jpg", removeLogo: true, itemStates: ["delivered", "delivered", "delivered", "delivered"] },
  { id: "FREE-PARTIAL", state: "partial", time: "昨天 19:08", ratio: "1:1", requested: 4, prompt: "透明果汁瓶漂浮在冰块与柑橘切片之间，明亮夏日光线。", inputName: "透明果汁.jpg", removeLogo: false, failureKind: "service", itemStates: ["delivered", "delivered", "failed", "ungenerated"] },
  { id: "FREE-FAILED", state: "failed", time: "07-30 11:22", ratio: "1:1", requested: 2, prompt: "透明玻璃杯放在浅色石材桌面，午后侧光和简洁背景。", inputName: "玻璃杯.jpg", removeLogo: false, failureKind: "service", itemStates: ["failed", "failed"] }
];

window.CHAMELEON.wb = {
  unitPrice: 30,
  projects: [
    { id: "PRJ-240716-C08", name: "山野净洗洁精", file: "商品素材_洗洁精.jpg", thumb: "thumb-cleaner", sideThumb: "thumb-cleaner-alt", subjectCount: 2, count: 3, unresolvedBillingCount: 2 },
    { id: "PRJ-240629-D04", name: "绒雾身体乳", file: "商品素材_身体乳.png", thumb: "thumb-lotion", sideThumb: "thumb-lotion", subjectCount: 1, count: 4, unresolvedBillingCount: 0 },
    { id: "PRJ-240618-F21", name: "暮山冷泡茶", file: "商品素材_冷泡茶.jpg", thumb: "thumb-tea", sideThumb: "thumb-night", subjectCount: 2, count: 3, unresolvedBillingCount: 0 },
    { id: "PRJ-240805-A17", name: "暖光护眼台灯", file: "商品素材_台灯.jpg", thumb: "thumb-warm", sideThumb: "thumb-warm", subjectCount: 1, count: 1, unresolvedBillingCount: 0 },
    { id: "PRJ-240806-N01", name: "晨雾保温杯", file: "商品素材_洗洁精.jpg", thumb: "thumb-cleaner", sideThumb: "thumb-cleaner-alt", subjectCount: 0, count: 1, unresolvedBillingCount: 0, isNew: true }
  ],
  mainShots: [
    { id: "marketing", name: "营销图", desc: "带文案的营销头图", copy: "rewrite" },
    { id: "macro1", name: "细节图一", desc: "细节特写 · 配置一", copy: "rewrite" },
    { id: "macro2", name: "细节图二", desc: "细节特写 · 配置二", copy: "rewrite" },
    { id: "scene", name: "场景图", desc: "真实使用场景", copy: "rewrite" },
    { id: "white", name: "白底图", desc: "纯白背景无阴影" }
  ],
  detailSizes: [
    { id: "d1", ratio: "1:1", px: "1024x1024", shape: "square" },
    { id: "d2", ratio: "3:4", px: "1024x1536", shape: "tall" },
    { id: "d3", ratio: "3:4", px: "900x1200", shape: "tall" },
    { id: "d4", ratio: "4:3", px: "1536x1024", shape: "wide" }
  ],
  detailStyles: ["简约白底", "轻奢暖调", "科技深色", "清新自然", "现代商务", "复古质感", "潮流撞色", "国风雅韵", "自定义"],
  detailSections: [
    { id: "hero", name: "首屏主张图", desc: "产品大图 + 核心主张大标题，有冲击力的首屏头图", copy: "rewrite" },
    { id: "points", name: "核心卖点图", desc: "产品图 + 3-4 个核心卖点图文", copy: "rewrite" },
    { id: "scene", name: "使用场景图", desc: "产品放进真实使用场景，生活化氛围", copy: "rewrite" },
    { id: "macro", name: "细节特写图", desc: "局部微距特写，突出材质 / 工艺", copy: "rewrite" },
    { id: "spec", name: "规格参数图", desc: "图示呈现规格 / 尺寸 / 参数", copy: "keep" },
    { id: "brand", name: "品牌保障图", desc: "品牌背书 / 售后 / 质保信任收尾", copy: "rewrite" }
  ],
  referenceAspects: [["composition", "画面构图"], ["scene", "场景与道具"], ["typography", "字体与文字样式"], ["color", "色彩体系"]],
  tasks: function (project, failedKind) {
    return [
      { taskId: "running-main", name: "商品主图生成任务", meta: "今天 16:18 · 3 / 5 张", total: 5, itemStates: ["delivered", "delivered", "delivered", "generating", "pending"], state: "running", stateText: "进行中", thumb: project.thumb },
      { taskId: "completed-main", name: "商品主图生成任务", meta: "07-16 10:42 · 3 套 · 3 张成图", total: 3, itemStates: ["delivered", "delivered", "delivered"], state: "ready", stateText: "已完成", thumb: project.thumb },
      { taskId: "partial-main", name: "商品主图生成任务", meta: "07-12 19:07 · 1 / 3 张已交付", total: 3, itemStates: ["delivered", "failed-safety", "ungenerated"], state: "partial", stateText: "部分完成", thumb: project.sideThumb },
      { taskId: "failed-main", name: "商品主图生成任务", meta: "07-11 14:22 · 0 / 3 张已交付", total: 3, itemStates: failedKind === "recovery-not-started" ? ["ungenerated", "ungenerated", "ungenerated"] : [failedKind === "safety" ? "failed-safety" : "failed-service", "ungenerated", "ungenerated"], failureKind: failedKind || "service", state: "failed", stateText: "失败", thumb: project.sideThumb },
      { taskId: "completed-main-old", name: "商品主图生成任务", meta: "07-09 09:31 · 2 套 · 2 张成图", total: 2, itemStates: ["delivered", "delivered"], state: "ready", stateText: "已完成", thumb: project.thumb }
    ];
  },
  outputs: function (project, task) {
    var base = [
      { id: "OUT-MARKETING", name: "营销图 · 柔润留香", functionName: "营销图", visualPlan: "视觉方案 VS-0629-A2", subjectId: "front", subject: "商品主体图 1", thumb: project.thumb },
      { id: "OUT-DETAIL", name: "细节图 · 乳霜质感", functionName: "细节图", visualPlan: "视觉方案 VS-0629-B1", subjectId: "front", subject: "商品主体图 1", thumb: "thumb-paper", usedReference: true },
      { id: "OUT-WHITE", name: "白底图 · 标准展示", functionName: "白底图", visualPlan: "视觉方案 VS-0629-C4", subjectId: "front", subject: "商品主体图 1", thumb: project.sideThumb },
      { id: "OUT-SCENE", name: "场景图 · 厨房晨光", functionName: "场景图", visualPlan: "视觉方案 VS-0629-D3", subjectId: "front", subject: "商品主体图 1", thumb: "thumb-warm" },
      { id: "OUT-MACRO", name: "细节图 · 泡沫特写", functionName: "细节图", visualPlan: "视觉方案 VS-0629-E2", subjectId: "front", subject: "商品主体图 1", thumb: "thumb-night" }
    ];
    var total = task && task.total ? task.total : 3;
    return Array.from({ length: total }, function (_, i) { var c = Object.assign({}, base[i % base.length]); c.id = c.id + "-" + (i + 1); c.setName = "第 " + (i + 1) + " 张"; c.itemState = task && task.itemStates ? task.itemStates[i] : "delivered"; return c; });
  },
  subjects: function (project) {
    var s = []; var n = typeof project.originalSubjectCount === "number" ? project.originalSubjectCount : project.subjectCount;
    if (n > 0) s.push({ id: "front", name: "商品主体图 1", origin: "已保存到当前商品项目", thumb: project.thumb });
    if (n > 1) s.push({ id: "side", name: "商品主体图 2", origin: "已保存到当前商品项目", thumb: project.sideThumb });
    if (project.hasAddedSubject) s.push({ id: "added", name: "商品主体图 " + (n + 1), origin: "由刚确认的商品素材保存", thumb: project.sideThumb });
    return s;
  }
};
