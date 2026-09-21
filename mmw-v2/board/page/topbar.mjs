import {Board, LAMP_WORD} from "./board-logic.mjs";
import {el, hand, hhmm, minutes} from "./shared.mjs";

const REFRESH_ICON = '<svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"></path><path d="M21 3v5h-5"></path></svg>';
const GEAR_ICON = '<svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path><circle cx="12" cy="12" r="3"></circle></svg>';

function sameLocalDay(left, right) {
  return left.getFullYear() === right.getFullYear()
    && left.getMonth() === right.getMonth()
    && left.getDate() === right.getDate();
}

function dataTime(value, now) {
  const read = new Date(value);
  if (sameLocalDay(read, now)) return hhmm(read);
  return `${read.getMonth() + 1} 月 ${read.getDate()} 日 ${hhmm(read)}`;
}

function age(value, now) {
  const elapsed = minutes(value, now);
  return elapsed < 60 ? `${elapsed} 分钟前` : `${Math.floor(elapsed / 60)} 小时前`;
}

export function fromBoard(payload = {}, now = new Date()) {
  const tasks = payload.tasks || [];
  const all = tasks.flatMap(task => Board.allTickets(task));
  const count = lamp => all.filter(ticket => Board.lamp(ticket) === lamp).length;
  const waiting = all.filter(ticket => Board.phase(ticket) === "waiting").length;
  const readAt = payload.read_at;
  const failed = Boolean(payload.read_failed);
  return {
    orangeN: count("orange"),
    greenN: count("green"),
    hollowN: count("hollow"),
    inkN: count("ink"),
    waiting,
    readFailed: failed,
    readClock: readAt ? (failed ? dataTime(readAt, now) : hhmm(readAt)) : "",
    readAgo: readAt ? age(readAt, now) : "",
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
    ? {cls: "readstate failed", text: view.readClock
      ? `读 GitHub 失败 · 下面是 ${view.readClock} 的数据（${view.readAgo}）`
      : "读 GitHub 失败"}
    : {cls: "readstate", text: view.readClock ? `只读 · ${view.readClock} 读取` : ""};
  const root = el("header", {class: "topbar board", "data-ui": "顶栏.root"});
  root.dataset.screen = "topbar";
  root.append(
    el("div", {class: "brand", "data-ui": "顶栏.brand"},
      el("span", {class: "brand-mark", "data-ui": "顶栏.brand.mark"}, "MMW"),
      el("span", {class: "brand-name", "data-ui": "顶栏.brand.name"}, "task board"),
      el("span", {class: "brand-repo", "data-ui": "顶栏.brand.repo"}, "chancheuklap/multi-model-workflow"),
    ),
    el("div", {class: "counters"},
      el("button", {
        type: "button",
        class: hot ? "counter hot" : "counter",
        disabled: !hot,
        "data-ui": "顶栏.needs-you",
        title: "跳到下一张 needs you 的 ticket",
        onClick: () => hooks.onJumpNeedYou?.(),
      }, el("span", {class: hot ? "lamp orange" : "lamp hollow", "data-ui": "顶栏.needs-you.lamp"}),
        LAMP_WORD.orange, el("span", {class: hot ? "counter-n hot" : "counter-n", "data-ui": "顶栏.needs-you.count"}, String(orangeN))),
      el("span", {class: "counter", "data-ui": "顶栏.running"},
        el("span", {class: "lamp green", "data-ui": "顶栏.running.lamp"}), LAMP_WORD.green,
        el("span", {class: "counter-n", "data-ui": "顶栏.running.count"}, String(view.greenN ?? 0)),
        waiting ? el("span", {class: "counter-sub", "data-ui": "顶栏.running.sub"}, `waiting for a slot ${waiting}`) : null),
      el("span", {class: "counter", "data-ui": "顶栏.queued"},
        el("span", {class: "lamp hollow", "data-ui": "顶栏.queued.lamp"}), LAMP_WORD.hollow,
        el("span", {class: "counter-n", "data-ui": "顶栏.queued.count"}, String(view.hollowN ?? 0))),
      el("span", {class: "counter", "data-ui": "顶栏.done"},
        el("span", {class: "lamp ink", "data-ui": "顶栏.done.lamp"}), LAMP_WORD.ink,
        el("span", {class: "counter-n", "data-ui": "顶栏.done.count"}, String(view.inkN ?? 0))),
    ),
    el("div", {class: read.cls, "data-ui": "顶栏.read-state"}, read.text),
    el("button", {
      type: "button", class: "gear",
      "aria-label": "立刻重读 GitHub",
      title: "立刻重读 GitHub（页面开着时每分钟自动读一次）",
      "data-ui": "顶栏.refresh",
      html: REFRESH_ICON,
      onClick: () => { void notify(() => api.refresh(), hooks.onRefresh); },
    }),
    el("button", {
      type: "button", class: view.settingsOpen ? "gear on" : "gear",
      "aria-label": "本机配置",
      title: "本机配置：每个 agent 跑在哪个 host、model、effort",
      "data-ui": "顶栏.settings",
      html: GEAR_ICON,
      onClick: () => { void notify(() => api.settings(), hooks.onOpenSettings); },
    }),
  );
  host.replaceChildren(root);
  return root;
}
