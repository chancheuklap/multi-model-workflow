import type { E2EConfig } from 'e2e';
import { web } from '@e2e-dev/web';

// The repository root: board-instance.py and the board run from there; the runner would otherwise start here.
const root = new URL('../../../', import.meta.url).pathname;

// Each run serves this checkout's board on its own port with a fresh MMW_HOME seeded from
// scripts/dev/board-fixtures/ (scripts/dev/board-instance.py serve). `design` names #1055's prototype, whose mount
// point is taken down: it serves the product until a new prototype adds a mount point and its module here.
const board = (prototype?: string) => ({
  executable: 'python3',
  args: ['scripts/dev/board-instance.py', 'serve', '--port', '{port}',
    ...(prototype ? ['--prototype', prototype] : [])],
  cwd: root,
  startupTimeout: 30_000,
  log: `.e2e/logs/${prototype ? 'design' : 'product'}.log`,
});

const PROTOTYPE = 'efforts/fix-1055/prototypes/1055/UI/mount.mjs';

export default {
  tests: '*.e2e.ts',
  cache: 'off',
  // Every test of a run talks to one board and one models.json; two saving at once get 409 from each other.
  workers: 1,
  targets: [
    { name: 'product', engine: web({ viewport: { width: 1440, height: 900 } }),
      app: { url: 'http://127.0.0.1:0', readyUrl: 'http://127.0.0.1:{port}/api/settings', command: board() } },
    { name: 'design', engine: web({ viewport: { width: 1440, height: 900 } }),
      app: { url: 'http://127.0.0.1:0', readyUrl: 'http://127.0.0.1:{port}/api/settings', command: board(PROTOTYPE) } },
  ],
} satisfies E2EConfig;
