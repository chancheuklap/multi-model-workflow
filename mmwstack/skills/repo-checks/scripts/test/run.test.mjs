import assert from 'node:assert/strict';
import test from 'node:test';
import { chmodSync, existsSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { cleanConfig, fixture } from './fixture.mjs';

const quote = value => `'${value.replaceAll("'", "'\\''")}'`;
const command = source => `${quote(process.execPath)} -e ${quote(source)}`;

function setup(t, change = () => {}) {
  const f = fixture(t);
  const c = cleanConfig();
  c.checks = ['unit', 'build'].map(id => ({
    id, run: command(`console.log("${id} output")`), inputs: [`src/${id}/**`],
    tests: [`test/${id}/**`], ci: false, ci_reason: 'Local checks are authoritative.',
  }));
  change(c, f);
  f.config(c);
  f.commit('Configure runnable checks');
  f.git('push', 'origin', 'main');
  f.git('switch', '-c', 'feature');
  return { f, c };
}

function runJson(f, args = [], status = 0) {
  const r = f.cli(...args, '--json');
  assert.equal(r.status, status, r.stdout + r.stderr);
  assert.equal(r.stderr, '');
  const facts = JSON.parse(r.stdout);
  assert.equal(facts.mode, 'run');
  assert.equal(facts.exit_code, status);
  assert.equal(facts.ok, status === 0);
  for (const field of ['selection', 'results', 'lanes', 'events']) assert.ok(Array.isArray(facts[field]), field);
  assert.ok(facts.timing.select_ms >= 0);
  return facts;
}

test('default run selects inputs from committed, staged, unstaged and untracked changes', t => {
  const { f } = setup(t, (_, f) => f.write('src/unit/unstaged.js', 'original\n'));
  f.write('src/unit/committed.js', 'one\n');
  f.commit();
  f.write('src/unit/staged.js', 'two\n');
  f.git('add', 'src/unit/staged.js');
  f.write('README.md', 'inert unstaged change\n');
  f.write('src/unit/unstaged.js', 'unstaged source change\n');
  f.write('src/build/untracked.js', 'three\n');
  const facts = runJson(f);
  assert.deepEqual(facts.changed_paths, ['README.md', 'src/build/untracked.js', 'src/unit/committed.js', 'src/unit/staged.js', 'src/unit/unstaged.js']);
  assert.deepEqual(facts.selection.map(x => [x.check.id, x.scope.kind]), [['unit', 'whole'], ['build', 'whole']]);
  assert.deepEqual(facts.results.map(x => [x.id, x.status]), [['unit', 'passed'], ['build', 'passed']]);
  assert.deepEqual(facts.summary, { selected: 2, passed: 2, failed: 0, skipped: 0, blocked: 0, 'internal-error': 0 });
  const text = f.cli();
  assert.equal(text.status, 0, text.stdout + text.stderr);
  assert.deepEqual(text.stdout.match(/^SELECT \S+/gm), ['SELECT unit', 'SELECT build']);
  assert.match(text.stdout, /SELECT unit inputs src\/unit\/committed.js/);
  assert.match(text.stdout, /PASS unit [\d.]+s/);
  assert.match(text.stdout, /SUMMARY 2 selected, 2 passed, 0 failed, 0 skipped\n$/);
  for (const result of facts.results) assert.match(readFileSync(result.log, 'utf8'), new RegExp(`${result.id} output`));
});

test('inert changes select nothing while affects_all widens every check', t => {
  const { f } = setup(t, c => c.affects_all.push('package-lock.json'));
  f.write('README.md', 'inert change\n');
  let facts = runJson(f);
  assert.deepEqual(facts.selection, []);
  assert.equal(f.cli().stdout, 'SUMMARY nothing selected\n');
  f.write('package-lock.json', '{}\n');
  facts = runJson(f);
  assert.deepEqual(facts.selection.map(x => x.check.id), ['unit', 'build']);
  assert.ok(facts.selection.every(x => x.scope.kind === 'whole'));
  assert.match(f.cli().stdout, /^WIDEN affects_all package-lock.json$/m);
});

test('UNCLASSIFIED reports its path and widens every check', t => {
  const { f } = setup(t);
  f.write('unknown path\nname.txt', 'new unknown input\n');
  const facts = runJson(f);
  assert.deepEqual(facts.selection.map(x => x.check.id), ['unit', 'build']);
  assert.ok(facts.events.some(x => x.type === 'UNCLASSIFIED' && x.path === 'unknown path\nname.txt'));
  assert.ok(facts.events.some(x => x.type === 'WIDEN' && x.path === 'unknown path\nname.txt'));
  assert.match(f.cli().stdout, /UNCLASSIFIED unknown path\nname.txt/);
});

test('--only intersects selection and --all forces whole scope without widening', t => {
  const { f } = setup(t);
  f.write('src/unit/a.js', 'changed\n');
  assert.deepEqual(runJson(f, ['--only', 'build']).selection, []);
  let facts = runJson(f, ['--only', 'unit']);
  assert.deepEqual(facts.selection.map(x => x.check.id), ['unit']);
  facts = runJson(f, ['--all', '--only', 'build']);
  assert.deepEqual(facts.selection.map(x => [x.check.id, x.scope.kind, x.reason]), [['build', 'whole', '--all']]);
  assert.equal(facts.events.some(x => x.type === 'WIDEN'), false);
  facts = runJson(f, ['--only', 'unit,build', '--all']);
  assert.deepEqual(facts.selection.map(x => x.check.id), ['unit', 'build']);
  for (const args of [['--only', 'typo'], ['--only', ''], ['--only'], ['--base'], ['--all', '--typo']]) {
    assert.ok(runJson(f, args, 2).events.some(x => x.type === 'ERROR'));
  }
});

test('sources selector narrows tests and safely quotes source and test filenames', t => {
  const source = "src/unit/space ' ;$(touch PWNED); \nfile.js";
  const target = "test/unit/space ' ;$(touch PWNED); \nfile.test.mjs";
  const { f } = setup(t, (c, repo) => {
    Object.assign(c.checks[0], {
      inputs: ['settings/**'], sources: ['src/unit/**'],
      select: `${command('console.log(JSON.stringify(process.argv.slice(1).map(x => x.replace("src/", "test/").replace(/\\.js$/, ".test.mjs"))))')} -- {files}`,
      run: `${command('console.log(JSON.stringify(process.argv.slice(1)))')} -- {files} {tests}`,
      run_all: command('console.log("whole suite")'),
    });
    repo.write(target, 'test fixture\n');
  });
  f.write(source, 'changed\n');
  const facts = runJson(f, ['--only', 'unit']);
  assert.deepEqual(facts.selection.map(x => x.check.id), ['unit']);
  assert.deepEqual(facts.selection[0].scope, { kind: 'narrowed', files: [source], tests: [target] });
  assert.deepEqual(JSON.parse(readFileSync(facts.results[0].log, 'utf8')), [source, target]);
  assert.equal(f.git('ls-files', '--others', '--exclude-standard', '-z'), `${source}\0`);
  assert.deepEqual(runJson(f, ['--only', 'build']).selection, []);
  const all = runJson(f, ['--only', 'unit', '--all']);
  assert.equal(all.selection[0].scope.kind, 'whole');
  assert.equal(readFileSync(all.results[0].log, 'utf8'), 'whole suite\n');
});

test('an empty selector selects nothing and inputs dominate narrowing', t => {
  const { f } = setup(t, c => Object.assign(c.checks[0], {
    inputs: ['settings/**'], sources: ['src/unit/**'],
    select: command('console.log("[]")'),
    run: `${command('console.log("narrow")')} {tests}`,
    run_all: command('console.log("whole")'),
  }));
  f.write('src/unit/a.js', 'changed source\n');
  assert.deepEqual(runJson(f).selection, []);
  f.write('settings/a.json', '{}\n');
  const facts = runJson(f);
  assert.equal(facts.selection[0].scope.kind, 'whole');
  assert.match(facts.selection[0].reason, /^inputs settings\/a.json$/);
  assert.equal(readFileSync(facts.results[0].log, 'utf8'), 'whole\n');
});

test('selector failures and invalid test lists exit 2 instead of false green', async t => {
  for (const [name, source] of [
    ['nonzero', 'console.error("selector broke"); process.exit(3)'],
    ['invalid JSON', 'console.log("not JSON")'],
    ['object', 'console.log("{}")'],
    ['non-string entry', 'console.log("[4]")'],
    ['NUL path', 'console.log(JSON.stringify(["test/unit/a\\0.test.mjs"]))'],
    ['absolute path', 'console.log(JSON.stringify(["/tmp/outside.test.mjs"]))'],
    ['parent traversal', 'console.log(JSON.stringify(["test/unit/../../../outside.test.mjs"]))'],
    ['foreign tests', 'console.log(JSON.stringify(["test/build/foreign.test.mjs"]))'],
  ]) {
    await t.test(name, () => {
      const { f } = setup(t, c => Object.assign(c.checks[0], {
        inputs: [], sources: ['src/unit/**'], select: command(source),
      }));
      f.write('src/unit/a.js', 'changed\n');
      const facts = runJson(f, [], 2);
      assert.equal(facts.results.length, 0);
      assert.ok(facts.events.some(x => x.type === 'ERROR' && /selector.*unit|unit.*selector/i.test(x.message)));
    });
  }
});

test('needs skip gate-covered checks and uncovered skips exit 2 with ci_reason', async t => {
  const otherOS = process.platform === 'darwin' ? 'linux' : 'darwin';
  for (const need of ['cmd:repo-checks-command-that-does-not-exist', `os:${otherOS}`, 'env:REPO_CHECKS_MISSING', 'path:missing-folder']) {
    await t.test(need, () => {
      const { f } = setup(t, c => {
        c.ci_workflow = 'gate.yml';
        Object.assign(c.checks[0], { needs: [need], ci: true, ci_run: 'node gate.mjs' });
      });
      delete f.env.REPO_CHECKS_MISSING;
      let facts = runJson(f, ['--all']);
      assert.deepEqual(facts.results.map(x => [x.id, x.status]), [['unit', 'skipped'], ['build', 'passed']]);
      assert.equal(facts.summary.skipped, 1);
      assert.equal(facts.summary.passed, 1);
      assert.match(f.cli('--all').stdout, new RegExp(`SKIP unit needs ${need.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')} \\(gate runs it\\)`));
      const config = JSON.parse(readFileSync(join(f.repo, '.agents/checks.json')));
      config.checks[0].ci = false;
      config.checks[1].run = command('console.error("real failure"); process.exit(1)');
      f.config(config);
      facts = runJson(f, ['--all'], 2);
      assert.equal(facts.results[0].ci_reason, 'Local checks are authoritative.');
      assert.equal(facts.summary.skipped, 1);
      assert.equal(facts.summary.failed, 1);
      assert.doesNotMatch(f.cli('--all').stdout, /\(gate runs it\)/);
    });
  }
});

test('satisfied command, OS, set environment and existing path needs permit execution', t => {
  const os = process.platform === 'win32' ? 'windows' : process.platform;
  const { f } = setup(t, c => {
    c.checks[0].needs = ['cmd:node', `os:${os}`, 'env:REPO_CHECKS_PRESENT', 'path:README.md'];
  });
  f.env.REPO_CHECKS_PRESENT = '';
  const facts = runJson(f, ['--all']);
  assert.deepEqual(facts.results.map(x => x.status), ['passed', 'passed']);
});

test('docker needs probe a reachable daemon, not merely the installed executable', t => {
  const version = spawnSync('docker', ['--version'], { encoding: 'utf8' });
  if (version.error?.code === 'ENOENT') return t.skip('Docker executable is not installed on this host.');
  assert.equal(version.status, 0, version.stderr);
  const { f } = setup(t, c => {
    c.ci_workflow = 'gate.yml';
    Object.assign(c.checks[0], { needs: ['docker'], ci: true, ci_run: 'node gate.mjs' });
  });
  f.env.DOCKER_HOST = `unix://${join(f.root, 'no-docker.sock')}`;
  delete f.env.DOCKER_CONTEXT;
  const facts = runJson(f, ['--all']);
  assert.equal(facts.results[0].status, 'skipped');
  assert.equal(facts.results[0].reason, 'needs docker');
  assert.equal(facts.summary.skipped, 1);
  assert.match(f.cli('--all').stdout, /^SKIP unit needs docker \(gate runs it\)$/m);
});

test('lanes are reported as not run here with their reason and runner, never executed', t => {
  const { f, c } = setup(t, c => {
    c.lanes = ['ci-only', 'device', 'owner-only'].map(kind => ({
      id: kind, kind, reason: `Requires ${kind} access`, run_by: 'owner',
      tests: [`lane/${kind}/**`], command: 'touch LANE_RAN',
    }));
  });
  const facts = runJson(f, ['--all']);
  assert.deepEqual(facts.lanes, c.lanes);
  const text = f.cli('--all');
  assert.equal(text.status, 0);
  for (const lane of c.lanes) {
    assert.ok(text.stdout.includes(`not run here ${lane.id}`));
    assert.ok(text.stdout.includes(lane.reason));
    assert.ok(text.stdout.includes(lane.run_by));
  }
  assert.equal(existsSync(join(f.repo, 'LANE_RAN')), false);
  assert.match(text.stdout, /SUMMARY .* skipped\n$/);
});

test('unreachable remote falls back visibly and --base overrides without fetching', t => {
  const { f } = setup(t);
  f.write('src/unit/a.js', 'committed\n');
  f.commit();
  const before = runJson(f);
  assert.deepEqual(before.selection.map(x => x.check.id), ['unit']);
  f.git('remote', 'set-url', 'origin', join(f.root, 'absent.git'));
  const fallback = runJson(f);
  assert.deepEqual(fallback.selection, before.selection);
  assert.ok(fallback.events.some(x => x.type === 'BASE' && x.fallback === true && /local.*origin\/main/.test(x.reason)));
  assert.match(f.cli().stdout, /fetch failed; using local refs\/remotes\/origin\/main/);
  const override = runJson(f, ['--base', 'HEAD']);
  assert.deepEqual(override.selection, []);
  assert.equal(override.base.ref, 'HEAD');
  assert.equal(override.events.some(x => x.type === 'BASE' && x.fallback), false);
  assert.ok(runJson(f, ['--base', 'missing-base'], 2).events.some(x => x.type === 'ERROR'));
  f.env.MMW_BASE_REF = 'HEAD';
  assert.deepEqual(runJson(f).selection, before.selection);
  f.git('update-ref', '-d', 'refs/remotes/origin/main');
  assert.deepEqual(runJson(f, ['--base', 'HEAD']).selection, []);
  runJson(f, [], 2);
});

test('fetch timeout bounds the wait, reaps its subprocesses and uses the local ref', t => {
  if (process.platform === 'win32') return t.skip('The forwarding entry fixture requires a POSIX shell.');
  const { f } = setup(t);
  const uploadpack = join(f.home, 'slow-uploadpack');
  const pidfile = join(f.home, 'uploadpack.pid');
  writeFileSync(uploadpack, `#!${process.execPath}\nrequire('node:fs').writeFileSync(${JSON.stringify(pidfile)}, String(process.pid)); setTimeout(() => {}, 10000);\n`);
  chmodSync(uploadpack, 0o755);
  t.after(() => {
    if (existsSync(pidfile)) {
      try { process.kill(Number(readFileSync(pidfile)), 'SIGKILL'); }
      catch (error) { if (error.code !== 'ESRCH') throw error; }
    }
  });
  f.git('config', 'remote.origin.uploadpack', quote(uploadpack));
  const start = performance.now();
  const facts = runJson(f);
  const elapsed = performance.now() - start;
  assert.ok(facts.events.some(x => x.type === 'BASE' && x.fallback));
  assert.ok(facts.timing.fetch_ms >= 2000);
  assert.ok(elapsed <= 5000, `Fetch fallback took ${elapsed}ms`);
  assert.ok(facts.timing.select_ms + facts.timing.fetch_ms <= elapsed);
  const pid = Number(readFileSync(pidfile));
  assert.throws(() => process.kill(pid, 0), { code: 'ESRCH' }, 'Timed-out upload-pack must not survive the engine.');
});

test('fetch updates only the integration destination despite a broad or different refspec', t => {
  const { f } = setup(t);
  f.write('src/unit/a.js', 'committed\n');
  f.commit();
  const head = f.git('rev-parse', 'HEAD');
  f.git('push', 'origin', 'HEAD:refs/heads/shipping');
  f.git('--git-dir', join(f.root, 'origin.git'), 'update-ref', 'refs/heads/main', head);
  f.git('--git-dir', join(f.root, 'origin.git'), 'update-ref', 'refs/heads/unwanted', head);
  f.git('--git-dir', join(f.root, 'origin.git'), 'update-ref', 'refs/tags/unwanted', head);
  f.git('config', 'remote.origin.fetch', '+refs/heads/*:refs/remotes/elsewhere/*');
  const facts = runJson(f);
  assert.equal(f.git('rev-parse', 'refs/remotes/origin/main'), head);
  assert.equal(f.git('for-each-ref', '--format=%(refname)', 'refs/remotes/elsewhere/'), '');
  assert.equal(f.git('for-each-ref', '--format=%(refname)', 'refs/remotes/origin/unwanted'), '');
  assert.equal(f.git('for-each-ref', '--format=%(refname)', 'refs/tags/unwanted'), '');
  assert.deepEqual(facts.selection, []);
});

test('renames keep old and new names across committed, staged and unstaged changes', t => {
  const old = "src/unit/old '\nfile.js";
  const middle = "src/build/middle '\nfile.js";
  const final = "src/third/final '\nfile.js";
  const { f } = setup(t, (c, f) => {
    c.checks.push({ ...c.checks[0], id: 'third', inputs: ['src/third/**'] });
    f.write(old, 'preserved content\n');
    f.write('src/build/seed.js', 'build seed\n');
    f.write('src/third/seed.js', 'third seed\n');
  });
  f.git('mv', old, middle);
  renameSync(join(f.repo, middle), join(f.repo, final));
  let facts = runJson(f);
  assert.deepEqual(facts.selection.map(x => x.check.id), ['unit', 'build', 'third']);
  assert.ok(facts.changed_paths.includes(old));
  assert.ok(facts.changed_paths.includes(middle));
  assert.ok(facts.changed_paths.includes(final));
  f.commit('Commit rename chain');
  facts = runJson(f);
  assert.deepEqual(facts.selection.map(x => x.check.id), ['unit', 'third']);
  assert.ok(facts.changed_paths.includes(old));
  assert.ok(facts.changed_paths.includes(final));
});

test('selector subprocess waits are excluded from timing.select_ms', t => {
  const { f } = setup(t, c => Object.assign(c.checks[0], {
    inputs: [], sources: ['src/unit/**'],
    select: command('setTimeout(() => console.log(JSON.stringify(["test/unit/a.test.mjs"])), 400)'),
  }));
  f.write('src/unit/a.js', 'changed\n');
  const start = performance.now();
  const facts = runJson(f);
  const elapsed = performance.now() - start;
  assert.deepEqual(facts.selection.map(x => x.check.id), ['unit']);
  assert.ok(facts.timing.selector_ms >= 400);
  assert.ok(facts.timing.select_ms + facts.timing.selector_ms <= elapsed);
});

test('failure output includes the saved log and exactly its last 40 lines while other checks still run', t => {
  const { f } = setup(t, c => {
    c.checks[0].run = command('for (let i=0;i<55;i++) console.log(`output ${i}`); console.error("last stderr"); process.exit(9)');
  });
  const facts = runJson(f, ['--all'], 1);
  assert.deepEqual(facts.results.map(x => [x.id, x.status]), [['unit', 'failed'], ['build', 'passed']]);
  const failure = facts.results[0];
  assert.deepEqual(failure.tail, [...Array.from({ length: 39 }, (_, i) => `output ${i + 16}`), 'last stderr']);
  assert.equal(failure.attempts[0].exit_code, 9);
  assert.equal(readFileSync(failure.log, 'utf8').split('\n').filter(Boolean).length, 56);
  const text = f.cli('--all');
  assert.equal(text.status, 1);
  const lines = text.stdout.trimEnd().split('\n');
  const at = lines.findIndex(x => /^FAIL unit [\d.]+s log=/.test(x));
  assert.ok(at >= 0, text.stdout);
  assert.deepEqual(lines.slice(at + 1, at + 41), failure.tail);
  const build = lines.findIndex(x => /^PASS build /.test(x));
  assert.ok(build >= 0 && (build < at || build > at + 40), text.stdout);
  assert.equal(lines.filter(x => /^PASS build /.test(x)).length, 1);
  assert.equal(lines.at(-1), 'SUMMARY 2 selected, 1 passed, 1 failed, 0 skipped');
});

test('run records carry request, HEAD, tree, config, source version and results under the git common directory', t => {
  const { f } = setup(t);
  const facts = runJson(f, ['--all', '--only', 'unit']);
  const saved = JSON.parse(readFileSync(facts.storage.record, 'utf8'));
  assert.deepEqual(saved, facts);
  assert.equal(saved.record_version, 1);
  assert.deepEqual(saved.request, { scope: 'all', only: ['unit'], base: null });
  assert.equal(saved.identity.head, f.git('rev-parse', 'HEAD'));
  assert.equal(saved.identity.tree, f.git('rev-parse', 'HEAD^{tree}'));
  assert.match(saved.identity.config_hash, /^[a-f0-9]{64}$/);
  assert.match(saved.identity.engine_hash, /^[a-f0-9]{64}$/);
  assert.equal(saved.identity.engine_version, saved.identity.engine_hash);
  assert.equal(saved.identity.dirty, false);
  assert.ok(saved.storage.record.includes('/.git/repo-checks/'));
  assert.equal(f.git('status', '--porcelain'), '');
  const linked = join(f.root, 'linked');
  f.git('worktree', 'add', '-b', 'linked-check', linked, 'HEAD');
  const result = spawnSync(join(linked, 'scripts/check'), ['--all', '--json'], {
    cwd: linked, env: f.env, encoding: 'utf8', timeout: 15_000,
  });
  assert.equal(result.status, 0, result.stdout + result.stderr);
  const other = JSON.parse(result.stdout);
  assert.notEqual(other.storage.worktree_dir, facts.storage.worktree_dir);
  assert.ok(other.storage.worktree_dir.startsWith(facts.storage.worktree_dir.split('/repo-checks/')[0] + '/repo-checks/'));
  assert.deepEqual(JSON.parse(readFileSync(other.storage.record)), other);
  assert.equal(f.git('-C', linked, 'status', '--porcelain'), '');
});

test('a real run-storage obstruction reports engine exit 70, never a check failure', t => {
  const { f } = setup(t);
  writeFileSync(join(f.repo, '.git/repo-checks'), 'A file obstructs the storage directory.\n');
  const facts = runJson(f, ['--all'], 70);
  assert.equal(facts.results.length, 0);
  assert.ok(facts.events.some(x => x.type === 'ERROR' && x.rule === 'engine' && /ENOTDIR|EEXIST/.test(x.message)));
  assert.equal(facts.events.some(x => x.type === 'FAIL'), false);
  assert.equal(f.cli('--all').status, 70);
});

test('invalid run configuration exits 2 before executing a check or protected lane command', t => {
  const { f, c } = setup(t);
  for (const invalid of ['{bad JSON', JSON.stringify({ ...c, unknown: true }), JSON.stringify({
    ...c, lanes: [{ id: 'owner', kind: 'owner-only', run_by: 'owner', reason: 'Protected access',
      tests: [], command: c.checks[0].run }],
  })]) {
    f.write('.agents/checks.json', invalid);
    const facts = runJson(f, ['--all'], 2);
    assert.deepEqual(facts.results, []);
    assert.ok(facts.events.some(x => x.type === 'ERROR'));
  }
});
