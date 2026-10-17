import type { E2EConfig } from 'e2e';
import { web } from '@e2e-dev/web';

export default {
	tests: '*.e2e.ts',
	retries: 0,
	workers: 1,
	targets: [
		{
			name: 'product',
			engine: web(),
			app: {
				url: 'http://127.0.0.1:0',
				command: {
					executable: 'bash',
					args: ['scripts/dev/notes.sh', 'serve', '--port', '{port}', '--temporary-data'],
					cwd: '../../..',
				},
			},
		},
		{
			name: 'design',
			engine: web(),
			app: {
				url: 'http://127.0.0.1:0',
				command: {
					executable: 'bash',
					args: ['scripts/dev/notes.sh', 'serve', '--port', '{port}', '--temporary-data'],
					cwd: '../../..',
					env: { NOTES_PROTOTYPE: '1' },
				},
			},
		},
	],
} satisfies E2EConfig;
