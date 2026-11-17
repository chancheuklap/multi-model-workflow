import assert from 'node:assert/strict';
import test from 'node:test';
import { unlinkSync } from 'node:fs';
import { join } from 'node:path';
import { cleanConfig, fixture, lintJson } from './fixture.mjs';

test('lint accepts a clean Check Config through the repository entry', t => {
  const f = fixture(t);
  assert.deepEqual(lintJson(f, 0), { mode: 'lint', ok: true, exit_code: 0, findings: [] });
  const text = f.cli('lint');
  assert.equal(text.status, 0, text.stderr);
  assert.match(text.stdout, /lint.*clean/i);
});

test('lint exits 2 and names missing or malformed Check Config', t => {
  const f = fixture(t);
  unlinkSync(join(f.repo, '.agents/checks.json'));
  for (const content of [null, '{not json']) {
    if (content !== null) f.write('.agents/checks.json', content);
    const facts = lintJson(f, 2);
    assert.equal(facts.findings[0].rule, 'config-read');
    assert.equal(facts.findings[0].path, '.agents/checks.json');
    assert.match(f.cli('lint').stdout, /\.agents\/checks\.json/);
  }
});

test('lint exits 1 and identifies invalid schema fields', async t => {
  const f = fixture(t);
  const cases = [
    ['root', () => null],
    ['integration', c => { delete c.integration; }],
    ['integration', c => { c.integration = ''; }],
    ['ci_workflow', c => { c.ci_workflow = 5; }],
    ['test_files', c => { c.test_files = '*.test.js'; }],
    ['inert[0]', c => { c.inert = [3]; }],
    ['affects_all[0]', c => { c.affects_all = ['/absolute/**']; }],
    ['marker_exempt[0]', c => { c.marker_exempt = ['../outside']; }],
    ['unknown', c => { c.unknown = true; }],
    ['prepare.run', c => { c.prepare = { run: ' ', stamps: [] }; }],
    ['prepare.stamps', c => { c.prepare = { run: 'npm ci' }; }],
    ['checks', c => { c.checks = {}; }],
    ['checks[0].id', c => { c.checks[0].id = ''; }],
    ['checks[0].run', c => { delete c.checks[0].run; }],
    ['checks[0].run_all', c => { c.checks[0].run_all = 'node {tests}'; }],
    ['checks[0].inputs[0]', c => { c.checks[0].inputs = [false]; }],
    ['checks[0].tests', c => { c.checks[0].tests = null; }],
    ['checks[0].sources', c => { c.checks[0].sources = 'src/**'; c.checks[0].select = 'select'; }],
    ['checks[0].select', c => { c.checks[0].sources = ['src/**']; }],
    ['checks[0].sources', c => { c.checks[0].select = 'select {files}'; }],
    ['checks[0].needs', c => { c.checks[0].needs = 'docker'; }],
    ['checks[0].ci', c => { c.checks[0].ci = 'yes'; }],
    ['checks[0].ci_reason', c => { delete c.checks[0].ci_reason; }],
    ['checks[0].ci_run', c => { c.checks[0].ci = true; }],
    ['checks[0].timeout_s', c => { c.checks[0].timeout_s = 0; }],
    ['checks[0].retry', c => { c.checks[0].retry = 2; }],
    ['checks[0].lock', c => { c.checks[0].lock = ''; }],
    ['checks[0].typo', c => { c.checks[0].typo = true; }],
    ['checks[0].run_all', c => { c.checks[0].run = 'node {files}'; }],
    ['checks[1].id', c => { c.checks.push({ ...c.checks[0] }); }],
    ['ci_workflow', c => { c.checks[0].ci = true; c.checks[0].ci_run = 'npm test'; }],
    ['lanes[0].kind', c => { c.lanes = [{ id: 'live', kind: 'automatic', reason: 'Live', run_by: 'owner', tests: [] }]; }],
    ['lanes[0].reason', c => { c.lanes = [{ id: 'live', kind: 'device', run_by: 'owner', tests: [] }]; }],
    ['lanes[0].run_by', c => { c.lanes = [{ id: 'live', kind: 'device', reason: 'Hardware', tests: [] }]; }],
    ['lanes[0].tests', c => { c.lanes = [{ id: 'live', kind: 'device', reason: 'Hardware', run_by: 'owner', tests: 'test/**' }]; }],
    ['lanes[0].command', c => { c.lanes = [{ id: 'live', kind: 'device', reason: 'Hardware', run_by: 'owner', tests: [], command: 7 }]; }],
    ['excluded[0].paths', c => { c.excluded = [{ paths: 'fixtures/**', reason: 'Data' }]; }],
    ['excluded[0].reason', c => { c.excluded = [{ paths: ['fixtures/**'] }]; }],
  ];
  for (const [field, mutate] of cases) {
    await t.test(field, () => {
      const c = cleanConfig();
      const changed = mutate(c);
      f.config(changed === null ? null : c);
      const facts = lintJson(f, 1);
      assert.ok(facts.findings.some(x => x.rule === 'schema' && x.field === field), JSON.stringify(facts));
      assert.ok(f.cli('lint').stdout.includes(field));
    });
  }
});

test('lint accepts the complete Check Config shape and rejects unknown needs forms', t => {
  const f = fixture(t);
  const c = cleanConfig();
  c.prepare = { run: 'npm ci', stamps: ['package{,-lock}.json'] };
  c.marker_exempt = ['retired/**'];
  Object.assign(c.checks[0], {
    run: 'node --test {tests}', run_all: 'node --test',
    sources: ['lib/**'], select: 'node select.mjs {files}',
    needs: ['cmd:node', 'cmd:pwsh.exe', 'docker', 'os:darwin', 'os:linux', 'os:windows', 'env:API_TOKEN', 'path:node_modules'],
    timeout_s: 30, retry: 1, lock: 'database',
  });
  c.lanes = [{ id: 'live', kind: 'owner-only', reason: 'Real shop', run_by: 'owner', tests: ['live/**'], command: 'npm run live' }];
  c.excluded = [{ paths: ['fixtures/**'], reason: 'Fixture data' }];
  f.config(c);
  lintJson(f, 0);
  for (const need of ['browser', 'os:win32', 'os:freebsd', 'cmd:', 'cmd:two words', 'cmd:/bin/node',
    'env:', 'env:1BAD', 'path:', 'path:/tmp/foo', 'path:../outside', 'path:C:\\outside', 'docker:yes']) {
    c.checks[0].needs = [need];
    f.config(c);
    const facts = lintJson(f, 1);
    assert.ok(facts.findings.some(x => x.rule === 'schema' && x.field === 'checks[0].needs[0]'), `${need}: ${JSON.stringify(facts)}`);
  }
});

test('lint classifies every tracked path using inputs, sources, inert and affects_all', t => {
  const f = fixture(t);
  const c = cleanConfig();
  Object.assign(c.checks[0], { sources: ['lib/**'], select: 'node select.mjs {files}' });
  c.inert.push('docs/**', 'root?.[cm]js', '**/notes.{md,txt}');
  c.affects_all.push('package{,-lock}.json', '.config/**');
  const paths = ['src/a.js', 'lib/nested/b.js', 'docs/a.md', 'root1.mjs', 'package.json',
    'package-lock.json', '.config/tool.json', 'notes.txt', 'nested/notes.md', 'unclaimed name\nwith newline.txt'];
  for (const path of paths) f.write(path, 'Ordinary content.\n');
  f.config(c);
  f.commit();
  f.write('untracked.txt', 'Not part of lint.\n');
  const facts = lintJson(f, 1);
  assert.deepEqual(facts.findings.map(x => [x.rule, x.path]), [
    ['unclassified', 'unclaimed name\nwith newline.txt'],
  ]);
  assert.ok(f.cli('lint').stdout.includes('unclaimed name'));
  c.inert.push('unclaimed*');
  f.config(c);
  lintJson(f, 0);
  c.inert = c.inert.filter(x => x !== 'root?.[cm]js');
  f.config(c);
  assert.deepEqual(lintJson(f, 1).findings.map(x => x.path), ['root1.mjs']);
});

test('lint names tracked tests not claimed by check tests, lanes or exclusions', t => {
  const f = fixture(t);
  const c = cleanConfig();
  c.inert.push('**/*.test.{js,mjs,ts}');
  c.lanes = [{ id: 'live', kind: 'owner-only', reason: 'Real shop', run_by: 'owner', tests: ['live/**'] }];
  c.excluded = [{ paths: ['fixture/**'], reason: 'Data, not executable tests' }];
  for (const path of ['test/unit.test.js', 'live/shop.test.js', 'fixture/data.test.js', 'orphan.test.mjs', 'src/unclaimed.test.ts']) {
    f.write(path, 'Ordinary test fixture.\n');
  }
  f.config(c);
  f.commit();
  f.write('untracked.test.js', 'Not tracked.\n');
  const facts = lintJson(f, 1);
  assert.deepEqual(facts.findings.map(x => [x.rule, x.path]), [
    ['unclaimed-test', 'orphan.test.mjs'],
    ['unclaimed-test', 'src/unclaimed.test.ts'],
  ]);
  const text = f.cli('lint');
  assert.equal(text.status, 1);
  assert.match(text.stdout, /orphan\.test\.mjs/);
  assert.match(text.stdout, /src\/unclaimed\.test\.ts/);
  c.checks[0].tests.push('**/*.test.{mjs,ts}');
  f.config(c);
  lintJson(f, 0);
});

test('lint names ci checks when the gate workflow is missing or ci_run is absent', t => {
  const f = fixture(t);
  const c = cleanConfig();
  c.ci_workflow = 'gate.yml';
  c.inert.push('.github/workflows/**');
  Object.assign(c.checks[0], { ci: true, ci_run: 'node --test test/*.test.mjs' });
  f.config(c);
  let facts = lintJson(f, 1);
  assert.equal(facts.findings[0].rule, 'ci-workflow');
  assert.equal(facts.findings[0].check, 'unit');
  assert.equal(facts.findings[0].path, '.github/workflows/gate.yml');
  f.write('.github/workflows/gate.yml', 'jobs:\n  verify:\n    steps:\n      - run: node --test other/*.test.mjs\n');
  f.commit();
  facts = lintJson(f, 1);
  assert.equal(facts.findings[0].rule, 'ci-command');
  assert.equal(facts.findings[0].check, 'unit');
  assert.match(f.cli('lint').stdout, /unit/);
  f.write('.github/workflows/gate.yml', 'jobs:\n  verify:\n    steps:\n      - run: node --test test/*.test.mjs\n');
  lintJson(f, 0);
  c.ci_workflow = '.github/workflows/gate.yml';
  f.config(c);
  lintJson(f, 0);
});

test('lint rejects run and run_all equal to owner-only or device lane commands', t => {
  const f = fixture(t);
  for (const kind of ['owner-only', 'device']) {
    for (const field of ['run', 'run_all']) {
      const c = cleanConfig();
      c.lanes = [{ id: 'protected', kind, reason: 'Requires explicit authorization', run_by: 'owner', tests: [], command: 'node real-resource.mjs' }];
      c.checks[0][field] = 'node real-resource.mjs';
      f.config(c);
      const facts = lintJson(f, 1);
      assert.ok(facts.findings.some(x => x.rule === 'protected-command' && x.check === 'unit' && x.field === `checks[0].${field}`));
      assert.match(f.cli('lint').stdout, /unit.*protected/);
      c.lanes[0].kind = 'ci-only';
      f.config(c);
      lintJson(f, 0);
    }
  }
});

test('lint requires integration to name an actual origin remote branch, not an arbitrary revision', t => {
  const f = fixture(t);
  f.git('branch', 'local-only');
  f.git('tag', 'tag-only');
  f.git('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main');
  const c = cleanConfig();
  for (const integration of ['missing', 'local-only', 'tag-only', 'HEAD', 'refs/heads/main', 'origin/main', 'main~0', f.git('rev-parse', 'HEAD')]) {
    c.integration = integration;
    f.config(c);
    const facts = lintJson(f, 1);
    assert.equal(facts.findings[0].rule, 'integration');
    assert.equal(facts.findings[0].field, 'integration');
    assert.ok(f.cli('lint').stdout.includes(integration));
  }
  f.git('push', 'origin', 'HEAD:refs/heads/development/integration');
  c.integration = 'development/integration';
  f.config(c);
  lintJson(f, 0);
});

test('lint finds the complete legacy marker list in its specified contexts', t => {
  const f = fixture(t);
  const c = cleanConfig();
  c.inert.push('**');
  const cases = [
    ['docs/base.md', 'Use MMW_BASE_REF for the base.', 'MMW_BASE_REF'],
    ['docs/logs.md', 'Logs live at .scratch/check/run.log.', '.scratch/check'],
    ['docs/header.md', 'Run by MMW before every ticket lands.', 'run by MMW before every ticket lands'],
    ['docs/zh.md', 'MMW 流水线在每张工单合并前、每晚开工前跑默认档。', 'run by MMW before every ticket lands'],
    ['docs/steps.md', 'Run scripts/check --step unit.', 'scripts/check --step'],
    ['docs/dispatch.md', 'Run scripts/check through dispatch.sh land.', 'dispatch.sh'],
    ['docs/verify.md', 'Checks run through verify-ticket.', 'verify-ticket'],
    ['docs/setup.md', 'Install scripts/check with setup-mmw.', 'setup-mmw'],
    ['.gitignore', '.worktrees/\n.scratch/', '.worktrees/'],
    ['.dockerignore', '.worktrees/**', '.worktrees/'],
    ['eslint.config.js', 'export default [{ ignores: [".worktrees/**"] }];', '.worktrees/'],
    ['vitest.config.ts', 'export default { test: { exclude: [".worktrees/**"] } };', '.worktrees/'],
    ['pyproject.toml', '[tool.pytest.ini_options]\nnorecursedirs = [".worktrees/**"]', '.worktrees/'],
    ['.github/workflows/filter.yml', 'on:\n  push:\n    paths-ignore:\n      - ".worktrees/**"\n      - ".mmw/**"\njobs: {}', '.worktrees/'],
    ['.github/workflows/inline.yml', 'on:\n  push:\n    paths: [".mmw/**"]', '.mmw/'],
    ['.github/workflows/flow.yml', 'on: {push: {paths-ignore: [".mmw/**"]}}\njobs: {}', '.mmw/'],
    ['docs/tiers.md', 'scripts/check has three tiers. The default tier selects changes.', 'v4 check tiers'],
    ['docs/all-tier.md', 'scripts/check --all tier runs everything.', 'v4 check tiers'],
    ['docs/staged-tier.md', 'scripts/check --staged tier runs prek.', 'v4 check tiers'],
    ['docs/zh-tiers.md', 'scripts/check 三档，默认档按输入选择。', 'v4 check tiers'],
    ['docs/inputs.md', 'scripts/check selects from the INPUTS table.', 'INPUTS'],
    ['docs/reads.md', 'scripts/check uses READS for disk reads.', 'READS'],
    ['docs/not-inputs.md', 'scripts/check uses NOT_INPUTS exclusions.', 'NOT_INPUTS'],
    ['docs/groups.md', 'scripts/check uses GROUP_MAP for test groups.', 'GROUP_MAP'],
    ['docs/gate-inputs.md', 'scripts/check uses GATE_INPUTS for its gate.', 'GATE_INPUTS'],
    ['.agents/skills/verify-erp/SKILL.md', 'A ticket copies this CHECK line, replacing <file>.', 'verify-erp ticket CHECK'],
  ];
  for (const [path, body] of cases) f.write(path, `${body}\n`);
  f.config(c);
  f.commit();
  const facts = lintJson(f, 1);
  for (const [path, , marker] of cases) {
    assert.ok(facts.findings.some(x => x.rule === 'legacy-marker' && x.path === path && x.marker === marker), `${path}: ${JSON.stringify(facts)}`);
  }
  assert.ok(facts.findings.some(x => x.path === '.github/workflows/filter.yml' && x.marker === '.mmw/'));
  const text = f.cli('lint');
  assert.equal(text.status, 1);
  for (const finding of facts.findings) assert.ok(text.stdout.includes(finding.message));
});

test('lint contextual legacy markers allow unrelated terms and apply marker_exempt only to markers', t => {
  const f = fixture(t);
  const c = cleanConfig();
  c.inert.push('docs/**', 'src/**', '.github/**', '.agents/skills/**', 'retired/**', 'vendor/**', 'pyproject.toml');
  c.marker_exempt = ['retired/**', 'vendor/**'];
  const allowed = [
    ['src/algorithm.js', 'const INPUTS = []; const READS = []; const NOT_INPUTS = []; const GROUP_MAP = {}; const GATE_INPUTS = [];'],
    ['docs/dispatch.md', 'dispatch.sh routes messages. verify-ticket and setup-mmw are historical package names.'],
    ['docs/locations.md', 'A sibling checkout can live in .worktrees/topic. The service uses .mmw/data.'],
    ['docs/tiers.md', 'The default tier is a customer subscription. The plan has three tiers.'],
    ['.github/workflows/service.yml', 'jobs:\n  deploy:\n    steps:\n      - run: echo ".mmw/data .worktrees/local"'],
    ['.github/workflows/job-paths.yml', 'jobs:\n  deploy:\n    steps:\n      - uses: example/action\n        with:\n          paths: [".mmw/cache", ".worktrees/local"]'],
    ['.agents/skills/verify-erp/SKILL.md', 'CHECK is an HTTP request method example.'],
    ['pyproject.toml', '[tool.demo]\ncache_dir = ".worktrees/cache"'],
    ['retired/legacy.md', 'MMW_BASE_REF and scripts/check --step unit'],
    ['vendor/legacy.md', '.scratch/check/run.log'],
  ];
  for (const [path, body] of allowed) f.write(path, body);
  f.config(c);
  f.commit();
  lintJson(f, 0);
  c.inert = c.inert.filter(x => x !== 'retired/**');
  f.write('retired/orphan.test.js', 'MMW_BASE_REF');
  f.config(c);
  f.commit();
  const facts = lintJson(f, 1);
  assert.deepEqual(facts.findings.map(x => [x.rule, x.path]), [
    ['unclassified', 'retired/legacy.md'],
    ['unclassified', 'retired/orphan.test.js'],
    ['unclaimed-test', 'retired/orphan.test.js'],
  ]);
});

test('the CLI advertises implemented modes and refuses unsupported requests', t => {
  const f = fixture(t);
  const help = f.cli('--help');
  assert.equal(help.status, 0);
  assert.match(help.stdout, /lint.*--json/);
  assert.ok(help.stdout.split('\n').length <= 40);
  for (const flag of ['--all', '--only', '--base', '--json', '--help']) assert.ok(help.stdout.includes(flag));
  for (const code of [0, 1, 2, 70]) assert.match(help.stdout, new RegExp(`\\b${code}\\b`));
  assert.doesNotMatch(help.stdout, /--push|--staged|ensure|selftest|replay/);
  for (const args of [['ensure'], ['--push'], ['lint', '--typo'], ['lint', 'extra']]) {
    const facts = JSON.parse(f.cli(...args, '--json').stdout);
    assert.equal(facts.exit_code, 2);
    assert.equal(facts.ok, false);
    const error = facts.mode === 'lint' ? facts.findings[0] : facts.events.find(x => x.type === 'ERROR');
    assert.equal(error.rule, 'usage');
  }
});

test('lint reports an unavailable engine dependency as exit 70 without a test-only switch', t => {
  const f = fixture(t);
  f.env.PATH = f.home;
  const facts = lintJson(f, 70);
  assert.equal(facts.findings[0].rule, 'engine');
});

test('lint JSON and text contain the same accumulated repository findings', t => {
  const f = fixture(t);
  const c = cleanConfig();
  c.integration = 'not-a-branch';
  c.ci_workflow = 'missing.yml';
  Object.assign(c.checks[0], { ci: true, ci_run: 'npm test', run_all: 'npm run live' });
  c.lanes = [{ id: 'live', kind: 'owner-only', reason: 'Real resource', run_by: 'owner', tests: [], command: 'npm run live' }];
  f.config(c);
  f.write('orphan.test.js', 'MMW_BASE_REF\n');
  f.commit();
  const facts = lintJson(f, 1);
  assert.deepEqual(facts.findings.map(x => x.rule), [
    'integration', 'ci-workflow', 'protected-command', 'unclassified', 'unclaimed-test', 'legacy-marker',
  ]);
  const text = f.cli('lint');
  assert.equal(text.status, 1);
  assert.deepEqual(text.stdout.trimEnd().split('\n'), facts.findings.map(x => `LINT ${x.rule} ${x.message}`));
});

test('lint identifies invalid glob syntax as a config finding rather than an engine crash', t => {
  const f = fixture(t);
  const c = cleanConfig();
  c.inert.push('docs/[z-a].md');
  f.config(c);
  const facts = lintJson(f, 1);
  assert.equal(facts.findings[0].rule, 'schema');
  assert.equal(facts.findings[0].field, 'inert[2]');
});
