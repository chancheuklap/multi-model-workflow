#!/usr/bin/env node
import { accessSync, closeSync, constants, existsSync, lstatSync, mkdirSync, openSync, readFileSync, readlinkSync, realpathSync, renameSync, statSync, writeFileSync } from 'node:fs';
import { execFileSync, spawn, spawnSync } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import { delimiter, isAbsolute, join, relative, resolve, sep } from 'node:path';

const configPath = '.agents/checks.json';

const schemaKeywords = new Set([
  '$schema', '$defs', '$ref', 'type', 'properties', 'required', 'additionalProperties',
  'items', 'minLength', 'pattern', 'enum', 'minimum', 'maximum', 'exclusiveMinimum',
  'allOf', 'anyOf', 'if', 'then', 'else', 'dependentRequired', 'format',
]);
const matchesType = (value, type) => {
  if (type === 'null') return value === null;
  if (type === 'array') return Array.isArray(value);
  if (type === 'object') return value !== null && typeof value === 'object' && !Array.isArray(value);
  if (type === 'integer') return Number.isInteger(value);
  return typeof value === type;
};
const childField = (field, key) => field ? `${field}.${key}` : key;

function validate(value, schema, node = schema, field = '') {
  for (const key of Object.keys(node)) {
    if (!schemaKeywords.has(key)) throw new Error(`Unsupported schema keyword ${key}`);
  }
  const findings = [];
  const invalid = (message, at = field) => findings.push({
    rule: 'schema', field: at || 'root', message: `${at || 'root'}: ${message}`,
  });
  if (node.$ref) {
    const target = node.$ref.split('/').slice(1).reduce((part, key) => part[key], schema);
    findings.push(...validate(value, schema, target, field));
  }
  if (node.type && !matchesType(value, node.type)) {
    invalid(`expected ${node.type}`);
    return findings;
  }
  if (node.enum && !node.enum.includes(value)) invalid(`expected one of ${JSON.stringify(node.enum)}`);
  if (typeof value === 'string') {
    if (node.minLength !== undefined && value.length < node.minLength) invalid(`minimum length ${node.minLength}`);
    if (node.pattern && !new RegExp(node.pattern).test(value)) invalid(`does not match ${node.pattern}`);
    if (node.format) {
      if (node.format !== 'repo-glob') throw new Error(`Unsupported schema format ${node.format}`);
      try { compileGlob(value); }
      catch (error) { invalid(`invalid glob: ${error.message}`); }
    }
  }
  if (typeof value === 'number') {
    if (node.minimum !== undefined && value < node.minimum) invalid(`minimum ${node.minimum}`);
    if (node.maximum !== undefined && value > node.maximum) invalid(`maximum ${node.maximum}`);
    if (node.exclusiveMinimum !== undefined && value <= node.exclusiveMinimum) invalid(`must exceed ${node.exclusiveMinimum}`);
  }
  if (matchesType(value, 'object')) {
    for (const key of node.required ?? []) {
      if (!Object.hasOwn(value, key)) invalid('required field', childField(field, key));
    }
    for (const [key, item] of Object.entries(value)) {
      if (Object.hasOwn(node.properties ?? {}, key)) findings.push(...validate(item, schema, node.properties[key], childField(field, key)));
      else if (node.additionalProperties === false) invalid('unknown field', childField(field, key));
    }
    for (const [key, required] of Object.entries(node.dependentRequired ?? {})) {
      if (!Object.hasOwn(value, key)) continue;
      for (const dependency of required) {
        if (!Object.hasOwn(value, dependency)) invalid(`required with ${key}`, childField(field, dependency));
      }
    }
  }
  if (Array.isArray(value) && node.items) {
    value.forEach((item, index) => findings.push(...validate(item, schema, node.items, `${field}[${index}]`)));
  }
  for (const item of node.allOf ?? []) findings.push(...validate(value, schema, item, field));
  if (node.anyOf && !node.anyOf.some(item => validate(value, schema, item, field).length === 0)) invalid('does not match any allowed form');
  if (node.if) {
    const branch = validate(value, schema, node.if, field).length === 0 ? node.then : node.else;
    if (branch) findings.push(...validate(value, schema, branch, field));
  }
  return findings;
}

function configFindings(config, schema) {
  const findings = validate(config, schema);
  if (findings.length) return findings;
  const ids = new Set();
  config.checks.forEach((check, index) => {
    if (ids.has(check.id)) findings.push({
      rule: 'schema', field: `checks[${index}].id`, check: check.id,
      message: `checks[${index}].id: duplicate check id ${check.id}`,
    });
    ids.add(check.id);
    if (check.ci && config.ci_workflow === null) findings.push({
      rule: 'schema', field: 'ci_workflow', check: check.id,
      message: `ci_workflow: ${check.id} is marked ci but no gate workflow is configured`,
    });
  });
  return findings;
}

function globSource(pattern) {
  let source = '';
  for (let i = 0; i < pattern.length; i++) {
    const char = pattern[i];
    if (char === '{') {
      let depth = 1;
      let end = i + 1;
      let start = end;
      const parts = [];
      for (; end < pattern.length && depth; end++) {
        if (pattern[end] === '{') depth++;
        if (pattern[end] === '}') depth--;
        if ((pattern[end] === ',' && depth === 1) || depth === 0) {
          parts.push(pattern.slice(start, end));
          start = end + 1;
        }
      }
      if (depth === 0 && parts.length > 1) {
        source += `(?:${parts.map(globSource).join('|')})`;
        i = end - 1;
        continue;
      }
    }
    if (char === '*') {
      const start = i;
      while (pattern[i + 1] === '*') i++;
      const globstar = i > start && (start === 0 || pattern[start - 1] === '/') &&
        (i + 1 === pattern.length || pattern[i + 1] === '/');
      if (globstar && pattern[i + 1] === '/') {
        source += '(?:[^/]+/)*';
        i++;
      } else source += globstar ? '.*' : '[^/]*';
    } else if (char === '?') source += '[^/]';
    else if (char === '[' && pattern.indexOf(']', i + 1) > i + 1) {
      const end = pattern.indexOf(']', i + 1);
      let range = pattern.slice(i + 1, end);
      if (range.startsWith('!')) range = `^${range.slice(1)}`;
      source += `(?!/)[${range}]`;
      i = end;
    } else source += char.replace(/[\\^$.*+?()[\]{}|]/g, '\\$&');
  }
  return source;
}

const globCache = new Map();
function compileGlob(pattern) {
  if (!globCache.has(pattern)) globCache.set(pattern, new RegExp(`^(?:${globSource(pattern)})$`, 's'));
  return globCache.get(pattern);
}

function patternsMatch(patterns) {
  const compiled = patterns.map(compileGlob);
  return path => compiled.some(pattern => pattern.test(path));
}

function ciFindings(config) {
  const checks = config.checks.filter(check => check.ci);
  if (!checks.length) return [];
  const path = config.ci_workflow.includes('/') ? config.ci_workflow : `.github/workflows/${config.ci_workflow}`;
  let workflow;
  try {
    workflow = readFileSync(path, 'utf8');
  } catch (error) {
    return checks.map(check => ({
      rule: 'ci-workflow', check: check.id, path,
      message: `${check.id}: cannot read gate workflow ${path}: ${error.message}`,
    }));
  }
  return checks.filter(check => !workflow.includes(check.ci_run)).map(check => ({
    rule: 'ci-command', check: check.id, field: 'ci_run', path,
    message: `${check.id}: ci_run ${JSON.stringify(check.ci_run)} is absent from ${path}`,
  }));
}

function protectedFindings(config) {
  const protectedLanes = config.lanes.filter(lane => lane.kind === 'owner-only' || lane.kind === 'device');
  const findings = [];
  config.checks.forEach((check, index) => {
    for (const commandField of ['run', 'run_all']) {
      if (!check[commandField]) continue;
      for (const lane of protectedLanes) {
        if (check[commandField] !== lane.command) continue;
        const field = `checks[${index}].${commandField}`;
        findings.push({
          rule: 'protected-command', check: check.id, field,
          message: `${check.id}: ${field} equals protected ${lane.kind} lane ${lane.id} command`,
        });
      }
    }
  });
  return findings;
}

function integrationFindings(config) {
  const ref = `refs/remotes/origin/${config.integration}`;
  const refs = execFileSync('git', ['for-each-ref', '--format=%(refname)%00%(objecttype)%00%(symref)', 'refs/remotes/origin/'], { encoding: 'utf8' });
  const branch = refs.trimEnd().split('\n').some(line => {
    const [name, type, symbolic] = line.split('\0');
    return name === ref && type === 'commit' && symbolic === '' && config.integration !== 'HEAD';
  });
  return branch ? [] : [{
    rule: 'integration', field: 'integration',
    message: `integration: ${JSON.stringify(config.integration)} is not a remote branch at ${ref}`,
  }];
}

const legacyMarkers = [
  { marker: 'MMW_BASE_REF', pattern: /\bMMW_BASE_REF\b/g },
  { marker: '.scratch/check', pattern: /\.scratch\/check(?![\w.-])/g },
  { marker: 'run by MMW before every ticket lands', pattern: /run\s+by\s+MMW\s+before\s+every\s+ticket\s+lands|MMW[^\n]{0,30}每(?:张|个)?(?:工单|票据|票)[^\n]{0,12}(?:合并|落地)前/gi },
  { marker: 'scripts/check --step', pattern: /\bscripts\/check\s+--step\b/g },
  { marker: 'dispatch.sh', pattern: /\bdispatch\.sh\b/g, context: 'checks' },
  { marker: 'verify-ticket', pattern: /\bverify-ticket\b/g, context: 'checks' },
  { marker: 'setup-mmw', pattern: /\bsetup-mmw\b/g, context: 'checks' },
  { marker: '.worktrees/', pattern: /(?<![\w.-])(?<!\.\.\/)\.worktrees(?:\/|(?=[\s"'`,\]}]|$))/g, context: 'exclusion' },
  { marker: '.mmw/', pattern: /\.mmw(?:\/|(?=[\s"'`,\]}]|$))/g, context: 'workflow-filter' },
  { marker: 'v4 check tiers', pattern: /\bdefault\s+tier\b|--(?:all|staged)\s+tier\b|\bthree\s+tiers\b|三档|默认档/gi, context: 'checks' },
  ...['INPUTS', 'READS', 'NOT_INPUTS', 'GROUP_MAP', 'GATE_INPUTS'].map(marker => ({
    marker, pattern: new RegExp(`\\b${marker}\\b`, 'g'), context: 'checks',
  })),
  { marker: 'verify-erp ticket CHECK', pattern: /\bCHECK\b/g, context: 'ticket-check' },
];

function workflowFilterAt(text, index) {
  let offset = 0;
  let filterIndent = null;
  let inTriggers = false;
  for (const line of text.split('\n')) {
    const indent = line.search(/\S/);
    const topKey = indent === 0 && !line.startsWith('#');
    if (topKey) inTriggers = /^["']?on["']?\s*:/.test(line);
    const key = line.match(/^(\s*)["']?paths(?:-ignore)?["']?\s*:/);
    const inlineFilter = /[,{]\s*["']?paths(?:-ignore)?["']?\s*:/.test(line);
    if (inTriggers && (key || inlineFilter)) filterIndent = indent;
    else if (!inTriggers || (filterIndent !== null && indent >= 0 && !line.trimStart().startsWith('#') && indent <= filterIndent)) filterIndent = null;
    if (offset + line.length >= index) return filterIndent !== null;
    offset += line.length + 1;
  }
  return false;
}

function markerContext(kind, path, text, index) {
  if (!kind) return true;
  const before = text.slice(0, index);
  const after = text.slice(index);
  const nearby = [...before.split('\n').slice(-3), ...after.split('\n').slice(0, 3)].join('\n');
  const heading = before.match(/^#{1,6}\s+.*$/gm)?.at(-1) ?? '';
  const context = `${heading}\n${nearby}`;
  const workflow = /^\.github\/workflows\/[^/]+\.ya?ml$/.test(path);
  if (kind === 'workflow-filter') return workflow && workflowFilterAt(text, index);
  if (kind === 'exclusion') {
    if (workflow) return workflowFilterAt(text, index);
    const tomlSection = before.match(/^\s*\[([^\]]+)\]/gm)?.at(-1) ?? '';
    const testOrLintSection = /(?:^|\/)pyproject\.toml$/.test(path) &&
      /\[tool\.(?:pytest|ruff|black|isort|coverage|pylint|flake8|mypy)(?:[.\]]|$)/.test(tomlSection);
    return testOrLintSection || /(?:^|\/)\.(?:gitignore|dockerignore|ignore|eslintignore|prettierignore)$|(?:eslint|oxlint|vitest|jest|pytest|ruff)[^/]*(?:config|\.ini|\.json|\.toml)/.test(path) ||
      /\b(?:ignore[sd]?|exclud\w*|omit)\b|排除|忽略/i.test(context);
  }
  if (kind === 'ticket-check') return /(?:^|\/)verify-erp(?:\/|$)/.test(path) && /\bticket\b|工单|票据/i.test(context);
  return path === 'scripts/check' || /^\.githooks\//.test(path) ||
    /\bscripts\/check\b|\bcheck(?:s|ers)?\b|检查|MMW[^\n]*(?:工单|ticket)/i.test(context);
}

function markerFindings(path) {
  let bytes;
  try {
    const stat = lstatSync(path);
    if (stat.isDirectory()) return [];
    bytes = stat.isSymbolicLink() ? Buffer.from(readlinkSync(path)) : readFileSync(path);
  } catch (error) {
    if (error.code === 'ENOENT') return [];
    return [{ rule: 'tracked-read', path, message: `${JSON.stringify(path)}: cannot scan tracked file: ${error.message}` }];
  }
  if (bytes.includes(0)) return [];
  const text = bytes.toString('utf8');
  const findings = [];
  for (const { marker, pattern, context } of legacyMarkers) {
    for (const match of text.matchAll(pattern)) {
      if (!markerContext(context, path, text, match.index)) continue;
      findings.push({
        rule: 'legacy-marker', path, marker,
        message: `${JSON.stringify(path)}: legacy marker ${JSON.stringify(marker)} (${JSON.stringify(match[0])})`,
      });
      break;
    }
  }
  return findings;
}

function repositoryFindings(config) {
  const findings = [...integrationFindings(config), ...ciFindings(config), ...protectedFindings(config)];
  const classified = patternsMatch([
    ...config.inert, ...config.affects_all,
    ...config.checks.flatMap(check => [...check.inputs, ...(check.sources ?? [])]),
  ]);
  const isTest = patternsMatch(config.test_files);
  const exempt = patternsMatch(config.marker_exempt ?? []);
  const claimed = patternsMatch([
    ...config.checks.flatMap(check => check.tests),
    ...config.lanes.flatMap(lane => lane.tests),
    ...config.excluded.flatMap(exclusion => exclusion.paths),
  ]);
  const tracked = execFileSync('git', ['ls-files', '-z'], { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 })
    .split('\0').filter(Boolean);
  for (const path of tracked) {
    if (!classified(path)) findings.push({
      rule: 'unclassified', path,
      message: `${JSON.stringify(path)}: matches none of inputs, sources, inert or affects_all`,
    });
    if (isTest(path) && !claimed(path)) findings.push({
      rule: 'unclaimed-test', path,
      message: `${JSON.stringify(path)}: no check tests, lane or exclusion claims this test`,
    });
    if (!exempt(path)) findings.push(...markerFindings(path));
  }
  return findings;
}

function lint(schema) {
  let config;
  try {
    config = JSON.parse(readFileSync(configPath, 'utf8'));
  } catch (error) {
    return { mode: 'lint', ok: false, exit_code: 2, findings: [{
      rule: 'config-read', path: configPath, message: `${configPath}: ${error.message}`,
    }] };
  }
  const findings = configFindings(config, schema);
  if (!findings.length) findings.push(...repositoryFindings(config));
  return { mode: 'lint', ok: findings.length === 0, exit_code: findings.length ? 1 : 0, findings };
}

const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const shellQuote = value => `'${value.replaceAll("'", "'\\''")}'`;

class RequestError extends Error {
  constructor(message, rule = 'request') {
    super(message);
    this.rule = rule;
  }
}

function parseRequest(args) {
  const request = { scope: 'changed', only: null, base: null };
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--all') request.scope = 'all';
    else if ((arg === '--only' || arg === '--base') && args[i + 1] && !args[i + 1].startsWith('-')) {
      const value = args[++i];
      if (arg === '--base') request.base = value;
      else {
        const ids = value.split(',');
        if (ids.some(id => !id || /\s/.test(id))) throw new RequestError('--only requires comma-separated check ids', 'usage');
        request.only = [...new Set([...(request.only ?? []), ...ids])];
      }
    } else throw new RequestError(`Invalid argument ${JSON.stringify(arg)}. Use --help.`, 'usage');
  }
  return request;
}

function git(...args) {
  return execFileSync('git', args, { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024, stdio: ['ignore', 'pipe', 'pipe'] });
}

function changedNames(output) {
  const fields = output.split('\0');
  const paths = [];
  for (let i = 0; i < fields.length && fields[i];) {
    const status = fields[i++];
    paths.push(fields[i++]);
    if (/^[RC]/.test(status)) paths.push(fields[i++]);
  }
  return paths;
}

function newRun() {
  return {
    mode: 'run', ok: false, exit_code: 70, record_version: 1,
    request: { scope: 'changed', only: null, base: null },
    selection: [], results: [], summary: { selected: 0, passed: 0, failed: 0, skipped: 0, blocked: 0 },
    lanes: [], events: [], timing: { select_ms: 0 }, preparation_stamp: null,
  };
}

function fetchIntegration(integration) {
  return new Promise((resolveFetch, reject) => {
    const child = spawn('git', [
      '-c', 'credential.interactive=false', '-c', 'maintenance.auto=false',
      'fetch', '--no-tags', '--no-recurse-submodules', '--refmap=', 'origin',
      `+refs/heads/${integration}:refs/remotes/origin/${integration}`,
    ], { stdio: 'ignore', detached: process.platform !== 'win32', env: { ...process.env, GIT_TERMINAL_PROMPT: '0' } });
    const timer = setTimeout(() => {
      try {
        if (process.platform === 'win32') {
          const killed = spawnSync('taskkill', ['/PID', String(child.pid), '/T', '/F'], { stdio: 'ignore', timeout: 2000 });
          if (killed.error) throw killed.error;
          child.kill('SIGKILL');
        } else process.kill(-child.pid, 'SIGKILL');
      } catch (error) {
        if (error.code !== 'ESRCH') reject(error);
      }
    }, 2500);
    child.once('error', error => { clearTimeout(timer); reject(error); });
    child.once('close', code => { clearTimeout(timer); resolveFetch(code === 0); });
  });
}

async function collectChanges(config, facts) {
  const remote = `refs/remotes/origin/${config.integration}`;
  const validRef = spawnSync('git', ['check-ref-format', `refs/heads/${config.integration}`], { stdio: 'ignore' });
  if (validRef.error) throw validRef.error;
  if (validRef.status !== 0 || config.integration === 'HEAD') throw new RequestError(`Invalid integration branch ${JSON.stringify(config.integration)}`);
  facts.timing.fetch_ms = 0;
  if (!facts.request.base) {
    const fetchStart = performance.now();
    const fetched = await fetchIntegration(config.integration);
    facts.timing.fetch_ms = performance.now() - fetchStart;
    if (!fetched) facts.events.push({
      type: 'BASE', ref: remote, fallback: true,
      reason: `fetch failed; using local ${remote}`,
    });
  }
  const start = performance.now();
  const invalidIntegration = facts.request.base ? [] : integrationFindings(config);
  if (invalidIntegration.length) throw new RequestError(invalidIntegration[0].message);
  facts.identity = {
    worktree: git('rev-parse', '--show-toplevel').trim(),
    head: git('rev-parse', 'HEAD').trim(),
    tree: git('rev-parse', 'HEAD^{tree}').trim(),
    config_hash: hash(readFileSync(configPath)),
    engine_hash: hash(readFileSync(new URL(import.meta.url))),
  };
  facts.identity.engine_version = facts.identity.engine_hash;
  const ref = facts.request.base ?? remote;
  let base;
  try { base = git('merge-base', 'HEAD', ref).trim(); }
  catch (error) {
    if (!error.status) throw error;
    throw new RequestError(`Cannot find merge base with ${ref}: ${error.stderr?.toString().trim()}`);
  }
  facts.base = { ref, commit: base };
  const diff = (...range) => changedNames(git('diff', '--name-status', '-z', '--find-renames', ...range, '--'));
  const committed = diff(base, 'HEAD');
  const staged = diff('--cached');
  const unstaged = diff();
  const untracked = git('ls-files', '--others', '--exclude-standard', '-z').split('\0').filter(Boolean);
  facts.changed_paths = [...new Set([...committed, ...staged, ...unstaged, ...untracked])].sort();
  facts.identity.dirty = staged.length + unstaged.length + untracked.length > 0;
  facts.timing.select_ms += performance.now() - start;
}

function expandCommand(template, scope) {
  if (scope.kind === 'whole') return template;
  return template.replace(/\{(files|tests)\}/g, (_, list) => scope[list].map(shellQuote).join(' '));
}

function selectorTests(check, files, facts) {
  const command = expandCommand(check.select, { kind: 'narrowed', files, tests: [] });
  const start = performance.now();
  let result;
  try {
    result = spawnSync(command, { shell: true, encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 });
  } finally {
    facts.timing.selector_ms += performance.now() - start;
  }
  if (result.error) {
    if (result.error.code !== 'ENOBUFS') throw result.error;
    throw new RequestError(`Selector ${check.id}: output exceeds 16 MiB`);
  }
  if (result.status !== 0) throw new RequestError(`Selector ${check.id} failed (${result.status ?? result.signal}): ${result.stderr.trim()}`);
  let tests;
  try { tests = JSON.parse(result.stdout); }
  catch { throw new RequestError(`Selector ${check.id}: stdout must be a JSON array of test paths`); }
  if (!Array.isArray(tests)) throw new RequestError(`Selector ${check.id}: expected a JSON array of test paths`);
  const belongs = patternsMatch(check.tests);
  for (const path of tests) {
    if (typeof path !== 'string' || !/^(?!\/|[A-Za-z]:)(?!.*(?:^|\/)\.\.(?:\/|$))[^\\\0]+$/.test(path) || !belongs(path)) {
      throw new RequestError(`Selector ${check.id}: invalid or unclaimed test path ${JSON.stringify(path)}`);
    }
    if (existsSync(path)) {
      const destination = relative(realpathSync('.'), realpathSync(path));
      if (isAbsolute(destination) || destination === '..' || destination.startsWith(`..${sep}`)) {
        throw new RequestError(`Selector ${check.id}: test path escapes repository ${JSON.stringify(path)}`);
      }
    }
  }
  return [...new Set(tests)];
}

function selectChecks(config, facts) {
  const start = performance.now();
  facts.timing.selector_ms = 0;
  try {
    const affects = patternsMatch(config.affects_all);
    const classified = patternsMatch([
      ...config.inert, ...config.affects_all,
      ...config.checks.flatMap(check => [...check.inputs, ...(check.sources ?? [])]),
    ]);
    let widened;
    if (facts.request.scope !== 'all') {
      for (const path of facts.changed_paths) {
        let reason;
        if (affects(path)) reason = `affects_all ${path}`;
        else if (!classified(path)) {
          facts.events.push({ type: 'UNCLASSIFIED', path });
          reason = `UNCLASSIFIED ${path}`;
        }
        if (reason) {
          widened ??= reason;
          facts.events.push({ type: 'WIDEN', reason, path });
        }
      }
    }
    facts.selection = config.checks.flatMap(check => {
      if (facts.request.only && !facts.request.only.includes(check.id)) return [];
      if (facts.request.scope === 'all' || widened) return [{
        check, reason: facts.request.scope === 'all' ? '--all' : widened, scope: { kind: 'whole' },
      }];
      const match = patternsMatch(check.inputs);
      const path = facts.changed_paths.find(match);
      if (path) return [{ check, reason: `inputs ${path}`, scope: { kind: 'whole' } }];
      const files = facts.changed_paths.filter(patternsMatch(check.sources ?? []));
      if (!files.length) return [];
      const tests = selectorTests(check, files, facts);
      return tests.length ? [{ check, reason: `sources ${files[0]}`, scope: { kind: 'narrowed', files, tests } }] : [];
    });
    facts.events.push(...facts.selection.map(({ check, reason }) => ({ type: 'SELECT', id: check.id, reason })));
  } finally {
    facts.timing.select_ms += performance.now() - start - facts.timing.selector_ms;
  }
}

function runStorage(facts) {
  const common = resolve(git('rev-parse', '--git-common-dir').trim());
  const folder = join(common, 'repo-checks', hash(facts.identity.worktree).slice(0, 24));
  const id = `${Date.now()}-${randomUUID()}`;
  const logs = join(folder, 'logs', id);
  const records = join(folder, 'records');
  mkdirSync(logs, { recursive: true });
  mkdirSync(records, { recursive: true });
  facts.storage = { worktree_dir: folder, record: join(records, `${id}.json`), logs };
}

function commandExists(name) {
  const extensions = process.platform === 'win32' ? ['', ...(process.env.PATHEXT ?? '.COM;.EXE;.BAT;.CMD').split(';')] : [''];
  for (const folder of (process.env.PATH ?? '').split(delimiter)) {
    for (const extension of extensions) {
      const path = join(folder, `${name}${extension}`);
      try {
        accessSync(path, constants.X_OK);
        if (statSync(path).isFile()) return true;
      } catch (error) {
        if (!['ENOENT', 'ENOTDIR', 'EACCES'].includes(error.code)) throw error;
      }
    }
  }
  return false;
}

function needSatisfied(need) {
  if (need === 'docker') {
    const probe = spawnSync('docker', ['info'], { stdio: 'ignore', timeout: 2500 });
    if (probe.error && !['ENOENT', 'ETIMEDOUT'].includes(probe.error.code)) throw probe.error;
    return probe.status === 0;
  }
  const colon = need.indexOf(':');
  const kind = need.slice(0, colon);
  const value = need.slice(colon + 1);
  if (kind === 'cmd') return commandExists(value);
  if (kind === 'os') return (process.platform === 'win32' ? 'windows' : process.platform) === value;
  if (kind === 'env') return Object.hasOwn(process.env, value);
  if (kind === 'path') return existsSync(value);
  throw new Error(`Unknown need ${need}`);
}

function executeSerial(facts) {
  for (const { check, scope } of facts.selection) {
    const command = expandCommand(scope.kind === 'whole' ? check.run_all ?? check.run : check.run, scope);
    const missing = (check.needs ?? []).filter(need => !needSatisfied(need));
    if (missing.length) {
      const outcome = {
        id: check.id, status: 'skipped', reason: `needs ${missing.join(', ')}`,
        missing_needs: missing, gate_runs_it: check.ci,
        ci: check.ci, ci_reason: check.ci_reason ?? null,
        command, scope, seconds: 0, log: null, tail: [], attempts: [],
      };
      facts.results.push(outcome);
      facts.events.push({ type: 'SKIP', ...outcome });
      continue;
    }
    const log = join(facts.storage.logs, `${hash(check.id).slice(0, 24)}.log`);
    const fd = openSync(log, 'w');
    const start = performance.now();
    let result;
    try { result = spawnSync(command, { shell: true, stdio: ['ignore', fd, fd] }); }
    finally { closeSync(fd); }
    if (result.error) throw result.error;
    const seconds = (performance.now() - start) / 1000;
    const status = result.status === 0 ? 'passed' : 'failed';
    const tail = readFileSync(log, 'utf8').replace(/\r\n/g, '\n').replace(/\n$/, '').split('\n').slice(-40);
    const outcome = {
      id: check.id, status, seconds, command, scope, log, tail,
      ci: check.ci, ci_reason: check.ci_reason ?? null,
      attempts: [{ exit_code: result.status, signal: result.signal, seconds, log }],
    };
    facts.results.push(outcome);
    facts.events.push({ type: status === 'passed' ? 'PASS' : 'FAIL', ...outcome });
  }
}

function finishRun(facts) {
  facts.summary.selected = facts.selection.length;
  for (const result of facts.results) facts.summary[result.status]++;
  const uncovered = facts.results.some(result => result.status === 'skipped' && !result.gate_runs_it);
  facts.exit_code = uncovered || facts.summary.blocked ? 2 : facts.summary.failed ? 1 : 0;
  facts.ok = facts.exit_code === 0;
  facts.events.push(...facts.lanes.map(lane => ({ type: 'LANE', ...lane })));
  facts.events.push({ type: 'SUMMARY', ...facts.summary });
  const temporary = `${facts.storage.record}.tmp`;
  writeFileSync(temporary, `${JSON.stringify(facts)}\n`);
  renameSync(temporary, facts.storage.record);
}

async function run(schema, facts) {
  let config;
  try { config = JSON.parse(readFileSync(configPath, 'utf8')); }
  catch (error) { throw new RequestError(`${configPath}: ${error.message}`); }
  const findings = [...configFindings(config, schema)];
  if (findings.length) throw new RequestError(findings.map(x => x.message).join('\n'));
  findings.push(...protectedFindings(config));
  if (findings.length) throw new RequestError(findings.map(x => x.message).join('\n'));
  for (const id of facts.request.only ?? []) {
    if (!config.checks.some(check => check.id === id)) throw new RequestError(`Unknown check id ${JSON.stringify(id)}`, 'usage');
  }
  await collectChanges(config, facts);
  selectChecks(config, facts);
  facts.lanes = config.lanes;
  runStorage(facts);
  executeSerial(facts);
  finishRun(facts);
}

function eventLines(event) {
  const { type } = event;
  if (type === 'SELECT') return [`SELECT ${event.id} ${event.reason}`];
  if (type === 'BASE') return [`BASE ${event.reason}`];
  if (type === 'UNCLASSIFIED') return [`UNCLASSIFIED ${event.path}`];
  if (type === 'WIDEN') return [`WIDEN ${event.reason}`];
  if (type === 'SKIP') return [`SKIP ${event.id} ${event.reason}${event.gate_runs_it ? ' (gate runs it)' : ''}`];
  if (type === 'LANE') return [`not run here ${event.id} ${event.kind}: ${event.reason}; run_by=${event.run_by}`];
  if (type === 'PASS') return [`PASS ${event.id} ${event.seconds.toFixed(3)}s`];
  if (type === 'FAIL') return [`FAIL ${event.id} ${event.seconds.toFixed(3)}s log=${event.log}`, ...event.tail];
  if (type === 'SUMMARY') return [event.selected === 0 ? 'SUMMARY nothing selected' :
    `SUMMARY ${event.selected} selected, ${event.passed} passed, ${event.failed} failed, ${event.skipped} skipped`];
  if (type === 'ERROR') return [`${event.rule.toUpperCase()} ${event.message}`];
  throw new Error(`Unknown event ${type}`);
}

function emit(facts, json) {
  if (json) console.log(JSON.stringify(facts));
  else if (facts.mode === 'lint') {
    if (facts.ok) console.log('LINT clean');
    else for (const finding of facts.findings) console.log(`LINT ${finding.rule} ${finding.message}`);
  } else {
    for (const event of facts.events) for (const line of eventLines(event)) console.log(line);
  }
  process.exitCode = facts.exit_code;
}

const argv = process.argv.slice(2);
const json = argv.includes('--json');
const args = argv.filter(arg => arg !== '--json');
let facts = args[0] === 'lint' ? { mode: 'lint', findings: [] } : newRun();
try {
  if (argv.length === 1 && argv[0] === '--help') {
    console.log([
      'Usage: scripts/check [--all] [--only <ids>] [--base <ref>] [--json]',
      '       scripts/check lint [--json]',
      '       scripts/check --help',
      '',
      'Default: committed changes since merge base plus staged, unstaged and untracked files.',
      '--all         Run whole checks instead of selecting affected tests.',
      '--only <ids>  Restrict to comma-separated ids; does not force selection without --all.',
      '--base <ref>  Override origin/<integration> for the merge base; no fetch.',
      '--json        Print exactly one JSON object with selection, results and timings.',
      '--help        Show this help.',
      '',
      'Exit codes:',
      '  0  Selected checks passed, gate-covered skips, or nothing selected.',
      '  1  A check failed, or lint found invalid configuration.',
      '  2  Invalid request/configuration, selector failure, or uncovered missing need.',
      ' 70  Engine unavailable or unexpected internal error.',
    ].join('\n'));
  } else {
    const schema = JSON.parse(readFileSync(new URL('./checks.schema.json', import.meta.url), 'utf8'));
    if (args.length === 1 && args[0] === 'lint') facts = lint(schema);
    else {
      if (args[0] === 'lint') throw new RequestError('Usage: scripts/check lint [--json]. Use --help.', 'usage');
      facts.request = parseRequest(args);
      await run(schema, facts);
    }
    emit(facts, json);
  }
} catch (error) {
  facts.ok = false;
  facts.exit_code = error instanceof RequestError ? 2 : 70;
  const finding = { rule: error instanceof RequestError ? error.rule : 'engine', message: error.message };
  if (facts.mode === 'lint') facts.findings.push(finding);
  else facts.events.push({ type: 'ERROR', ...finding });
  emit(facts, json);
}
