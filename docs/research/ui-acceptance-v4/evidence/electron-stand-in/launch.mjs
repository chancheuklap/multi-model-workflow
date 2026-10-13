// Stands in for `electron-vite dev`: serves the renderer on PORT, starts Electron with a free CDP port
// and its own user-data dir, and writes the CDP endpoint where the e2e config reads it.
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path'; import { spawn } from 'node:child_process';
import electron from 'electron';
const port = Number(process.env.PORT), run = process.env.RUN_DIR, here = path.dirname(new URL(import.meta.url).pathname);
const ud = path.join(run, 'user-data'), data = path.join(run, 'data'); fs.mkdirSync(ud, { recursive: true }); fs.mkdirSync(data, { recursive: true });
let ready = false;
http.createServer((q, s) => {
  if (q.url === '/__ready') { s.writeHead(ready ? 200 : 503); return s.end(); }
  const f = path.join(here, 'app', q.url === '/' ? 'index.html' : q.url);
  fs.existsSync(f) ? (s.writeHead(200, { 'content-type': 'text/html' }), s.end(fs.readFileSync(f))) : (s.writeHead(404), s.end());
}).listen(port, '127.0.0.1');
const child = spawn(electron, [path.join(here, 'app/main.cjs'), '--remote-debugging-port=0', `--user-data-dir=${ud}`],
  { env: { ...process.env, RENDERER_URL: `http://127.0.0.1:${port}`, DATA_DIR: data }, stdio: 'inherit' });
const t = setInterval(() => { const p = path.join(ud, 'DevToolsActivePort');
  if (fs.existsSync(p)) { const [cdp] = fs.readFileSync(p, 'utf8').split('\n'); fs.writeFileSync(path.join(run, 'cdp'), `http://127.0.0.1:${cdp}`); ready = true; clearInterval(t); } }, 200);
const stop = () => { child.kill('SIGTERM'); process.exit(0); };
process.on('SIGTERM', stop); process.on('SIGINT', stop); child.on('exit', () => process.exit(0));
