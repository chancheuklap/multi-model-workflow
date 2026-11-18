import assert from 'node:assert/strict';
import test from 'node:test';
import { chmodSync, copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, utimesSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { cleanConfig, fixture } from './fixture.mjs';

const engine = new URL('../check.mjs', import.meta.url);
const quote = value => `'${value.replaceAll("'", "'\\''")}'`;
const command = source => `${quote(process.execPath)} -e ${quote(source)}`;
const daysAgo = days => new Date(Date.now() - days * 86400000).toISOString();

function json(f, args, status = 0, options = {}) {
  const result = f.invoke([...args, '--json'], options);
  assert.equal(result.status, status, result.stdout + result.stderr);
  assert.equal(result.stderr, '');
  const facts = JSON.parse(result.stdout);
  assert.equal(facts.exit_code, status);
  assert.equal(facts.ok, status === 0);
  return facts;
}

function setup(t) {
  const f = fixture(t);
  const c = cleanConfig();
  c.checks = ['unit', 'build'].map(id => ({
    id, run: 'touch CHECK_RAN', inputs: [`src/${id}/**`], tests: [],
    ci: false, ci_reason: 'Local fixture check.',
  }));
  c.prepare = { run: 'touch PREPARE_RAN', stamps: ['.agents/checks.json'] };
  f.config(c);
  f.commit('Configure replay fixture');
  f.git('push', 'origin', 'main');
  return { f, c };
}

function records(f, name, entries, audits = []) {
  const folder = join(f.repo, '.git/repo-checks', name);
  mkdirSync(join(folder, 'records'), { recursive: true });
  entries.forEach((entry, i) => writeFileSync(join(folder, 'records', `${i}.json`), JSON.stringify(entry)));
  if (audits.length) writeFileSync(join(folder, 'audit.jsonl'), audits.map(record => JSON.stringify(record)).join('\n') + '\n');
  return folder;
}

function runRecord(overrides = {}) {
  return { mode: 'run', time: daysAgo(1), exit_code: 0, ok: true, results: [], ...overrides };
}

function execution(id, seconds, timeout_s = 600, extra = {}) {
  return { id, seconds, timeout_s, status: 'passed', attempts: [{ exit_code: 0 }], reused: false, recovered: false, ...extra };
}

function snapshot(folder) {
  return readdirSync(folder, { recursive: true }).filter(path => statSync(join(folder, path)).isFile()).sort()
    .map(path => [path, statSync(join(folder, path)).mtimeMs, readFileSync(join(folder, path), 'utf8')]);
}

test('report on empty history returns stable zero facts without a Check Config', t => {
  const f = fixture(t);
  rmSync(join(f.repo, '.agents/checks.json'));
  f.env.MMW_CHECKS_SKIP = 'Report must not bypass or write';
  const facts = json(f, ['report']);
  assert.deepEqual(facts, {
    mode: 'report', ok: true, exit_code: 0,
    runs: { total: 0, passed: 0, failed: 0, blocked: 0, internal_error: 0 },
    bypasses: { count: 0, latest_reason: null, records: [] },
    engine_failures: { count: 0, records: [] },
    retry_recoveries: 0, slow: [], flaky: [], passed_push_commits: [], findings: [],
  });
  const text = f.cli('report');
  assert.equal(text.status, 0, text.stderr);
  assert.match(text.stdout, /RUNS 0 total, 0 passed, 0 failed, 0 blocked, 0 internal errors/);
  assert.match(text.stdout, /BYPASSES 0 in 14 days; latest reason: none/);
  assert.equal(existsSync(join(f.repo, '.git/repo-checks')), false);
});

test('report counts fixture history, bypass reasons, recovery and slow checks without changing history', t => {
  const f = fixture(t);
  const head = f.git('rev-parse', 'HEAD');
  records(f, 'one', [
    runRecord({ results: [execution('unit', 301, 600, { recovered: true })] }),
    runRecord({ mode: 'push', identity: { head, dirty: false }, push: { dirty: false, ranges: [{ head }] } }),
    runRecord({ exit_code: 1, ok: false }),
    runRecord({ exit_code: 2, ok: false }),
    runRecord({ exit_code: 70, ok: false }),
  ], [
    { type: 'bypass', time: daysAgo(1), reason: 'Repair a wrong check', hook: 'pre-push' },
    { type: 'engine-failure', time: daysAgo(1), reason: 'Engine exited 70', hook: 'pre-commit', exit_code: 70 },
    { type: 'bypass', time: daysAgo(15), reason: 'Old bypass', hook: 'pre-push' },
  ]);
  const folder = join(f.repo, '.git/repo-checks');
  const before = snapshot(folder);
  f.write('.agents/checks.json', 'invalid current config');
  const facts = json(f, ['report']);
  assert.equal(facts.mode, 'report');
  assert.deepEqual(facts.runs, { total: 5, passed: 2, failed: 1, blocked: 1, internal_error: 1 });
  assert.equal(facts.bypasses.count, 1);
  assert.equal(facts.bypasses.latest_reason, 'Repair a wrong check');
  assert.equal(facts.bypasses.records[0].hook, 'pre-push');
  assert.equal(facts.engine_failures.count, 1);
  assert.equal(facts.engine_failures.records[0].exit_code, 70);
  assert.equal(facts.retry_recoveries, 1);
  assert.deepEqual(facts.slow, [{ id: 'unit', samples: 1, p90_s: 301, timeout_s: 600 }]);
  assert.deepEqual(facts.flaky, []);
  assert.deepEqual(facts.passed_push_commits, [head]);
  const text = f.cli('report');
  assert.equal(text.status, 0, text.stderr);
  assert.match(text.stdout, /BYPASS .*pre-push: Repair a wrong check/);
  assert.match(text.stdout, /RETRY_RECOVERIES 1 in 14 days/);
  assert.match(text.stdout, /SLOW unit p90=301s over last 1 executions > half timeout 600s/);
  assert.match(text.stdout, new RegExp(`PASSED_PUSH ${head}`));
  assert.deepEqual(snapshot(folder), before);
});

test('report joins worktree history and uses 14-day recoveries and last 20 actual executions', t => {
  const f = fixture(t);
  const first = records(f, 'first', [
    runRecord({ time: daysAgo(30), results: [execution('old-slow', 500)] }),
    ...Array.from({ length: 20 }, (_, i) => runRecord({
      time: daysAgo(25 - i), results: [execution('old-slow', 1)],
    })),
    runRecord({ time: daysAgo(15), results: [execution('flaky', 1, 600, { recovered: true })] }),
    runRecord({ time: daysAgo(10), results: [execution('flaky', 1, 600, { recovered: true })] }),
  ], [{ type: 'bypass', time: daysAgo(10), reason: 'Earlier reason', hook: 'pre-commit' }]);
  records(f, 'second', [
    runRecord({ results: [execution('flaky', 1, 600, { recovered: true })] }),
    runRecord({ results: [execution('flaky', 999, 600, { recovered: true, reused: true, attempts: [] })] }),
    runRecord({ results: [execution('skipped', 999, 600, { status: 'skipped', attempts: [] })] }),
    runRecord({ results: [execution('blocked', 999, 600, { status: 'blocked', attempts: [] })] }),
    ...Array.from({ length: 20 }, (_, i) => runRecord({ results: [execution('rank', i < 18 ? 5 : 9, 10)] })),
    runRecord({ results: [execution('above', 5.01, 10)] }),
  ], [{ type: 'bypass', time: daysAgo(1), reason: 'Latest reason', hook: 'pre-push' }]);
  const legacy = runRecord({ results: [execution('legacy', 301)] });
  delete legacy.time;
  delete legacy.results[0].timeout_s;
  const legacyPath = join(first, 'records/legacy.json');
  writeFileSync(legacyPath, JSON.stringify(legacy));
  const yesterday = new Date(daysAgo(1));
  utimesSync(legacyPath, yesterday, yesterday);
  const facts = json(f, ['report']);
  assert.equal(facts.runs.total, 49);
  assert.equal(facts.bypasses.count, 2);
  assert.equal(facts.bypasses.latest_reason, 'Latest reason');
  assert.equal(facts.retry_recoveries, 2);
  assert.deepEqual(facts.flaky, [{ id: 'flaky', recoveries: 2 }]);
  assert.deepEqual(facts.slow, [
    { id: 'above', samples: 1, p90_s: 5.01, timeout_s: 10 },
    { id: 'legacy', samples: 1, p90_s: 301, timeout_s: 600 },
  ]);
  assert.match(f.cli('report').stdout, /FLAKY flaky 2 recoveries in 14 days \(threshold 2\)/);
});

test('report lists only clean matching-head successful pushes, deduplicated across worktrees', t => {
  const f = fixture(t);
  const head = f.git('rev-parse', 'HEAD');
  const other = 'a'.repeat(40);
  const valid = runRecord({
    mode: 'push', identity: { head, dirty: false }, identity_after: { head, dirty: false },
    push: { dirty: false, ranges: [{ head }] },
  });
  records(f, 'main', [
    valid, { ...valid, exit_code: 1, ok: false },
    { ...valid, push: { ...valid.push, dirty: true } },
    { ...valid, identity: { head, dirty: true } },
    { ...valid, identity_after: { head, dirty: true } },
    { ...valid, identity_after: { head: other, dirty: false } },
    { ...valid, push: { dirty: false, ranges: [{ head: other }] } },
    { ...valid, mode: 'run', identity: { head: other, dirty: false } },
  ]);
  records(f, 'linked', [valid]);
  assert.deepEqual(json(f, ['report']).passed_push_commits, [head]);
  const linked = join(f.root, 'linked');
  f.git('worktree', 'add', '-b', 'linked', linked, 'HEAD');
  assert.deepEqual(json(f, ['report'], 0, { cwd: linked }).passed_push_commits, [head]);
});

test('real saved executions include effective timeouts and feed report across linked worktrees', t => {
  const f = fixture(t);
  const c = cleanConfig();
  c.checks[0].run = command('console.log("executed")');
  c.checks[0].timeout_s = 17;
  f.config(c);
  f.commit();
  const base = f.git('rev-parse', 'HEAD');
  f.write('src/new.js', 'change\n');
  f.commit();
  const run = json(f, ['--base', base]);
  assert.equal(run.results[0].timeout_s, 17);
  assert.equal(JSON.parse(readFileSync(run.storage.record)).results[0].timeout_s, 17);
  const head = f.git('rev-parse', 'HEAD');
  const push = json(f, ['--push'], 0, { input: `refs/heads/main ${head} refs/heads/main ${base}\n` });
  assert.equal(push.results[0].reused, true);
  const linked = join(f.root, 'linked');
  f.git('worktree', 'add', '-b', 'linked', linked, 'HEAD');
  const other = json(f, ['--base', base], 0, { cwd: linked });
  assert.notEqual(other.storage.worktree_dir, run.storage.worktree_dir);
  const facts = json(f, ['report'], 0, { cwd: linked });
  assert.deepEqual(facts.runs, { total: 3, passed: 3, failed: 0, blocked: 0, internal_error: 0 });
  assert.deepEqual(facts.passed_push_commits, [head]);
});

test('range replay uses committed range and current config, with no network, preparation, checks or history writes', t => {
  const { f, c } = setup(t);
  const base = f.git('rev-parse', 'HEAD');
  f.write('src/unit/new.js', 'change\n');
  f.commit();
  const head = f.git('rev-parse', 'HEAD');
  f.write('src/build/dirty.js', 'ignored worktree edit\n');
  f.env.MMW_CHECKS_SKIP = 'Replay is not a bypass';
  const gh = join(f.home, 'gh');
  writeFileSync(gh, '#!/bin/sh\necho "gh must not run" >&2\nexit 99\n');
  chmodSync(gh, 0o755);
  const upload = join(f.home, 'upload');
  writeFileSync(upload, '#!/bin/sh\ntouch "$HOME/FETCH_RAN"\nexit 99\n');
  chmodSync(upload, 0o755);
  f.git('config', 'remote.origin.uploadpack', upload);
  let result = f.cli('replay', '--range', `${base}..${head}`);
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.equal(result.stdout, 'SELECT unit inputs src/unit/new.js\nSUMMARY 1 selected (replay; no checks run)\n');
  c.checks[0].inputs = [];
  c.checks[1].inputs.push('src/unit/**');
  f.config(c);
  result = f.cli('replay', '--range', `${base}..${head}`);
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.match(result.stdout, /^SELECT build inputs src\/unit\/new.js$/m);
  assert.doesNotMatch(result.stdout, /PASS|SKIP|DIRTY|SELECT unit/);
  for (const path of ['CHECK_RAN', 'PREPARE_RAN', '.git/repo-checks']) assert.equal(existsSync(join(f.repo, path)), false, path);
  assert.equal(existsSync(join(f.home, 'FETCH_RAN')), false);
});

test('range replay preserves inert, unclassified, widen and rename selection behavior', t => {
  const { f } = setup(t);
  f.write('src/unit/old.js', 'preserved\n');
  f.commit();
  const base = f.git('rev-parse', 'HEAD');
  f.write('README.md', 'inert\n');
  f.commit();
  assert.equal(f.cli('replay', '--range', `${base}..HEAD`).stdout, 'SUMMARY nothing selected\n');
  const inert = f.git('rev-parse', 'HEAD');
  f.write('src/build/seed.js', 'seed\n');
  f.git('mv', 'src/unit/old.js', 'src/build/new.js');
  f.commit();
  const rename = f.cli('replay', '--range', `${inert}..HEAD`);
  assert.equal(rename.status, 0, rename.stderr);
  assert.match(rename.stdout, /^SELECT unit inputs src\/unit\/old.js$/m);
  assert.match(rename.stdout, /^SELECT build inputs src\/build\/new.js$/m);
  const beforeUnknown = f.git('rev-parse', 'HEAD');
  f.write('unknown.txt', 'unclassified\n');
  f.commit();
  const widened = f.cli('replay', '--range', `${beforeUnknown}..HEAD`);
  assert.equal(widened.status, 0, widened.stderr);
  assert.match(widened.stdout, /^UNCLASSIFIED unknown.txt$/m);
  assert.match(widened.stdout, /^WIDEN UNCLASSIFIED unknown.txt$/m);
  assert.equal((widened.stdout.match(/^SELECT /gm) ?? []).length, 2);
});

test('range replay runs source selection but not the selected test command', t => {
  const { f, c } = setup(t);
  Object.assign(c.checks[0], {
    inputs: [], sources: ['src/unit/**'], tests: ['test/**'],
    select: command('console.log(JSON.stringify(["test/unit.test.mjs"]))'),
  });
  f.config(c);
  f.commit();
  const base = f.git('rev-parse', 'HEAD');
  f.write('src/unit/new.js', 'source\n');
  f.commit();
  const result = f.cli('replay', '--range', `${base}..HEAD`);
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.equal(result.stdout, 'SELECT unit sources src/unit/new.js\nSUMMARY 1 selected (replay; no checks run)\n');
  assert.equal(existsSync(join(f.repo, 'CHECK_RAN')), false);
  assert.equal(existsSync(join(f.repo, '.git/repo-checks')), false);
});

for (const kind of ['squash', 'merge', 'rebase']) test(`PR replay selects the full ${kind} PR files, not the advanced integration tip`, t => {
  const { f } = setup(t);
  f.write('src/unit/old.js', 'rename contents\n');
  f.commit();
  f.git('push', 'origin', 'main');
  f.git('switch', '-c', 'topic');
  f.write('src/unit/pr.js', 'PR input\n');
  f.commit('First PR commit');
  mkdirSync(join(f.repo, 'src/build'), { recursive: true });
  f.git('mv', 'src/unit/old.js', 'src/build/renamed.js');
  f.commit('Last PR commit');
  f.git('switch', 'main');
  if (kind === 'squash') {
    f.git('merge', '--squash', 'topic');
    f.git('commit', '-m', 'Squash topic');
  } else if (kind === 'merge') f.git('merge', '--no-ff', 'topic', '-m', 'Merge topic');
  else {
    f.write('README.md', 'advance before rebase\n');
    f.commit();
    f.git('switch', 'topic');
    f.git('rebase', 'main');
    f.git('switch', 'main');
    f.git('merge', '--ff-only', 'topic');
  }
  f.write('integration-only.txt', 'later integration change must not widen\n');
  f.commit();
  f.git('push', 'origin', 'main');
  const gh = join(f.home, 'gh');
  const pages = [
    [{ filename: 'src/unit/pr.js', status: 'added' }],
    [{ filename: 'src/build/renamed.js', previous_filename: 'src/unit/old.js', status: 'renamed' }],
  ];
  writeFileSync(gh, `#!/bin/sh
printf '%s\\n' "$*" >> "$HOME/gh-args"
case "$*" in
  'pr view 42 --json state') printf '%s\\n' '{"state":"MERGED"}' ;;
  'api --paginate --slurp repos/{owner}/{repo}/pulls/42/files') printf '%s\\n' '${JSON.stringify(pages)}' ;;
  *) echo "Unexpected gh command: $*" >&2; exit 99 ;;
esac
`);
  chmodSync(gh, 0o755);
  const result = f.cli('replay', '42');
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.equal(readFileSync(join(f.home, 'gh-args'), 'utf8'),
    'pr view 42 --json state\napi --paginate --slurp repos/{owner}/{repo}/pulls/42/files\n');
  assert.equal(result.stdout, 'SELECT unit inputs src/unit/old.js\nSELECT build inputs src/build/renamed.js\nSUMMARY 2 selected (replay; no checks run)\n');
  for (const path of ['CHECK_RAN', 'PREPARE_RAN', '.git/repo-checks']) {
    assert.equal(existsSync(join(f.repo, path)), false);
  }
  const c = cleanConfig();
  c.inert.push('src/unit/old.js', 'src/build/renamed.js');
  c.checks[0].inputs = ['src/unit/pr.js'];
  f.config(c);
  assert.match(f.cli('replay', '42').stdout, /^SELECT unit inputs src\/unit\/pr.js$/m);
});

test('replay rejects invalid ranges, unmerged PRs and invalid current config with request exit 2', t => {
  const { f } = setup(t);
  for (const args of [[], ['--range'], ['--range', 'HEAD...HEAD'], ['--range', 'HEAD..'], ['--range', 'missing..HEAD'], ['0'], ['--all']]) {
    const result = f.cli('replay', ...args);
    assert.equal(result.status, 2, JSON.stringify(args) + result.stdout + result.stderr);
    assert.match(result.stdout, /USAGE|REQUEST/);
    assert.doesNotMatch(result.stdout, /SUMMARY/);
  }
  const gh = join(f.home, 'gh');
  writeFileSync(gh, '#!/bin/sh\nprintf \'%s\\n\' \'{"state":"OPEN","mergeCommit":null}\'\n');
  chmodSync(gh, 0o755);
  let result = f.cli('replay', '42');
  assert.equal(result.status, 2, result.stdout + result.stderr);
  assert.match(result.stdout, /PR 42 is not merged/);
  f.write('.agents/checks.json', 'bad JSON');
  result = f.cli('replay', '--range', 'HEAD..HEAD');
  assert.equal(result.status, 2, result.stdout + result.stderr);
  assert.match(result.stdout, /checks.json/);
});

test('selftest runs the installed engine through its canonical entry outside git and cleans its own fixture', t => {
  const f = fixture(t);
  const temp = join(f.root, 'selftest-temp');
  mkdirSync(temp);
  f.env.TMPDIR = temp;
  f.env.MMW_CHECKS_SKIP = 'Selftest still must test';
  const facts = json(f, ['selftest'], 0, { cwd: f.home });
  assert.equal(facts.mode, 'selftest');
  assert.deepEqual(facts.assertions, ['fixture', 'engine-run', 'selection', 'check-pass', 'check-log'].map(name => ({ name, ok: true })));
  assert.deepEqual(facts.findings, []);
  assert.deepEqual(readdirSync(temp), []);
  const text = f.invoke(['selftest'], { cwd: f.home });
  assert.equal(text.status, 0, text.stdout + text.stderr);
  assert.match(text.stdout, /^SELFTEST PASS selection$/m);
  assert.match(text.stdout, /^SELFTEST PASS check-log$/m);
  assert.deepEqual(readdirSync(temp), []);
  assert.equal(existsSync(join(f.repo, '.git/repo-checks')), false);
});

test('selftest names a failed selection assertion on a mutated engine with no test fixtures installed', t => {
  const f = fixture(t);
  const scripts = join(f.home, 'installed/scripts');
  const templates = join(f.home, 'installed/templates');
  mkdirSync(scripts, { recursive: true });
  mkdirSync(templates);
  const original = readFileSync(engine, 'utf8');
  const broken = original.replace('const path = facts.changed_paths.find(match);', 'const path = undefined;');
  assert.notEqual(broken, original);
  const copy = join(scripts, 'check.mjs');
  writeFileSync(copy, broken);
  copyFileSync(new URL('../checks.schema.json', import.meta.url), join(scripts, 'checks.schema.json'));
  copyFileSync(new URL('../../templates/check', import.meta.url), join(templates, 'check'));
  f.env.MMW_REPO_CHECKS_ENGINE = copy;
  const facts = json(f, ['selftest'], 1, { cwd: f.home });
  assert.equal(facts.mode, 'selftest');
  assert.equal(facts.assertions.find(item => item.name === 'selection').ok, false);
  assert.match(facts.assertions.find(item => item.name === 'selection').message, /Expected only unit; selected/);
  const text = f.cli('selftest');
  assert.equal(text.status, 1, text.stdout + text.stderr);
  assert.match(text.stdout, /SELFTEST FAIL selection/);
});

test('selftest succeeds with no user Git configuration and creates none', t => {
  const f = fixture(t);
  f.env.GIT_CONFIG_GLOBAL = join(f.home, 'absent.gitconfig');
  f.env.GIT_CONFIG_NOSYSTEM = '1';
  const facts = json(f, ['selftest'], 0, { cwd: f.home });
  assert.equal(facts.ok, true);
  assert.equal(existsSync(f.env.GIT_CONFIG_GLOBAL), false);
});

test('new modes reject extra options as mode-specific JSON facts, and report errors do not assume events', t => {
  const f = fixture(t);
  for (const mode of ['report', 'selftest']) {
    for (const arg of ['--all', '--check', 'extra']) {
      const facts = json(f, [mode, arg], 2);
      assert.equal(facts.mode, mode);
      assert.equal(facts.findings[0].rule, 'usage');
    }
  }
  const replay = json(f, ['replay', '--range', 'HEAD..HEAD'], 2);
  assert.equal(replay.mode, 'replay');
  assert.equal(replay.events[0].rule, 'usage');
  const outside = json(f, ['report'], 70, { cwd: f.home });
  assert.equal(outside.mode, 'report');
  assert.equal(outside.findings[0].rule, 'engine');
});
