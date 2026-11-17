import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { chmodSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const engine = fileURLToPath(new URL('../check.mjs', import.meta.url));
const quote = value => `'${value.replaceAll("'", "'\\''")}'`;

export function cleanConfig() {
  return {
    integration: 'main',
    ci_workflow: null,
    test_files: ['**/*.test.{js,mjs,ts}', '**/test_*.py'],
    inert: ['README.md', 'scripts/check'],
    affects_all: ['.agents/checks.json'],
    checks: [{
      id: 'unit', run: 'node --test', inputs: ['src/**', 'test/**'],
      tests: ['test/**'], ci: false, ci_reason: 'This repository has no deployment gate.',
    }],
    lanes: [],
    excluded: [],
  };
}

export function fixture(t, nodeArgs = []) {
  const root = mkdtempSync(join(tmpdir(), 'repo-checks-'));
  t?.after(() => rmSync(root, { recursive: true, force: true }));
  const repo = join(root, 'repo');
  const home = join(root, 'home');
  const hooks = join(root, 'hooks');
  for (const dir of [repo, home, hooks]) mkdirSync(dir);
  const env = {
    ...process.env,
    HOME: home,
    XDG_CONFIG_HOME: join(home, '.config'),
    XDG_CACHE_HOME: join(home, '.cache'),
    GIT_CONFIG_GLOBAL: process.env.GIT_CONFIG_GLOBAL ?? join(homedir(), '.gitconfig'),
    GIT_TERMINAL_PROMPT: '0',
  };
  for (const key of ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR']) delete env[key];
  function git(...args) {
    const result = spawnSync('git', ['-c', `core.hooksPath=${hooks}`,
      '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', ...args], {
      cwd: repo, env, encoding: 'utf8', timeout: 15_000,
    });
    assert.equal(result.status, 0, `git ${args.join(' ')}\n${result.stdout}\n${result.stderr}`);
    return result.stdout.trim();
  }
  git('var', 'GIT_AUTHOR_IDENT');
  git('var', 'GIT_COMMITTER_IDENT');
  git('init', '--bare', '--template=', join(root, 'origin.git'));
  git('--git-dir', join(root, 'origin.git'), 'config', 'core.hooksPath', hooks);
  git('init', '--template=', '-b', 'main');
  git('config', 'core.hooksPath', hooks);
  git('remote', 'add', 'origin', join(root, 'origin.git'));
  function write(path, body) {
    const full = join(repo, path);
    mkdirSync(dirname(full), { recursive: true });
    writeFileSync(full, body);
  }
  function config(value) { write('.agents/checks.json', `${JSON.stringify(value, null, 2)}\n`); }
  function commit(message = 'Fixture change') {
    git('add', '--all');
    git('commit', '-m', message);
  }
  function cli(...args) {
    const start = performance.now();
    const result = spawnSync(join(repo, 'scripts/check'), args, {
      cwd: repo, env, encoding: 'utf8', timeout: 15_000, maxBuffer: 16 * 1024 * 1024,
    });
    assert.ifError(result.error);
    return { ...result, elapsed_ms: performance.now() - start };
  }
  config(cleanConfig());
  write('README.md', 'Fixture repository.\n');
  write('scripts/check', `#!/bin/sh\nexec ${[process.execPath, ...nodeArgs, engine].map(quote).join(' ')} "$@"\n`);
  chmodSync(join(repo, 'scripts/check'), 0o755);
  commit('Initial fixture');
  git('push', '-u', 'origin', 'main');
  return { root, repo, home, env, git, write, config, commit, cli,
    cleanup: () => rmSync(root, { recursive: true, force: true }) };
}

export function lintJson(f, expectedStatus) {
  const result = f.cli('lint', '--json');
  assert.equal(result.status, expectedStatus, result.stdout + result.stderr);
  assert.equal(result.stderr, '');
  const facts = JSON.parse(result.stdout);
  assert.equal(facts.mode, 'lint');
  assert.equal(facts.ok, expectedStatus === 0);
  assert.equal(facts.exit_code, expectedStatus);
  assert.ok(Array.isArray(facts.findings));
  for (const finding of facts.findings) {
    assert.equal(typeof finding.rule, 'string');
    assert.equal(typeof finding.message, 'string');
  }
  return facts;
}
