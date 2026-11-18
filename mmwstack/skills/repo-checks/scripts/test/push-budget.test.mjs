import assert from 'node:assert/strict';
import { cpus, loadavg } from 'node:os';
import test from 'node:test';
import { cleanConfig, fixture } from './fixture.mjs';

test('empty push meets 5000ms in three fresh processes over exactly 8475 tracked files', t => {
  const f = fixture(t);
  const c = cleanConfig();
  c.inert.push('docs/**', 'assets/**');
  c.checks[0].run = 'node -e \'console.log("source control ran")\'';
  f.config(c);
  for (let i = 0; i < 8470; i++) {
    const name = String(i).padStart(5, '0');
    const path = [`src/module-${name}.js`, `test/unit-${name}.test.mjs`,
      `docs/document-${name}.md`, `assets/data-${name}.json`][i % 4];
    f.write(path, `Ordinary payload ${i}.\n`);
  }
  f.commit('Exactly 8475 tracked files');
  f.git('push', 'origin', 'main');
  f.git('switch', '-c', 'push-budget');
  f.write('README.md', 'Committed inert change, not empty stdin.\n');
  f.commit('Inert change');
  assert.equal(f.git('ls-files', '-z').split('\0').filter(Boolean).length, 8475);
  const loadBefore = loadavg();
  const run = () => {
    const head = f.git('rev-parse', 'HEAD');
    const input = `refs/heads/push-budget ${head} refs/heads/push-budget ${'0'.repeat(40)}\n`;
    const result = f.invoke(['--push', '--json'], { input });
    assert.equal(result.status, 0, result.stdout + result.stderr);
    assert.equal(result.stderr, '');
    const facts = JSON.parse(result.stdout);
    assert.equal(facts.mode, 'push');
    assert.equal(facts.ok, true);
    assert.equal(facts.exit_code, 0);
    assert.equal(facts.push.ranges.length, 1);
    assert.equal(facts.push.ranges[0].head, head);
    assert.equal(facts.push.ranges[0].base, f.git('rev-parse', 'origin/main'));
    assert.equal(facts.push.dirty, false);
    return { facts, elapsed_ms: result.elapsed_ms, exit_code: result.status };
  };
  const runs = Array.from({ length: 3 }, () => {
    const result = run();
    assert.deepEqual(result.facts.changed_paths, ['README.md']);
    assert.deepEqual(result.facts.selection, []);
    assert.deepEqual(result.facts.results, []);
    return { elapsed_ms: result.elapsed_ms, select_ms: result.facts.timing.select_ms,
      fetch_ms: result.facts.timing.fetch_ms, selected: 0, exit_code: result.exit_code };
  });
  f.write('src/module-00000.js', 'Committed selected source.\n');
  f.commit('Negative control selected source');
  const control = run();
  assert.deepEqual(control.facts.selection.map(x => x.check.id), ['unit']);
  assert.equal(control.facts.results[0].status, 'passed');
  assert.equal(control.facts.results[0].reused, false);
  console.log(JSON.stringify({
    node: process.version, platform: process.platform, cores: cpus().length, load_before: loadBefore,
    tracked_files: 8475, command: 'scripts/check --push --json < pre-push-branch-stdin',
    budget_ms: 5000,
    cache: 'Three fresh processes, no push warmup. Filesystem cache is not flushed after fixture setup.',
    timing_scope: 'Complete entry process: stdin, config, integration fetch, selection, storage and summary.',
    runs, negative_control: { elapsed_ms: control.elapsed_ms, selected: ['unit'], passed: 1, exit_code: control.exit_code },
  }, null, 2));
  for (const run of runs) assert.ok(run.elapsed_ms <= 5000, `Empty push exceeded 5000ms: ${run.elapsed_ms}ms`);
});
