import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { cpus, loadavg } from 'node:os';
import test from 'node:test';
import { cleanConfig, fixture } from './fixture.mjs';

test('selection meets 2000ms in three fresh JSON runs over exactly 8475 tracked files', t => {
  const f = fixture(t);
  const c = cleanConfig();
  c.inert.push('docs/**', 'assets/**');
  c.affects_all.push('package-lock.json');
  c.checks = [{
    id: 'unit', inputs: ['test/**'], sources: ['src/**'], tests: ['test/**'],
    select: 'node -e \'console.log(JSON.stringify(["test/unit-00001.test.mjs"]))\'',
    run: 'node -e \'console.log(JSON.stringify(process.argv.slice(1)))\' -- {tests}',
    run_all: 'node -e \'console.log("whole unit")\'',
    ci: false, ci_reason: 'Local suite.',
  }, {
    id: 'tools', inputs: ['tools/**'], tests: [], run: 'node -e \'console.log("tools")\'',
    ci: false, ci_reason: 'Local tools.',
  }];
  f.config(c);
  for (let i = 0; i < 8472; i++) {
    const name = String(i).padStart(5, '0');
    const path = [`src/module-${name}.js`, `test/unit-${name}.test.mjs`,
      `docs/document-${name}.md`, `assets/data-${name}.json`][i % 4];
    f.write(path, `Ordinary fixture payload ${i}.\n`);
  }
  f.commit('Exactly 8475 tracked files');
  f.git('push', 'origin', 'main');
  f.git('switch', '-c', 'selection-budget');
  f.write('src/module-00000.js', 'Changed source.\n');
  f.commit('One affected source');
  assert.equal(f.git('ls-files', '-z').split('\0').filter(Boolean).length, 8475);
  const loadBefore = loadavg();
  const runs = [];
  for (let trial = 0; trial < 3; trial++) {
    const result = f.cli('--json');
    assert.equal(result.status, 0, result.stdout + result.stderr);
    assert.equal(result.stderr, '');
    const facts = JSON.parse(result.stdout);
    assert.equal(facts.mode, 'run');
    assert.equal(facts.ok, true);
    assert.equal(facts.exit_code, 0);
    assert.deepEqual(facts.selection.map(x => [x.check.id, x.scope.kind, x.scope.tests]), [
      ['unit', 'narrowed', ['test/unit-00001.test.mjs']],
    ]);
    assert.deepEqual(facts.results.map(x => [x.id, x.status]), [['unit', 'passed']]);
    assert.deepEqual(JSON.parse(readFileSync(facts.results[0].log, 'utf8')), ['test/unit-00001.test.mjs']);
    assert.equal(facts.summary.selected, 1);
    assert.equal(facts.summary.passed, 1);
    assert.ok(facts.timing.select_ms >= 0);
    runs.push({ select_ms: facts.timing.select_ms, fetch_ms: facts.timing.fetch_ms,
      selector_ms: facts.timing.selector_ms, elapsed_ms: result.elapsed_ms,
      selected: facts.selection.map(x => x.check.id), exit_code: result.status });
  }
  f.write('package-lock.json', '{}\n');
  const control = f.cli('--json');
  assert.equal(control.status, 0, control.stdout + control.stderr);
  const controlFacts = JSON.parse(control.stdout);
  assert.deepEqual(controlFacts.selection.map(x => [x.check.id, x.scope.kind]), [['unit', 'whole'], ['tools', 'whole']]);
  assert.equal(controlFacts.summary.passed, 2);
  console.log(JSON.stringify({
    node: process.version, platform: process.platform, cores: cpus().length, load_before: loadBefore,
    tracked_files: 8475, command: 'scripts/check --json', budget_ms: 2000,
    cache: 'Fresh engine processes. Filesystem cache is not flushed after fixture setup.',
    timing_scope: 'Merge-base, local git collection and planning; fetch and selector subprocess waits excluded.',
    runs, negative_control: { selected: ['unit', 'tools'], passed: controlFacts.summary.passed },
  }, null, 2));
  for (const run of runs) assert.ok(run.select_ms <= 2000, `Selection exceeded 2000ms: ${run.select_ms}ms`);
});
