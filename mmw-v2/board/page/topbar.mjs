const REFRESH_ICON = '<svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"></path><path d="M21 3v5h-5"></path></svg>';
const GEAR_ICON = '<svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path><circle cx="12" cy="12" r="3"></circle></svg>';

const EMPTY_VIEW = {
  orangeN: 0, greenN: 0, hollowN: 0, inkN: 0, hot: false,
  needCls: "counter", needNCls: "counter-n", needLightCls: "light hollow",
  waitingSub: "", readCls: "readstate", readText: "",
  noNeed: true, hasWaiting: false,
};

function el(doc, tag, attrs = {}, ...kids) {
  const node = doc.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "disabled") node.disabled = true;
    else if (key === "html") node.innerHTML = value;
    else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid == null || kid === false) continue;
    node.append(typeof kid === "object" ? kid : String(kid));
  }
  return node;
}

function openSettings(api, hooks) {
  Promise.resolve(api?.settings?.())
    .then(async response => {
      if (!response || response.ok === false) return;
      const sheet = typeof response.json === "function" ? await response.json() : response;
      hooks.onOpenSettings?.(sheet);
    })
    .catch(() => {});
}

export function render(host, data = {}, api = undefined, hooks = {}) {
  const doc = host.ownerDocument || document;
  const vals = data.vals || {};
  const v = vals.v || EMPTY_VIEW;
  const root = el(doc, "header", {class: "topbar board"});
  root.dataset.screen = "topbar";

  const need = el(doc, "button", {
    type: "button",
    class: v.needCls,
    disabled: v.noNeed,
    title: "跳到下一张需要你的票",
    onClick: () => { if (!v.noNeed) hooks.onJumpNeedYou?.(); },
  }, el(doc, "span", {class: v.needLightCls}), "需要你", el(doc, "span", {class: v.needNCls}, String(v.orangeN)));

  const running = el(doc, "span", {class: "counter"},
    el(doc, "span", {class: "light green"}),
    "在跑",
    el(doc, "span", {class: "counter-n"}, String(v.greenN)),
    v.hasWaiting ? el(doc, "span", {class: "counter-sub"}, v.waitingSub) : null,
  );

  const refresh = el(doc, "button", {
    type: "button",
    class: "gear",
    "aria-label": "立刻重读 GitHub",
    title: "立刻重读 GitHub（页面开着时每分钟自动读一次）",
    html: REFRESH_ICON,
    onClick: () => { api?.refresh?.(); },
  });
  const gear = el(doc, "button", {
    type: "button",
    class: vals.gearCls || "gear",
    "aria-label": "本机配置",
    title: "本机配置：每个角色跑在哪个 host、model、effort",
    html: GEAR_ICON,
    onClick: () => openSettings(api, hooks),
  });

  root.append(
    el(doc, "div", {class: "brand"},
      el(doc, "span", {class: "brand-mark"}, "MMW"),
      el(doc, "span", {class: "brand-name"}, "task board"),
      el(doc, "span", {class: "brand-repo"}, "chancheuklap/multi-model-workflow"),
    ),
    el(doc, "div", {class: "counters"},
      need, running,
      el(doc, "span", {class: "counter"},
        el(doc, "span", {class: "light hollow"}), "待派",
        el(doc, "span", {class: "counter-n"}, String(v.hollowN))),
      el(doc, "span", {class: "counter"},
        el(doc, "span", {class: "light ink"}), "好了",
        el(doc, "span", {class: "counter-n"}, String(v.inkN))),
    ),
    el(doc, "div", {class: v.readCls}, v.readText),
    refresh, gear,
  );
  host.replaceChildren(root);
  return root;
}
