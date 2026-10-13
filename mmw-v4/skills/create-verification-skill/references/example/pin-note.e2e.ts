// tests/e2e/notes/pin-note.e2e.ts
import { test } from '@e2e-dev/web';
import { expect } from 'e2e';
import { designPage } from './helpers/design.ts';

test('pins a note and keeps it pinned after refresh', async ({ app, screen, browser }) => {
	if (app.baseUrl === undefined) throw new Error('Notes targets require app.url');
	const isDesign = new URL(app.baseUrl).pathname === '/notes/';

	if (isDesign) {
		await app.open(designPage({ route: '/notes', state: 'pinned' }));
	} else {
		await app.open('/notes');
		await screen.getByRole('button', 'New note').tap();
		await screen.getByLabel('Title').fill('Release checklist');
		await screen.getByLabel('Body').fill('Tag and publish');
		await screen.getByRole('button', 'Save note').tap();
		await expect(screen.getByRole('heading', 'Release checklist')).toBeVisible();
		await expect(screen.getByRole('button', 'Pin Release checklist')).toBeVisible();
		await screen.getByRole('button', 'Pin Release checklist').tap();
	}

	const assertPinned = async () => {
		await expect(screen.getByRole('heading', 'Release checklist')).toBeVisible();
		await expect(screen.getByRole('status', 'Pin status')).toHaveText('Pinned');
		await expect(screen.getByRole('button', 'Unpin Release checklist')).toBeVisible();
	};
	await assertPinned();
	await browser.reload();
	await assertPinned();
});
