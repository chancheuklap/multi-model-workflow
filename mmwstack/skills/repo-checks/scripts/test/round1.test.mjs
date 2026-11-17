import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, readdirSync, statSync, unlinkSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { cleanConfig, fixture } from './fixture.mjs';

const quote = value => `'${value.replaceAll("'", "'\\''")}'`;
const command = source => `${quote(process.execPath)} -e ${quote(source)}`;
const output = result => result.stdout + result.stderr;
function realGit(f, ...args) {
  const result = spawnSync('git', args, { cwd: f.repo, env: f.env, encoding: 'utf8', timeout: 15_000 });
  assert.ifError(result.error);
  return result;
}
function records(f) {
  const root = join(f.repo, '.git/repo-checks');
  return readdirSync(root).flatMap(name => {
    const folder = join(root, name, 'records');
    return existsSync(folder) ? readdirSync(folder).map(file => JSON.parse(readFileSync(join(folder, file)))) : [];
  });
}

for (const [stream, push] of [['stdout', false], ['stderr', false], ['stdout', true]]) {
  test(`F-A closed ${stream} preserves a failing ${push ? 'real push' : 'direct --all'} result`, async t => {
    const f = fixture(t, stream === 'stderr' ? [
      '--import', 'data:text/javascript,console.log=(...args)=>console.error(...args)',
    ] : []);
    const release = join(f.home, 'reader-closed');
    const c = cleanConfig();
    c.checks[0].run = command(`const fs=require("node:fs");const timer=setInterval(()=>{if(fs.existsSync(${JSON.stringify(release)})){clearInterval(timer);console.error("planted closed-output failure");process.exitCode=1}},10)`);
    f.config(c);
    f.commit('Configure closed-output failure');
    f.git('push', 'origin', 'main');
    f.write('src/input.js', 'selected\n');
    f.commit('Select failing check');
    f.git('config', 'core.hooksPath', '.githooks');
    const active = push
      ? f.start(['push', 'origin', 'HEAD:refs/heads/refused'], { entry: relative(f.repo, '/usr/bin/git') })
      : f.start(['--all']);
    t.after(() => { if (active.child.exitCode === null) active.child.kill('SIGKILL'); });
    await active.until(/SELECT unit/);
    await new Promise(resolve => {
      const pipe = active.child[stream];
      pipe.once('close', resolve);
      pipe.destroy();
    });
    writeFileSync(release, 'closed\n');
    const result = await active.done;
    const saved = records(f).filter(record => record.mode === (push ? 'push' : 'run')).at(-1);
    const remote = push ? f.git('--git-dir', join(f.root, 'origin.git'), 'for-each-ref',
      '--format=%(refname)', 'refs/heads/refused') : null;
    t.diagnostic(JSON.stringify({ stream, push, status: result.status, signal: result.signal, remote, exit_code: saved?.exit_code,
      check_status: saved?.results[0]?.status, check_exit: saved?.results[0]?.attempts[0]?.exit_code }));
    assert.equal(result.status, 1, output(result));
    assert.equal(saved.exit_code, 1);
    assert.equal(saved.results[0].status, 'failed');
    assert.equal(saved.results[0].attempts[0].exit_code, 1);
    if (push) assert.equal(remote, '');
  });
}

test('F-B an actual pre-push check has no hook context and its nested manual failure remains 70', t => {
  const f = fixture(t);
  const c = cleanConfig();
  const evidence = join(f.home, 'command-environment.json');
  c.checks[0].run = command(`const fs=require("node:fs");const result=require("node:child_process").spawnSync("./scripts/check",["--all"],{env:{...process.env,MMW_REPO_CHECKS_ENGINE:"/nonexistent"},encoding:"utf8"});const facts={hook:process.env.MMW_REPO_CHECKS_HOOK??null,status:result.status};fs.writeFileSync(${JSON.stringify(evidence)},JSON.stringify(facts));console.log(JSON.stringify(facts));process.exitCode=facts.hook===null&&facts.status===70?0:1`);
  f.config(c);
  f.commit('Configure nested check');
  f.git('push', 'origin', 'main');
  f.write('src/input.js', 'selected\n');
  f.commit();
  const manual = f.invoke(['--all'], { env: { ...f.env, MMW_REPO_CHECKS_ENGINE: '/nonexistent' } });
  assert.equal(manual.status, 70, output(manual));
  f.git('config', 'core.hooksPath', '.githooks');
  const result = realGit(f, 'push', 'origin', 'HEAD:refs/heads/nested');
  t.diagnostic(output(result).trim());
  assert.equal(result.status, 0, output(result));
  assert.deepEqual(JSON.parse(readFileSync(evidence)), { hook: null, status: 70 });
  const saved = records(f).at(-1);
  assert.match(readFileSync(saved.results[0].log, 'utf8'), /"hook":null,"status":70/);
});

test('F-C plain cp -p installs executable templates and a real commit runs real prek', t => {
  const version = spawnSync('prek', ['--version'], { encoding: 'utf8' });
  if (version.error?.code === 'ENOENT') {
    return t.skip('Install real prek: brew install prek (or uv tool install prek).');
  }
  assert.ifError(version.error);
  assert.equal(version.status, 0, version.stderr);
  t.diagnostic(version.stdout.trim());
  const f = fixture(t);
  for (const [template, entry] of [['check', 'scripts/check'], ['pre-commit', '.githooks/pre-commit'], ['pre-push', '.githooks/pre-push']]) {
    unlinkSync(join(f.repo, entry));
    const copied = spawnSync('/bin/cp', ['-p', fileURLToPath(new URL(`../../templates/${template}`, import.meta.url)), join(f.repo, entry)], { encoding: 'utf8' });
    assert.equal(copied.status, 0, copied.stderr);
    assert.equal(statSync(join(f.repo, entry)).mode & 0o111, 0o111, entry);
  }
  const marker = join(f.home, 'real-prek-ran');
  f.write('prek.toml', `[[repos]]\nrepo = "local"\n[[repos.hooks]]\nid = "marker"\nname = "Real prek marker"\nlanguage = "system"\nentry = ${JSON.stringify(command(`require("node:fs").writeFileSync(${JSON.stringify(marker)},"ran")`))}\nalways_run = true\npass_filenames = false\n`);
  f.git('add', '--all');
  f.git('config', 'core.hooksPath', '.githooks');
  const result = realGit(f, 'commit', '-m', 'Run copied hooks');
  assert.equal(result.status, 0, output(result));
  assert.match(output(result), /Real prek marker/);
  assert.equal(readFileSync(marker, 'utf8'), 'ran');
});

test('F-D a GUI PATH without Node allows real commit and push with a warning but manual checks return 70', t => {
  const f = fixture(t);
  assert.notEqual(spawnSync('/bin/sh', ['-c', 'command -v node'], { env: { PATH: '/usr/bin:/bin' } }).status, 0);
  f.git('config', 'core.hooksPath', '.githooks');
  f.write('README.md', 'Minimal GUI PATH\n');
  f.git('add', '--all');
  f.env.PATH = '/usr/bin:/bin';
  const direct = f.cli('--all');
  assert.equal(direct.status, 70, output(direct));
  assert.match(direct.stderr, /repo-checks .*unavailable/i);
  for (const args of [['commit', '-m', 'GUI commit'], ['push', 'origin', 'HEAD:refs/heads/gui']]) {
    const result = realGit(f, ...args);
    assert.equal(result.status, 0, output(result));
    assert.match(result.stderr, /repo-checks .*unavailable/i);
  }
  assert.equal(f.git('--git-dir', join(f.root, 'origin.git'), 'rev-parse', 'refs/heads/gui'), f.git('rev-parse', 'HEAD'));
});
