const calls = [];
const answers = window.__STORY_ANSWERS__ || {};
const answerIndexes = new Map();

function answerFor(method, path) {
  const key = `${method} ${path}`;
  const configured = answers[key];
  if (Array.isArray(configured)) {
    const index = answerIndexes.get(key) || 0;
    answerIndexes.set(key, index + 1);
    return configured[Math.min(index, configured.length - 1)];
  }
  return configured;
}

const {makeApi} = await import("/product/api.mjs");
const api = makeApi(async (method, path, fields = undefined) => {
  calls.push({method, path, fields});
  const answer = answerFor(method, path) || {status: 200, body: {}};
  if (answer.never) return new Promise(() => {});
  const status = answer.status ?? 200;
  const body = Object.hasOwn(answer, "body") ? answer.body : {};
  return {
    ok: status >= 200 && status < 300,
    status,
    async json() { return structuredClone(body); },
  };
});
window.storyApi = api;
window.storyCalls = () => calls.map(call => structuredClone(call));

const params = new URLSearchParams(location.search);
const page = params.get("page") || "";
const sceneName = params.get("scene") || "";
const scenes = await fetch("/scenes.json").then(response => response.json());
const scene = scenes.find(candidate => candidate.name === sceneName);
if (!scene) throw new Error(`unknown scene: ${sceneName}`);
const inputResponse = await fetch(`/scene-input.json?scene=${encodeURIComponent(sceneName)}`);
if (!inputResponse.ok) {
  const reason = (await inputResponse.text()).trim();
  throw new Error(reason || `scene input unavailable for ${sceneName}`);
}
const input = await inputResponse.json();
const adapter = await import(`/adapters/${encodeURIComponent(page)}.mjs`);
adapter.render(document.querySelector("#story-host"), input, api);
