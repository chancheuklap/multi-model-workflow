import { test, expect } from 'e2e';

test('the board opens on this repository and its settings sheet opens from the gear', async ({ app, screen }) => {
  await app.open('/');
  await expect(screen.getByText('chancheuklap/multi-model-workflow')).toBeVisible();
  await screen.getByRole('button', '本机配置').tap();
  await expect(screen.getByRole('heading', '这台机器上，每个 agent 跑在哪')).toBeVisible();
});
