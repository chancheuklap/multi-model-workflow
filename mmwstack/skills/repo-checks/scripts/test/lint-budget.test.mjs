import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';
import { cleanConfig, fixture } from './fixture.mjs';

test('lint skips large binaries and rejects repeated out-of-context markers', t => {
  const f = fixture(t);
  const config = cleanConfig();
  config.inert.push('docs/**', 'assets/**');
  f.config(config);
  const binary = Buffer.alloc(128 * 1024 * 1024, 0xff);
  binary[0] = 0;
  binary.write('MMW_BASE_REF', 8192);
  f.write('assets/large.bin', binary);
  const line = `${'Ordinary reference material. '.repeat(150)}CHECK .mmw/data .worktrees/topic dispatch.sh INPUTS\n`;
  f.write('docs/large.md', `# Reference\n${line.repeat(2400)}\n# Checks\nscripts/check uses dispatch.sh and INPUTS.\nMMW_BASE_REF\n`);
  f.commit('Large binary and marker context fixture');
  const result = f.invoke(['lint', '--json'], { timeout: 120_000 });
  assert.equal(result.status, 1, result.stdout + result.stderr);
  assert.equal(result.stderr, '');
  assert.deepEqual(JSON.parse(result.stdout), {
    mode: 'lint', ok: false, exit_code: 1,
    findings: ['MMW_BASE_REF', 'dispatch.sh', 'INPUTS'].map(marker => ({
      rule: 'legacy-marker', path: 'docs/large.md', marker,
      message: `${JSON.stringify('docs/large.md')}: legacy marker ${JSON.stringify(marker)} (${JSON.stringify(marker)})`,
    })),
  });
});

test('lint finds an introduced marker among 8475 tracked files', t => {
  const f = fixture(t);
  const config = cleanConfig();
  config.inert.push('docs/**', 'assets/**');
  f.config(config);
  const payload = 'Ordinary fixture data without legacy mechanism text. '.repeat(20);
  for (let i = 0; i < 8470; i++) {
    const name = String(i).padStart(5, '0');
    const path = [
      `src/module-${name}.js`, `test/unit-${name}.test.mjs`,
      `docs/document-${name}.md`, `assets/data-${name}.json`,
    ][i % 4];
    f.write(path, `${JSON.stringify({ index: i, payload })}\n`);
  }
  f.commit('Exactly 8475 tracked files');
  const count = f.git('ls-files', '-z').split('\0').filter(Boolean).length;
  assert.equal(count, 8475);
  function run(expectedExit, expectedFindings) {
    const result = f.cli('lint', '--json');
    assert.equal(result.status, expectedExit, result.stdout + result.stderr);
    assert.equal(result.stderr, '');
    const facts = JSON.parse(result.stdout);
    assert.equal(facts.mode, 'lint');
    assert.equal(facts.exit_code, expectedExit);
    assert.equal(facts.ok, expectedExit === 0);
    assert.deepEqual(facts.findings.map(({ rule, path, marker }) => ({ rule, path, marker })), expectedFindings);
  }
  assert.equal(f.git('status', '--porcelain'), '');
  run(0, []);
  const sentinel = 'docs/document-00002.md';
  const original = readFileSync(join(f.repo, sentinel));
  f.write(sentinel, 'MMW_BASE_REF\n');
  run(1, [{ rule: 'legacy-marker', path: sentinel, marker: 'MMW_BASE_REF' }]);
  f.write(sentinel, original);
  assert.equal(f.git('status', '--porcelain'), '');
});
