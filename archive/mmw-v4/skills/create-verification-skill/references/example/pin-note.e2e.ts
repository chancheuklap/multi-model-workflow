import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('pins a note', async ({ app, screen }) => {
	await app.open('/notes');
	await screen.getByRole('button', 'New note').tap();
	await screen.getByLabel('Title').fill('Release checklist');
	await screen.getByLabel('Body').fill('Tag and publish');
	await screen.getByRole('button', 'Save note').tap();
	await expect(screen.getByRole('heading', 'Release checklist')).toBeVisible();
	await expect(screen.getByRole('button', 'Pin Release checklist')).toBeVisible();
	await screen.getByRole('button', 'Pin Release checklist').tap();
	await expect(screen.getByRole('status', 'Pin status')).toHaveText('Pinned');
	await expect(screen.getByRole('button', 'Unpin Release checklist')).toBeVisible();
	await app.screenshot('pinned-note');
});
