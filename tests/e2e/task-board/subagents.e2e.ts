import { test, expect } from 'e2e';

// #1055: the 本机配置 sheet's 子代理 and 型号目录 tabs (feature file features/settings.md).

async function openSheet(app, screen) {
  await app.open('/');
  await screen.getByRole('button', '本机配置').tap();
  await expect(screen.getByRole('heading', '这台机器上，每个 agent 跑在哪')).toBeVisible();
}

// The answer of GET /api/settings, changed by `edit`: for the states no operation on the local board reaches.
async function answerSettings(browser, edit) {
  await browser.route('**/api/settings', async route => {
    if (route.request.method !== 'GET') return route.fallback();
    const body = await (await fetch(route.request.url)).json();
    edit(body);
    return route.fulfill({ json: body });
  });
}

test('a subagent row is set per host, counted, saved, and shown again when the sheet reopens', async ({ app, screen }) => {
  await openSheet(app, screen);
  await screen.getByRole('tab', /^子代理/).tap();
  for (const [row, what] of [
    ['review-axis', 'code-review 的四个审查轴，一个轴派一个'],
    ['reader', '读大量材料，交回压缩过的结论'],
    ['default', '其余点了名的子代理步骤，也包括没点行名的'],
  ]) {
    await expect(screen.getByRole('group', `子代理 ${row}`)).toBeVisible();
    await expect(screen.getByText(what)).toBeVisible();
  }
  const claudeModel = screen.getByRole('combobox', 'reader 的 Claude model');
  const codexModel = screen.getByRole('combobox', 'reader 的 Codex model');
  const codexEffort = screen.getByRole('combobox', 'reader 的 Codex effort');
  await expect(claudeModel.getByRole('option')).toHaveCount(5);
  expect((await claudeModel.getByRole('option').allTextContents())[0]).toBe('跟叫它的会话一样');
  expect(await claudeModel.getByRole('option').allTextContents())
    .toContain('sonnet · Most efficient for simpler tasks');
  await expect(screen.getByRole('combobox', 'reader 的 Claude effort').getByRole('option')).toHaveCount(6);

  await expect(codexModel.getByRole('option')).toHaveCount(8);
  expect(await codexEffort.getByRole('option').allTextContents())
    .toEqual(['跟叫它的会话一样', 'low', 'medium', 'high', 'xhigh', 'max']);
  await codexModel.selectOption('gpt 6 luna');
  await codexEffort.selectOption('xhigh');
  await expect(screen.getByText(/^改了 2 处：/)).toBeVisible();
  await screen.getByRole('button', '保存').tap();
  await expect(screen.getByText(/^已保存/)).toBeVisible();
  await app.screenshot('subagents-saved');

  await screen.getByRole('button', '关闭本机配置').tap();
  await screen.getByRole('button', '本机配置').tap();
  await screen.getByRole('tab', /^子代理/).tap();
  await expect(screen.getByRole('combobox', 'reader 的 Codex model').getByRole('option', { selected: true }))
    .toHaveText('gpt 6 luna');
  await expect(screen.getByRole('combobox', 'reader 的 Codex effort').getByRole('option', { selected: true }))
    .toHaveText('xhigh');
});

test('the model catalog tab says when each host was read and what it offers', async ({ app, screen }) => {
  await openSheet(app, screen);
  await screen.getByRole('tab', /^型号目录/).tap();
  await expect(screen.getByText(/^目录读于 (\d+月\d+日 )?\d\d:\d\d/)).toHaveCount(2);
  await expect(screen.getByText(/^现在可选：opus、fable、sonnet、haiku$/)).toBeVisible();
  await expect(screen.getByText(/^现在可选：gpt 6\.1 sol、/)).toBeVisible();
  await expect(screen.getByText('配置里存的 model 都还在目录里。')).toBeVisible();
  await app.screenshot('catalog');
});

test('a failed catalog read names its kind and detail and keeps the stored catalog', async ({ app, screen, browser }) => {
  await answerSettings(browser, body => {
    body.scan.hosts.codex.failure = { kind: 'timeout', detail: 'codex app-server 30 秒没有回答', at: '2026-10-17T09:05:11Z' };
  });
  await openSheet(app, screen);
  await expect(screen.getByRole('tab', /^型号目录.*读取失败/)).toBeVisible();
  await screen.getByRole('tab', /^型号目录/).tap();
  await expect(screen.getByText(/最近一次读取失败.*超时 · codex app-server 30 秒没有回答。仍在用 (\d+月\d+日 )?\d\d:\d\d 读到的那份。/)).toBeVisible();
  await app.screenshot('read-failed');
});

test('a saved model the catalog no longer lists is named, reachable, and blocks saving', async ({ app, screen, browser }) => {
  await answerSettings(browser, body => {
    body.subagents = { ...(body.subagents || {}), 'review-axis': { claude: { model: 'inherit', effort: 'inherit' }, codex: { model: 'gpt-5.5-sol', effort: 'high' } } };
    if (body.subagent_options) body.subagent_options.labels.codex['gpt-5.5-sol'] = 'gpt 5.5 sol';
    body.stale = [{ cell: 'subagents.review-axis.codex.model', host: 'codex', stored: 'gpt-5.5-sol',
      offered: ['gpt-6.1-sol', 'gpt-6-astra', 'gpt-6-sol', 'gpt-6-luna', 'gpt-5.6-sol', 'gpt-5.6-terra', 'gpt-5.6-luna'] }];
  });
  await openSheet(app, screen);
  await expect(screen.getByRole('tab', /^型号目录.*1 格旧型号/)).toBeVisible();
  await expect(screen.getByRole('button', '保存')).toBeDisabled();
  await screen.getByRole('tab', /^型号目录/).tap();
  await expect(screen.getByText('子代理 review-axis 的 Codex model')).toBeVisible();
  await expect(screen.getByText(/^存的是 gpt 5\.5 sol，codex 的目录里已经没有；现在可选：gpt 6\.1 sol、/)).toBeVisible();
  await screen.getByRole('button', '跳到子代理 review-axis 的 Codex model').tap();
  await expect(screen.getByRole('combobox', 'review-axis 的 Codex model')).toBeFocused();
  await app.screenshot('stale-model');
});
