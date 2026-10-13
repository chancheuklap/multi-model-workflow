import type { E2EConfig } from 'e2e';
import { web } from '@e2e-dev/web';
import { electronProvider } from './electron-provider.ts';
export default {
  targets: [{
    name: 'product',
    engine: web({ browser: electronProvider }),
    app: { url: 'http://127.0.0.1:0', command: { executable: 'node', args: ['serve.mjs'], env: { PORT: '{port}' }, log: '.e2e/logs/app.log' } },
  }],
} satisfies E2EConfig;
