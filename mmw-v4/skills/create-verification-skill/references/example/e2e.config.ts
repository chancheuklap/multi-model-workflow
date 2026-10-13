// tests/e2e/notes/e2e.config.ts
import type { E2EConfig } from 'e2e';
import { web } from '@e2e-dev/web';

export default {
	tests: '*.e2e.ts',
	retries: 0,
	targets: [
		{
			name: 'product',
			engine: web(),
			app: {
				url: 'http://127.0.0.1:0',
				command: {
					executable: 'npm',
					args: ['run', 'start', '--', '--port', '{port}', '--temporary-data'],
					cwd: '../../..',
				},
			},
		},
		{
			name: 'design',
			engine: web(),
			app: {
				url: 'http://127.0.0.1:0/notes/',
				command: {
					executable: 'python3',
					args: ['-m', 'http.server', '{port}', '--bind', '127.0.0.1', '--directory', 'design'],
					cwd: '../../..',
				},
			},
		},
	],
} satisfies E2EConfig;
