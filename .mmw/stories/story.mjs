const calls = [];
const {makeApi} = await import("/product/api.mjs");
const api = makeApi(async (method, path, fields = undefined) => {
  calls.push({method, path, fields});
  return {ok: true, status: 200, async json() { return {}; }};
});
window.storyApi = api;
window.storyCalls = () => calls.map(call => structuredClone(call));

const params = new URLSearchParams(location.search);
const page = params.get("page") || "";
const sceneName = params.get("scene") || "";
const scenes = await fetch("/scenes.json").then(response => response.json());
const scene = scenes.find(candidate => candidate.name === sceneName);
if (!scene) throw new Error(`unknown scene: ${sceneName}`);
const adapter = await import(`/adapters/${encodeURIComponent(page)}.mjs`);
adapter.render(document.querySelector("#story-host"), scene.data, api);
