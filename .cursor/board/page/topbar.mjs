import {render as renderLayout} from './topbar-layout.mjs';
export {fromBoard} from './topbar-layout.mjs';

export function render(host, view, api, hooks) {
  const root = renderLayout(host, view, api, hooks);
  const settings = root.querySelector('[data-ui="顶栏.settings"]');
  settings.setAttribute('aria-label', '项目模型配置');
  settings.title = '项目模型配置：下一轮使用的 host、model、effort 与并行 Worker 数';
  return root;
}
