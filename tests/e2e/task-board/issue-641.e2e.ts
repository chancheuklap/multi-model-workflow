import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { createInterface } from 'node:readline';
import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

const root = new URL('../../../', import.meta.url).pathname;

async function fixture(scenario: 'landed-edge' | 'review-return') {
  const child = spawn('python3', ['efforts/fix-641/diagnose.py', 'serve', '--scenario', scenario],
    { cwd: root, stdio: ['pipe', 'pipe', 'pipe'] });
  let errors = '';
  child.stderr.on('data', chunk => { errors += String(chunk); });
  const output = createInterface({ input: child.stdout });
  const lines = output[Symbol.asyncIterator]();
  const close = async () => {
    child.stdin.end();
    if (child.exitCode === null) await once(child, 'close');
    output.close();
    if (child.exitCode !== 0) throw new Error(errors || 'isolated board exited unsuccessfully');
  };
  try {
    const first = await lines.next();
    if (first.done) throw new Error(errors || 'isolated board supplied no origin');
    const ready: unknown = JSON.parse(first.value);
    if (typeof ready !== 'object' || ready === null || !('origin' in ready)
      || typeof ready.origin !== 'string') throw new Error('isolated board supplied an invalid origin');
    const origin = new URL(ready.origin);
    if (origin.protocol !== 'http:' || origin.hostname !== '127.0.0.1') {
      throw new Error('isolated board must serve on local HTTP');
    }
    return {
      origin: origin.href,
      async land() {
        child.stdin.write('land\n');
        const reply = await lines.next();
        if (reply.done || reply.value !== 'landed') throw new Error('GitHub fixture did not change');
      },
      close,
    };
  } catch (error) {
    await close();
    throw error;
  }
}

test('existing board selection and settings controls remain usable', async ({ app, screen, browser }) => {
  const board = await fixture('landed-edge');
  try {
    await app.open(board.origin);
    await expect(screen.getByText('fixture/mmw-641')).toBeVisible();
    await screen.getByRole('button', '#11 source ticket').tap();
    await expect(browser.locator('[data-ui="详情.status.phase"]')).toHaveText('working');
    await screen.getByRole('button', '本机配置').tap();
    await expect(screen.getByRole('heading', '这台机器上，每个 agent 跑在哪')).toBeVisible();
    await screen.getByRole('button', '关闭本机配置').tap();
    await expect(browser.locator('[data-ui="详情.status.phase"]')).toHaveText('working');
    await app.screenshot('existing-controls');
  } finally {
    await board.close();
  }
});

test('manual refresh releases an upstream that GitHub closed and landed', async ({ app, screen, browser }) => {
  const board = await fixture('landed-edge');
  try {
    await app.open(board.origin);
    const source = screen.getByRole('button', '#11 source ticket');
    await expect(source).toBeVisible();
    await source.tap();
    await expect(browser.locator('[data-ui="详情.status.phase"]')).toHaveText('working');
    await app.screenshot('working-before-refresh');
    await board.land();
    await screen.getByRole('button', '立刻重读 GitHub').tap();
    await expect(browser.locator('[data-ui="详情.status.phase"]')).toHaveText('landed');
    await app.screenshot('landed-after-refresh');
    await expect(browser.locator('.e-block.blocked')).toHaveCount(0);
  } finally {
    await board.close();
  }
});

test('a worker that resumes after review has working as its latest event phase', async ({ app, screen, browser }) => {
  const board = await fixture('review-return');
  try {
    await app.open(board.origin);
    await screen.getByRole('button', '#11 source ticket').tap();
    await expect(browser.locator('[data-ui="详情.status.phase"]')).toHaveText('working');
    await app.screenshot('worker-resumed-after-review');
    await expect(browser.locator('[data-ui="详情.event-block.phase"]').last()).toHaveText('working');
  } finally {
    await board.close();
  }
});
