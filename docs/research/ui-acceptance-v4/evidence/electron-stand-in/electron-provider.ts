import { spawn, type ChildProcess } from 'node:child_process';
import fs from 'node:fs'; import os from 'node:os'; import path from 'node:path';
import electron from 'electron';
const procs = new Map<string, ChildProcess>();
export const electronProvider = {
  name: 'electron',
  scope: 'attempt' as const,
  acquire: async () => {
    const run = fs.mkdtempSync(path.join(os.tmpdir(), 'parrot-e2e-'));
    const ud = path.join(run, 'user-data'), data = path.join(run, 'data');
    fs.mkdirSync(data, { recursive: true });
    process.env.E2E_DATA_DIR = data;
    const child = spawn(electron as unknown as string, ['app/main.cjs', '--remote-debugging-port=0', `--user-data-dir=${ud}`],
      { env: { ...process.env, RENDERER_URL: 'about:blank#', DATA_DIR: data }, stdio: 'ignore' });
    const file = path.join(ud, 'DevToolsActivePort');
    for (let i = 0; i < 300 && !fs.existsSync(file); i++) await new Promise((r) => setTimeout(r, 100));
    const [port] = fs.readFileSync(file, 'utf8').split('\n');
    procs.set(run, child);
    return { id: run, cdpEndpoint: `http://127.0.0.1:${port}` };
  },
  release: async (lease: { id: string }) => {
    const child = procs.get(lease.id); procs.delete(lease.id);
    if (child && child.exitCode === null) { child.kill('SIGTERM'); await new Promise((r) => child.once('exit', r)); }
  },
};
