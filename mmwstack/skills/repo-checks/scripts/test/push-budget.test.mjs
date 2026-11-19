import assert from 'node:assert/strict';
import test from 'node:test';
import { cleanConfig, fixture } from './fixture.mjs';

test('push selects only relevant changes among 8475 tracked files', t => {
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
    return facts;
  };
  const inert = run();
  assert.deepEqual(inert.changed_paths, ['README.md']);
  assert.deepEqual(inert.selection, []);
  assert.deepEqual(inert.results, []);
  f.write('src/module-00000.js', 'Committed selected source.\n');
  f.commit('Negative control selected source');
  const control = run();
  assert.deepEqual(control.selection.map(x => x.check.id), ['unit']);
  assert.equal(control.results[0].status, 'passed');
  assert.equal(control.results[0].reused, false);
});
