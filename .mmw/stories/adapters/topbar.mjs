import {fromBoard, render as renderProduct} from "/product/topbar.mjs";

export function render(host, data, api) {
  const transitions = [];
  window.storyTransitions = () => structuredClone(transitions);

  const move = (scene, value = null) => transitions.push({scene, data: value});
  const paint = payload => {
    const root = renderProduct(host, fromBoard(payload, new Date(data.now)), api, {
      onJumpNeedYou() {
        move("Component · 详情.ticket-returned");
      },
      onRefresh(value) {
        move(value.read_failed ? "Component · 顶栏.bad-data" : "Component · 顶栏.morning", value);
        paint(value);
      },
      onOpenSettings(value) {
        move("Component · 本机配置.mine", value);
      },
    });
    root.dataset.storyRoot = "";
    root.style.height = "52px";
  };
  paint(data.payload);
}
