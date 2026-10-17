// What the board's settings sheet loads when MMW_BOARD_PROTOTYPE names this file: the variant
// `?variant=` picks (WINNER by default) behind the API fake, with the shared switcher.
// `?sheet=1` opens 本机配置 as soon as the board has loaded.
import {withFake} from "./fake.mjs";
import {mountSwitcher} from "../../switcher.mjs";

const VARIANTS = {
  定稿: "./winner/sheet.mjs",
  1: "./candidates/1/sheet.mjs", 2: "./candidates/2/sheet.mjs", 3: "./candidates/3/sheet.mjs",
};
const WINNER = "定稿";

const params = new URLSearchParams(location.search);
let key = VARIANTS[params.get("variant")] ? params.get("variant") : WINNER;
const loaded = {};

async function load(k) {
  if (!loaded[k]) {
    try {
      loaded[k] = await import(VARIANTS[k]);
    } catch (error) {
      loaded[k] = placeholder(k, error);
    }
  }
  return loaded[k];
}

function placeholder(k, error) {
  return {
    name: "还没做好",
    fromPayload: payload => ({payload}),
    render(host, _model, _api, hooks) {
      const box = document.createElement("div");
      box.dataset.screen = "settings";
      Object.assign(box.style, {position: "absolute", inset: "40px", background: "#fff", padding: "24px",
        font: "14px system-ui", overflow: "auto"});
      box.textContent = `原型 ${k} 加载失败：${error.message}`;
      const close = document.createElement("button");
      close.textContent = "关闭";
      close.onclick = () => { host.replaceChildren(); hooks.onClose?.(); };
      box.append(" ", close);
      host.replaceChildren(box);
      return box;
    },
    unmount: host => host.replaceChildren(),
  };
}

let current = await load(key);
let last = null;

function switcher() {
  mountSwitcher({
    keys: Object.keys(VARIANTS), current: key,
    names: Object.fromEntries(Object.entries(loaded).map(([k, m]) => [k, m.name || ""])),
    onSwitch: async next => {
      const url = new URL(location.href);
      url.searchParams.set("variant", next);
      history.replaceState(null, "", url);
      key = next;
      current = await load(next);
      if (last) {
        current.render(last.host, current.fromPayload(last.payload), last.api, last.hooks);
      }
      switcher();
    },
  });
}

export function fromPayload(payload) {
  const faked = withFake(payload);
  const model = current.fromPayload(faked);
  model._payload = faked;
  return model;
}

export function render(host, model, api, hooks = {}) {
  last = {host, payload: model._payload, api, hooks};
  const root = current.render(host, model, api, hooks);
  switcher();
  return root;
}

export function unmount(host) {
  last = null;
  document.querySelector("[data-prototype-switcher]")?.remove();
  return current.unmount(host);
}

if (params.get("sheet") === "1") {
  const open = () => {
    const gear = document.querySelector('[data-ui="顶栏.settings"]');
    if (gear) gear.click(); else setTimeout(open, 100);
  };
  setTimeout(open, 0);
}
