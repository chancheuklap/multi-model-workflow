import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { chmodSync, copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, symlinkSync, unlinkSync } from 'node:fs';
import { join, resolve } from 'node:path';
import test from 'node:test';
import { cleanConfig, fixture, lintJson } from './fixture.mjs';

const quote = value => `'${value.replaceAll("'", "'\\''")}'`;
const command = source => `${quote(process.execPath)} -e ${quote(source)}`;
const output = result => result.stdout + result.stderr;
const zero = '0'.repeat(40);
function realGit(f, ...args) {
  const result = spawnSync('git', args, { cwd: f.repo, env: f.env, encoding: 'utf8', timeout: 15_000 });
  assert.ifError(result.error);
  return result;
}
function enableHooks(f) { f.git('config', 'core.hooksPath', '.githooks'); }
function setup(t) {
  const f = fixture(t);
  const c = cleanConfig();
  c.checks = ['unit', 'build'].map(id => ({
    ...c.checks[0], id, inputs: [`src/${id}/**`],
    run: command(`console.log("${id} checked")`),
  }));
  f.config(c);
  f.commit('Configure push checks');
  f.git('push', 'origin', 'main');
  f.git('switch', '-c', 'feature');
  return { f, c };
}
function line(f, ref = 'feature', head = f.git('rev-parse', 'HEAD'), old = zero) {
  return `refs/heads/${ref} ${head} refs/heads/${ref} ${old}\n`;
}
function push(f, input = line(f), json = true) {
  const result = f.invoke(['--push', ...(json ? ['--json'] : [])], { input });
  assert.equal(result.status, 0, output(result));
  return json ? JSON.parse(result.stdout) : result.stdout;
}
function audits(f, repo = f.repo) {
  const common = f.git('-C', repo, 'rev-parse', '--git-common-dir');
  const base = join(resolve(repo, common), 'repo-checks');
  if (!existsSync(base)) return [];
  return readdirSync(base).flatMap(name => {
    const path = join(base, name, 'audit.jsonl');
    return existsSync(path) ? readFileSync(path, 'utf8').trimEnd().split('\n').map(JSON.parse) : [];
  });
}
function prekConfig(f) {
  f.write('.pre-commit-config.yaml', `repos:
  - repo: local
    hooks:
      - id: toy-lint
        name: Toy planted lint
        language: system
        entry: ${JSON.stringify(command('const fs=require("node:fs"); for(const p of process.argv.slice(1)) if(fs.readFileSync(p,"utf8").includes("PLANTED_LINT")){console.error("planted lint error: "+p);process.exit(1)}') + ' --')}
        files: '\\.js$'
`);
}
function requirePrek(t) {
  const result = spawnSync('prek', ['--version'], { encoding: 'utf8' });
  if (result.error?.code === 'ENOENT') {
    t.skip('Install real prek: brew install prek (or uv tool install prek).');
    return false;
  }
  assert.equal(result.status, 0, result.stderr);
  t.diagnostic(result.stdout.trim());
  return true;
}
async function until(predicate, timeout = 5000) {
  const deadline = Date.now() + timeout;
  while (!predicate()) {
    assert.ok(Date.now() < deadline, 'Observable hook condition timed out');
    await new Promise(resolve => setTimeout(resolve, 20));
  }
}

test('a real commit uses real prek and names the failing planted lint hook', t => {
  if (!requirePrek(t)) return;
  const f = fixture(t);
  prekConfig(f);
  f.commit('Add toy prek config');
  enableHooks(f);
  f.write('src/error.js', 'PLANTED_LINT\n');
  f.git('add', 'src/error.js');
  const before = f.git('rev-parse', 'HEAD');
  const denied = realGit(f, 'commit', '-m', 'Must not commit');
  assert.equal(denied.status, 1, output(denied));
  assert.match(output(denied), /toy-lint|Toy planted lint/);
  assert.match(output(denied), /planted lint error/);
  assert.equal(f.git('rev-parse', 'HEAD'), before);
  f.write('src/error.js', 'clean\n');
  f.git('add', 'src/error.js');
  const allowed = realGit(f, 'commit', '-m', 'Clean commit');
  assert.equal(allowed.status, 0, output(allowed));
});

test('a missing prek refuses a real commit and names installation; no config is a no-op', t => {
  const f = fixture(t);
  assert.equal(f.cli('--staged').status, 0);
  unlinkSync(join(f.repo, '.agents/checks.json'));
  assert.equal(f.cli('--staged').status, 0, 'Commit runs do not read Check Config');
  const bin = join(f.home, 'minimal-bin');
  mkdirSync(bin);
  symlinkSync(process.execPath, join(bin, 'node'));
  const gitPath = spawnSync('which', ['git'], { encoding: 'utf8' }).stdout.trim();
  symlinkSync(gitPath, join(bin, 'git'));
  f.env.PATH = bin;
  prekConfig(f);
  f.write('src/error.js', 'PLANTED_LINT\n');
  f.git('add', '--all');
  enableHooks(f);
  const result = realGit(f, 'commit', '-m', 'Missing prek');
  assert.equal(result.status, 1, output(result));
  assert.match(output(result), /Install prek: brew install prek/);
  assert.equal(f.cli('--staged').status, 2);
});

test('push selects committed ranges only, prints DIRTY, and never looks up or writes reusable passes', t => {
  const { f } = setup(t);
  f.write('src/unit/a.js', 'committed\n');
  f.commit();
  assert.equal(f.cli().status, 0);
  assert.match(push(f, line(f), false), /PASS unit [\d.]+s \(reused\)/);
  f.write('src/build/untracked.js', 'untracked must not widen\n');
  f.write('README.md', 'unstaged inert\n');
  f.write('staged-unknown', 'staged must not widen\n');
  f.git('add', 'staged-unknown');
  const facts = push(f);
  assert.deepEqual(facts.changed_paths, ['src/unit/a.js']);
  assert.deepEqual(facts.selection.map(x => x.check.id), ['unit']);
  assert.equal(facts.push.dirty, true);
  assert.equal(facts.reuse_eligible, false);
  assert.equal(facts.results[0].reused, false);
  assert.equal(facts.results[0].reusable, false);
  assert.match(push(f, line(f), false), /^DIRTY$/m);
  assert.deepEqual(facts.push.ranges[0], {
    ref: 'refs/heads/feature', head: f.git('rev-parse', 'HEAD'),
    remote_ref: 'refs/heads/feature', remote_head: zero, base: f.git('rev-parse', 'origin/main'),
  });
  assert.ok(Number.isFinite(Date.parse(facts.time)));
});

test('a push with a non-HEAD tip disables both reuse lookup and reusable proof', t => {
  const { f } = setup(t);
  f.write('src/unit/a.js', 'committed\n');
  f.commit();
  const tip = f.git('rev-parse', 'HEAD');
  f.git('branch', 'pushed-tip', tip);
  f.write('README.md', 'different HEAD\n');
  f.commit();
  assert.equal(f.cli('--all').status, 0);
  const facts = push(f, line(f, 'pushed-tip', tip));
  assert.equal(facts.identity.dirty, false);
  assert.equal(facts.push.dirty, true);
  assert.deepEqual(facts.changed_paths, ['src/unit/a.js']);
  assert.equal(facts.results[0].reused, false);
  assert.equal(facts.results[0].reusable, false);
  assert.equal(facts.reuse_eligible, false);
});

test('a real push is refused for a selected failing check and accepts an inert commit', t => {
  const { f, c } = setup(t);
  c.checks[0].run = command('console.error("planted push failure");process.exit(1)');
  f.config(c);
  f.commit('Configure failure');
  f.git('push', 'origin', 'HEAD:main');
  f.write('src/unit/a.js', 'committed\n');
  f.commit();
  enableHooks(f);
  const denied = realGit(f, 'push', 'origin', 'HEAD:refs/heads/refused');
  assert.notEqual(denied.status, 0, output(denied));
  assert.match(output(denied), /FAIL unit/);
  assert.match(output(denied), /planted push failure/);
  assert.equal(f.git('--git-dir', join(f.root, 'origin.git'), 'for-each-ref', '--format=%(refname)', 'refs/heads/refused'), '');
  f.git('switch', '-c', 'inert', 'origin/main');
  f.write('README.md', 'Only inert committed bytes\n');
  f.commit();
  const allowed = realGit(f, 'push', 'origin', 'inert');
  assert.equal(allowed.status, 0, output(allowed));
  assert.match(output(allowed), /SUMMARY nothing selected/);
});

test('a real multi-branch push unions merge-base ranges rather than remote old SHAs', t => {
  const { f } = setup(t);
  f.write('src/unit/a.js', 'unit branch\n');
  f.commit();
  const unit = f.git('rev-parse', 'HEAD');
  f.git('branch', 'unit-branch');
  f.git('switch', '-c', 'build-branch', 'origin/main');
  f.write('src/build/b.js', 'build branch\n');
  f.commit();
  const build = f.git('rev-parse', 'HEAD');
  const facts = push(f, line(f, 'unit-branch', unit, unit) + line(f, 'build-branch', build, build));
  assert.deepEqual(facts.changed_paths, ['src/build/b.js', 'src/unit/a.js']);
  assert.deepEqual(facts.selection.map(x => x.check.id), ['unit', 'build']);
  assert.ok(facts.results.every(x => !x.reusable && !x.reused));
  enableHooks(f);
  const result = realGit(f, 'push', 'origin', 'unit-branch', 'build-branch');
  assert.equal(result.status, 0, output(result));
  assert.match(output(result), /SELECT unit/);
  assert.match(output(result), /SELECT build/);
  assert.match(output(result), /^DIRTY$/m);
});

test('empty, deletion and tag pushes do not fetch or run checks', t => {
  const { f } = setup(t);
  f.write('src/unit/a.js', 'selected if inspected\n');
  f.commit();
  f.git('push', 'origin', 'HEAD:refs/heads/deleted');
  const marker = join(f.home, 'fetch-ran');
  const uploadpack = join(f.home, 'uploadpack');
  f.write('../home/uploadpack', `#!/bin/sh\ntouch ${quote(marker)}\nexit 1\n`);
  chmodSync(uploadpack, 0o755);
  f.git('config', 'remote.origin.uploadpack', uploadpack);
  for (const input of ['', line(f, 'deleted', zero), `refs/tags/v1 ${f.git('rev-parse', 'HEAD')} refs/tags/v1 ${zero}\n`]) {
    const facts = push(f, input);
    assert.deepEqual(facts.selection, []);
    assert.deepEqual(facts.results, []);
    assert.equal(facts.push.ranges.length, 0);
    assert.equal(existsSync(marker), false);
  }
  enableHooks(f);
  f.git('tag', 'v1');
  for (const args of [['push', 'origin', ':refs/heads/deleted'], ['push', 'origin', 'v1']]) {
    const result = realGit(f, ...args);
    assert.equal(result.status, 0, output(result));
    assert.match(output(result), /SUMMARY nothing selected/);
    assert.doesNotMatch(output(result), /SELECT |BASE |DIRTY/);
  }
  assert.equal(existsSync(marker), false);
});

test('MMW_CHECKS_SKIP prints the exact reason and appends one JSON line per real hook invocation', t => {
  const f = fixture(t);
  enableHooks(f);
  f.env.MMW_CHECKS_SKIP = 'repair "red"\ncheck';
  f.write('.agents/checks.json', 'invalid config deliberately bypassed');
  f.git('add', '--all');
  const commit = realGit(f, 'commit', '-m', 'Audited bypass');
  assert.equal(commit.status, 0, output(commit));
  assert.ok(output(commit).includes(`SKIPPED BY REASON ${f.env.MMW_CHECKS_SKIP}`));
  const pushed = realGit(f, 'push', 'origin', 'HEAD:refs/heads/bypassed');
  assert.equal(pushed.status, 0, output(pushed));
  assert.ok(output(pushed).includes(`SKIPPED BY REASON ${f.env.MMW_CHECKS_SKIP}`));
  const records = audits(f);
  assert.equal(records.length, 2);
  assert.deepEqual(records.map(x => x.hook), ['pre-commit', 'pre-push']);
  for (const record of records) {
    assert.equal(record.type, 'bypass');
    assert.equal(record.reason, f.env.MMW_CHECKS_SKIP);
    assert.ok(Number.isFinite(Date.parse(record.time)));
    assert.deepEqual(Object.keys(record).sort(), ['hook', 'reason', 'time', 'type']);
  }
});

test('internal engine error returns 70 directly; the real push reports, allows and audits once', t => {
  const { f } = setup(t);
  const engine = join(f.home, 'broken.mjs');
  copyFileSync(new URL('../check.mjs', import.meta.url), engine);
  f.env.MMW_REPO_CHECKS_ENGINE = engine;
  const direct = f.cli('--all', '--json');
  assert.equal(direct.status, 70, output(direct));
  assert.equal(JSON.parse(direct.stdout).exit_code, 70);
  enableHooks(f);
  const pushed = realGit(f, 'push', 'origin', 'HEAD:refs/heads/internal-error');
  assert.equal(pushed.status, 0, output(pushed));
  assert.match(output(pushed), /engine failed \(70\); allowing pre-push/);
  const records = audits(f);
  assert.equal(records.length, 1);
  assert.equal(records[0].type, 'engine-failure');
  assert.equal(records[0].exit_code, 70);
  assert.equal(records[0].hook, 'pre-push');
  assert.ok(Number.isFinite(Date.parse(records[0].time)));
  assert.match(records[0].reason, /engine failed/);
});

test('both canonical hooks deny only 1 and 2 and allow every other exit and killed engines', t => {
  const f = fixture(t);
  const engine = join(f.home, 'override.mjs');
  f.env.MMW_REPO_CHECKS_ENGINE = engine;
  for (const hook of ['pre-commit', 'pre-push']) {
    for (const code of [0, 1, 2, 3, 70, 127, 130, 143, 255]) {
      f.write('../home/override.mjs', `process.exit(${code});\n`);
      const result = spawnSync(join(f.repo, '.githooks', hook), [], {
        cwd: f.repo, env: f.env, encoding: 'utf8', input: '', timeout: 5000,
      });
      assert.equal(result.status, [1, 2].includes(code) ? code : 0, `${hook} ${code}: ${output(result)}`);
    }
    for (const signal of ['SIGKILL', 'SIGTERM']) {
      f.write('../home/override.mjs', `process.kill(process.pid, "${signal}");\n`);
      const result = spawnSync(join(f.repo, '.githooks', hook), [], {
        cwd: f.repo, env: f.env, encoding: 'utf8', input: '', timeout: 5000,
      });
      assert.equal(result.status, 0, `${hook} ${signal}: ${output(result)}`);
      assert.match(output(result), new RegExp(`engine failed \\(${signal}\\)`));
    }
  }
  assert.equal(audits(f).length, 16);
});

test('missing engine falls back to real prek for commits and reports and allows a real push', t => {
  if (!requirePrek(t)) return;
  const f = fixture(t);
  prekConfig(f);
  f.commit('Add fallback config');
  enableHooks(f);
  f.env.MMW_REPO_CHECKS_ENGINE = join(f.home, 'absent.mjs');
  f.write('src/error.js', 'PLANTED_LINT\n');
  f.git('add', '--all');
  const denied = realGit(f, 'commit', '-m', 'Fallback must refuse');
  assert.equal(denied.status, 1, output(denied));
  assert.match(output(denied), /toy-lint|Toy planted lint/);
  assert.match(output(denied), /planted lint error/);
  assert.equal(f.cli().status, 70);
  const pushed = realGit(f, 'push', 'origin', 'HEAD:refs/heads/missing-engine');
  assert.equal(pushed.status, 0, output(pushed));
  assert.match(output(pushed), /engine missing/);
  assert.equal(audits(f).length, 1);
});

test('the shim resolves its default installed engine and honors the engine override', t => {
  const f = fixture(t);
  const folder = join(f.home, '.agents/skills/repo-checks/scripts');
  mkdirSync(folder, { recursive: true });
  copyFileSync(new URL('../check.mjs', import.meta.url), join(folder, 'check.mjs'));
  copyFileSync(new URL('../checks.schema.json', import.meta.url), join(folder, 'checks.schema.json'));
  delete f.env.MMW_REPO_CHECKS_ENGINE;
  assert.match(f.cli('--help').stdout, /Usage: scripts\/check/);
  f.write('../home/override.mjs', 'console.log("override "+process.argv.slice(2).join(" "));\n');
  f.env.MMW_REPO_CHECKS_ENGINE = join(f.home, 'override.mjs');
  const result = f.cli('--staged');
  assert.equal(result.status, 0);
  assert.equal(result.stdout, 'override --staged\n');
});

test('canonical fixture entry preserves nodeArgs fault injection', t => {
  const f = fixture(t, ['--import', 'data:text/javascript,process.stderr.write("fixture preload\\n")']);
  const result = f.cli('--help');
  assert.equal(result.status, 0, output(result));
  assert.equal(result.stderr, 'fixture preload\n');
  assert.match(result.stdout, /Usage: scripts\/check/);
});

test('linked worktrees write bypass JSONL in their own common-directory subfolder', t => {
  const f = fixture(t);
  const linked = join(f.root, 'linked');
  f.git('worktree', 'add', '-b', 'linked', linked, 'HEAD');
  const invoke = repo => spawnSync(join(repo, 'scripts/check'), ['--staged'], {
    cwd: repo, env: { ...f.env, MMW_CHECKS_SKIP: 'worktree audit proof' }, encoding: 'utf8',
  });
  for (const repo of [f.repo, linked]) {
    const result = invoke(repo);
    assert.equal(result.status, 0, output(result));
    assert.match(result.stdout, /SKIPPED BY REASON worktree audit proof/);
  }
  const common = resolve(linked, f.git('-C', linked, 'rev-parse', '--git-common-dir'));
  const folders = readdirSync(join(common, 'repo-checks'));
  assert.equal(folders.length, 2);
  for (const folder of folders) {
    const lines = readFileSync(join(common, 'repo-checks', folder, 'audit.jsonl'), 'utf8').trimEnd().split('\n');
    assert.equal(lines.length, 1);
    assert.equal(JSON.parse(lines[0]).hook, 'pre-commit');
  }
});

test('lint compares all three entry files byte-for-byte, including missing files', t => {
  const f = fixture(t);
  lintJson(f, 0);
  for (const path of ['scripts/check', '.githooks/pre-commit', '.githooks/pre-push']) {
    const original = readFileSync(join(f.repo, path));
    f.write(path, Buffer.concat([original, Buffer.from('\n')]));
    const facts = lintJson(f, 1);
    assert.ok(facts.findings.some(x => x.rule === 'template' && x.path === path));
    assert.ok(f.cli('lint').stdout.includes(path));
    f.write(path, original);
    lintJson(f, 0);
  }
  unlinkSync(join(f.repo, '.githooks/pre-push'));
  assert.ok(lintJson(f, 1).findings.some(x => x.rule === 'template' && x.path === '.githooks/pre-push'));
});

for (const signal of ['SIGINT', 'SIGTERM']) for (const hook of [false, true]) {
  test(`${signal} through ${hook ? 'pre-push hook' : 'entry shim'} stops descendants and never retries`, async t => {
    const { f, c } = setup(t);
    const pids = join(f.home, 'pids.json');
    const attempts = join(f.home, 'attempts');
    c.checks[0].retry = 1;
    c.checks[0].run = command(`const fs=require("node:fs");fs.appendFileSync(${JSON.stringify(attempts)},"attempt\\n");const child=require("node:child_process").spawn(process.execPath,["-e","setInterval(()=>{},1000)"],{stdio:"ignore"});fs.writeFileSync(${JSON.stringify(pids)},JSON.stringify([process.pid,child.pid]));setInterval(()=>{},1000)`);
    f.config(c);
    f.commit();
    const active = hook ? f.start([], { entry: '.githooks/pre-push', input: line(f) }) : f.start(['--all']);
    await until(() => existsSync(pids));
    active.child.kill(signal);
    assert.equal((await active.done).status, hook ? 0 : signal === 'SIGINT' ? 130 : 143);
    const children = JSON.parse(readFileSync(pids));
    const alive = pid => { try { process.kill(pid, 0); return true; } catch (error) { if (error.code !== 'ESRCH') throw error; return false; } };
    await until(() => children.every(pid => !alive(pid)));
    assert.equal(readFileSync(attempts, 'utf8'), 'attempt\n');
  });
}
