import {render as renderProduct} from "/product/topbar.mjs";

function viewFrom(data) {
  const v = data?.vals?.v || {};
  const text = v.readText || "";
  return {
    orangeN: v.orangeN ?? 0,
    greenN: v.greenN ?? 0,
    hollowN: v.hollowN ?? 0,
    inkN: v.inkN ?? 0,
    waiting: v.hasWaiting ? Number((v.waitingSub || "").match(/(\d+)/)?.[1] || 0) : 0,
    readFailed: (v.readCls || "").includes("failed"),
    readClock: (text.match(/(\d{2}:\d{2})/) || [])[1] || "",
    readAgo: Number((text.match(/（(\d+) 分钟前）/) || [])[1] || 0),
    settingsOpen: (data?.vals?.gearCls || "gear") === "gear on",
  };
}

export function render(host, data, api) {
  const root = renderProduct(host, viewFrom(data), api);
  root.dataset.storyRoot = "";
  root.style.height = "52px";
}
