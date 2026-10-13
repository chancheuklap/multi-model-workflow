import { test, expect } from 'e2e';
import fs from 'node:fs'; import path from 'node:path';
test('starts a dubbing job', async ({ app, screen }) => {
  await app.open('/index.html');
  await expect(screen.getByRole('heading', 'Parrot stand-in')).toBeVisible();
  await screen.getByRole('button', '开始配音').click();
  await expect(screen.getByRole('status')).toContainText('已开始');
  expect(fs.readFileSync(path.join(process.env.E2E_DATA_DIR!, 'job.txt'), 'utf8')).toBe('dubbing');
});
