import { test, expect } from 'e2e';

test('an agent row change is counted, saved, and shown again when the sheet reopens', async ({ app, screen }) => {
  await app.open('/');
  await screen.getByRole('button', '本机配置').tap();
  const effort = screen.getByRole('combobox', 'reviewer 的 effort');
  await expect(screen.getByRole('combobox', 'reviewer 的 model')).toHaveValue('sonnet');
  await expect(effort).toHaveValue('high');
  await expect(screen.getByRole('button', '保存')).toBeDisabled();

  await effort.selectOption('medium');
  await expect(screen.getByText(/^改了 1 处/)).toBeVisible();
  await screen.getByRole('button', '保存').tap();
  await expect(screen.getByText(/^已保存/)).toBeVisible();
  await app.screenshot('saved');

  await screen.getByRole('button', '关闭本机配置').tap();
  await screen.getByRole('button', '本机配置').tap();
  await expect(screen.getByRole('combobox', 'reviewer 的 effort')).toHaveValue('medium');
});
