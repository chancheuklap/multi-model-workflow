import {fromBoard, render as renderProduct} from "/product/topbar.mjs";

// Scene input is TOPBAR_SCENES.<scene>: the design page's own fields, copied
// onto the component view. A missing field stays missing.
function viewFromScene(scene) {
  return {
    orangeN: scene.orangeN,
    greenN: scene.greenN,
    hollowN: scene.hollowN,
    inkN: scene.inkN,
    waiting: scene.waiting,
    readFailed: scene.readFailed,
    readText: scene.readText,
    settingsOpen: scene.settingsOpen,
  };
}

export function render(host, data, api) {
  const transitions = [];
  window.storyTransitions = () => structuredClone(transitions);

  const move = (scene, value = null) => transitions.push({scene, data: value});
  const paint = view => {
    const root = renderProduct(host, view, api, {
      onJumpNeedYou() {
        move("Component · 详情.ticket-returned");
      },
      onRefresh(value) {
        const failed = Boolean(value && value.read_failed);
        move(failed ? "Component · 顶栏.bad-data" : "Component · 顶栏.morning", value);
        paint(fromBoard(value));
      },
      onOpenSettings(value) {
        move("Component · 本机配置.mine", value);
      },
    });
    root.dataset.storyRoot = "";
    root.style.cssText = "width:1440px;height:52px";
  };
  paint(viewFromScene(data));
}
