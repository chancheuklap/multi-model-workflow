import {mountPage} from "/product/app.mjs";

// Scene input is APP_SCENES.<scene>: which example board, which task, which card,
// and which settings scene is already open. The page is the product's mountPage.
// The dataset behind `board` is the example payload that scene was drawn from.

async function readJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    const reason = (await response.text()).trim();
    throw new Error(reason || `${url} returned ${response.status}`);
  }
  return response.json();
}

export async function render(host, data, api) {
  if (!data || !data.board) {
    throw new Error("APP_SCENES scene has no board. The story cannot choose a dataset.");
  }
  host.style.cssText = "width:1440px;height:900px";
  const board = await readJson(`/example-board.json?name=${encodeURIComponent(data.board)}`);
  const settings = data.settings
    ? await readJson(`/scene-input.json?scene=${encodeURIComponent(`Component · 本机配置.${data.settings}`)}`)
    : null;
  const root = mountPage(host, {
    data: {
      payload: board.payload,
      select: {task: data.task ?? null, node: data.sel ?? null},
      now: board.now,
      settingsOpen: Boolean(data.settings),
      settings: settings ? settings.payload : null,
    },
    api,
    live: false,
  });
  root.dataset.storyRoot = "";
  return root;
}
