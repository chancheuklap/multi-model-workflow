import {Board} from "./board-logic.mjs";
import {el, hand, hhmm, minutes} from "./shared.mjs";

const REFRESH_ICON = '<svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"></path><path d="M21 3v5h-5"></path></svg>';
const GEAR_ICON = '<svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path><circle cx="12" cy="12" r="3"></circle></svg>';

function clockFrom(text) {
  return (text || "").match(/(\d{2}:\d{2})/)?.[1] || "";
}

function agoFrom(text) {
  return Number((text || "").match(/（(\d+) 分钟前）/)?.[1] || 0);
}

export function fromScene(data = {}) {
  const v = data.vals?.v || {};
  return {
    orangeN: v.orangeN ?? 0,
    greenN: v.greenN ?? 0,
    hollowN: v.hollowN ?? 0,
    inkN: v.inkN ?? 0,
    waiting: v.hasWaiting ? Number((v.waitingSub || "").match(/(\d+)/)?.[1] || 0) : 0,
    readFailed: (v.readCls || "").includes("failed"),
    readClock: clockFrom(v.readText),
    readAgo: agoFrom(v.readText),
    settingsOpen: (data.vals?.gearCls || "gear") === "gear on",
  };
}

export function fromBoard(payload = {}, now = new Date()) {
  const tasks = payload.tasks || [];
  const all = tasks.flatMap(task => Board.allTickets(task));
  const count = light => all.filter(ticket => Board.light(ticket) === light).length;
  const waiting = all.filter(ticket => Board.step(ticket) === "waiting").length;
  const readAt = payload.read_failed?.at || payload.read_at;
  return {
    orangeN: count("orange"),
    greenN: count("green"),
    hollowN: count("hollow"),
    inkN: count("ink"),
    waiting,
    readFailed: Boolean(payload.read_failed),
    readClock: readAt ? hhmm(readAt) : "",
    readAgo: readAt ? minutes(readAt, now) : 0,
    settingsOpen: Boolean(payload.settingsOpen),
  };
}

async function notify(method, hook) {
  await hand(async () => {
    const response = await method();
    if (response.ok) hook?.(await response.json());
  });
}

export function render(host, view = {}, api, hooks = {}) {
  const orangeN = view.orangeN ?? 0;
  const hot = orangeN > 0;
  const waiting = view.waiting || 0;
  const read = view.readFailed
    ? {cls: "readstate failed", text: `读 GitHub 失败 · 下面是 ${view.readClock} 的数据（${view.readAgo} 分钟前）`}
    : {cls: "readstate", text: view.readClock ? `只读 · ${view.readClock} 读取` : ""};
  const root = el("header", {class: "topbar board"});
  root.dataset.screen = "topbar";
  root.append(
    el("div", {class: "brand"},
      el("span", {class: "brand-mark"}, "MMW"),
      el("span", {class: "brand-name"}, "task board"),
      el("span", {class: "brand-repo"}, "chancheuklap/multi-model-workflow"),
    ),
    el("div", {class: "counters"},
      el("button", {
        type: "button",
        class: hot ? "counter hot" : "counter",
        disabled: !hot,
        title: "跳到下一张需要你的票",
        onClick: () => hooks.onJumpNeedYou?.(),
      }, el("span", {class: hot ? "light orange" : "light hollow"}),
        "需要你", el("span", {class: hot ? "counter-n hot" : "counter-n"}, String(orangeN))),
      el("span", {class: "counter"},
        el("span", {class: "light green"}), "在跑",
        el("span", {class: "counter-n"}, String(view.greenN ?? 0)),
        waiting ? el("span", {class: "counter-sub"}, `其中等槽位 ${waiting}`) : null),
      el("span", {class: "counter"},
        el("span", {class: "light hollow"}), "待派",
        el("span", {class: "counter-n"}, String(view.hollowN ?? 0))),
      el("span", {class: "counter"},
        el("span", {class: "light ink"}), "好了",
        el("span", {class: "counter-n"}, String(view.inkN ?? 0))),
    ),
    el("div", {class: read.cls}, read.text),
    el("button", {
      type: "button", class: "gear",
      "aria-label": "立刻重读 GitHub",
      title: "立刻重读 GitHub（页面开着时每分钟自动读一次）",
      html: REFRESH_ICON,
      onClick: () => { void notify(() => api.refresh(), hooks.onRefresh); },
    }),
    el("button", {
      type: "button", class: view.settingsOpen ? "gear on" : "gear",
      "aria-label": "本机配置",
      title: "本机配置：每个角色跑在哪个 host、model、effort",
      html: GEAR_ICON,
      onClick: () => { void notify(() => api.settings(), hooks.onOpenSettings); },
    }),
  );
  host.replaceChildren(root);
  return root;
}
