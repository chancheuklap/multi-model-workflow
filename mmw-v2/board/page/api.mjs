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

export const api = {
  board: () => request("GET", "/api/board"),
  refresh: () => request("POST", "/api/board/refresh"),
  settings: () => request("GET", "/api/settings"),
  saveSettings: fields => request("PUT", "/api/settings", fields),
  scanSettings: fields => request("POST", "/api/settings/scan", fields),
};
