import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { chmodSync, copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
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
    inert: ['README.md', 'scripts/check', '.githooks/**'],
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
  copyFileSync(process.env.GIT_CONFIG_GLOBAL ?? join(homedir(), '.gitconfig'), join(home, '.gitconfig'));
  writeFileSync(join(home, 'node'), `#!/bin/sh\nexec ${[process.execPath, ...nodeArgs].map(quote).join(' ')} "$@"\n`);
  chmodSync(join(home, 'node'), 0o755);
  const env = {
    ...process.env,
    HOME: home,
    XDG_CONFIG_HOME: join(home, '.config'),
    XDG_CACHE_HOME: join(home, '.cache'),
    GIT_CONFIG_GLOBAL: join(home, '.gitconfig'),
    GIT_TERMINAL_PROMPT: '0',
    PATH: `${home}:${process.env.PATH}`,
    MMW_REPO_CHECKS_ENGINE: engine,
  };
  for (const key of ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR', 'MMW_REPO_CHECKS_HOOK']) delete env[key];
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
  git('--git-dir', join(root, 'origin.git'), 'symbolic-ref', 'HEAD', 'refs/heads/main');
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
  function invoke(args, options = {}) {
    const start = performance.now();
    const result = spawnSync(join(repo, 'scripts/check'), args, {
      cwd: repo, env, encoding: 'utf8', timeout: 15_000, maxBuffer: 16 * 1024 * 1024, ...options,
    });
    assert.ifError(result.error);
    return { ...result, elapsed_ms: performance.now() - start };
  }
  function cli(...args) { return invoke(args); }
  function start(args = [], options = {}) {
    const child = spawn(join(options.repo ?? repo, options.entry ?? 'scripts/check'), args, {
      cwd: options.repo ?? repo, env: options.env ?? env, stdio: [options.input === undefined ? 'ignore' : 'pipe', 'pipe', 'pipe'],
    });
    if (options.input !== undefined) child.stdin.end(options.input);
    let stdout = '';
    let stderr = '';
    const lines = [];
    child.stdout.on('data', bytes => { stdout += bytes; lines.push({ stream: 'stdout', time: Date.now(), text: String(bytes) }); });
    child.stderr.on('data', bytes => { stderr += bytes; lines.push({ stream: 'stderr', time: Date.now(), text: String(bytes) }); });
    const timer = setTimeout(() => child.kill('SIGKILL'), options.timeout ?? 45_000);
    const done = new Promise((resolve, reject) => {
      child.once('error', reject);
      child.once('close', (status, signal) => {
        clearTimeout(timer);
        resolve({ status, signal, stdout, stderr, lines });
      });
    });
    async function until(pattern, timeout = 5000) {
      const deadline = Date.now() + timeout;
      while (!pattern.test(stdout + stderr)) {
        if (child.exitCode !== null || Date.now() > deadline) {
          throw new Error(`Waiting for ${pattern}\n${stdout}\n${stderr}`);
        }
        await new Promise(resolve => setTimeout(resolve, 20));
      }
    }
    return { child, done, until, lines };
  }
  config(cleanConfig());
  write('README.md', 'Fixture repository.\n');
  for (const [path, template] of [['scripts/check', 'check'], ['.githooks/pre-commit', 'pre-commit'], ['.githooks/pre-push', 'pre-push']]) {
    write(path, readFileSync(new URL(`../../templates/${template}`, import.meta.url)));
    chmodSync(join(repo, path), 0o755);
  }
  commit('Initial fixture');
  git('push', '-u', 'origin', 'main');
  return { root, repo, home, env, git, write, config, commit, cli, invoke, start,
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
