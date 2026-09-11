const token = typeof document === "undefined"
  ? ""
  : document.querySelector('meta[name="mmw-page-token"]')?.content || "";

export async function request(method, path, fields = undefined) {
  const options = {method, headers: {"Accept": "application/json"}};
  if (method !== "GET") options.headers["X-MMW-Token"] = token;
  if (fields !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(fields);
  }
  return fetch(path, options);
}

export function makeApi(transport = request) {
  return {
    board: () => transport("GET", "/api/board"),
    refresh: () => transport("POST", "/api/board/refresh"),
    settings: () => transport("GET", "/api/settings"),
    saveSettings: fields => transport("PUT", "/api/settings", fields),
    scanSettings: fields => transport("POST", "/api/settings/scan", fields),
  };
}

export const api = makeApi();
