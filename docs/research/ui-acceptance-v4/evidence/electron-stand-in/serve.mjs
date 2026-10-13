import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const here = path.dirname(new URL(import.meta.url).pathname);
http.createServer((q, s) => { const f = path.join(here, 'app', q.url === '/' ? 'index.html' : q.url);
  fs.existsSync(f) ? (s.writeHead(200, { 'content-type': 'text/html' }), s.end(fs.readFileSync(f))) : (s.writeHead(404), s.end()); })
  .listen(Number(process.env.PORT), '127.0.0.1');
