#!/usr/bin/env node
import { accessSync, appendFileSync, chmodSync, closeSync, constants, existsSync, globSync, lstatSync, mkdirSync, mkdtempSync, openSync, readFileSync, readSync, readdirSync, readlinkSync, realpathSync, renameSync, rmSync, rmdirSync, statSync, unlinkSync, writeFileSync } from 'node:fs';
import { execFileSync, fork, spawn, spawnSync } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import { delimiter, isAbsolute, join, relative, resolve, sep } from 'node:path';
import { cpus, homedir, tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

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
    for (const commandField of ['run', 'run_all', 'select']) {
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

const anyLegacyMarker = new RegExp(legacyMarkers.map(({ pattern }) => `(?:${pattern.source})`).join('|'), 'i');

function workflowFilterAt(text, index, scan) {
  scan.workflow ??= { offset: 0, end: -1, filterIndent: null, inTriggers: false };
  const state = scan.workflow;
  while (state.end < index && state.offset <= text.length) {
    const newline = text.indexOf('\n', state.offset);
    state.end = newline < 0 ? text.length : newline;
    const line = text.slice(state.offset, state.end);
    const indent = line.search(/\S/);
    const topKey = indent === 0 && !line.startsWith('#');
    if (topKey) state.inTriggers = /^["']?on["']?\s*:/.test(line);
    const key = line.match(/^(\s*)["']?paths(?:-ignore)?["']?\s*:/);
    const inlineFilter = /[,{]\s*["']?paths(?:-ignore)?["']?\s*:/.test(line);
    if (state.inTriggers && (key || inlineFilter)) state.filterIndent = indent;
    else if (!state.inTriggers || (state.filterIndent !== null && indent >= 0 && !line.trimStart().startsWith('#') && indent <= state.filterIndent)) state.filterIndent = null;
    state.offset = state.end + 1;
  }
  return state.filterIndent !== null;
}

function markerContext(kind, path, text, index, scan) {
  if (!kind) return true;
  const workflow = /^\.github\/workflows\/[^/]+\.ya?ml$/.test(path);
  if (kind === 'workflow-filter') return workflow && workflowFilterAt(text, index, scan);
  if (kind === 'ticket-check' && !/(?:^|\/)verify-erp(?:\/|$)/.test(path)) return false;
  if (kind === 'exclusion') {
    if (workflow) return workflowFilterAt(text, index, scan);
    if (/(?:^|\/)\.(?:gitignore|dockerignore|ignore|eslintignore|prettierignore)$|(?:eslint|oxlint|vitest|jest|pytest|ruff)[^/]*(?:config|\.ini|\.json|\.toml)/.test(path)) return true;
    const toml = /(?:^|\/)pyproject\.toml$/.test(path);
    const ini = /(?:^|\/)(?:setup\.cfg|tox\.ini)$/.test(path);
    if (toml || ini) {
      scan.sections ??= { pattern: /^\s*\[([^\]]+)\]/gm, current: '' };
      const sections = scan.sections;
      if (sections.next === undefined) sections.next = sections.pattern.exec(text);
      while (sections.next && sections.next.index + sections.next[0].length <= index) {
        sections.current = sections.next[0];
        sections.next = sections.pattern.exec(text);
      }
    }
    const tomlSection = scan.sections?.current ?? '';
    const testOrLintSection = toml &&
      /\[tool\.(?:pytest|ruff|black|isort|coverage|pylint|flake8|mypy)(?:[.\]]|$)/.test(tomlSection);
    const pytestSection = ini &&
      /^\s*\[(?:tool:pytest|pytest)\]\s*$/.test(tomlSection);
    if (testOrLintSection || pytestSection) return true;
  }
  if (kind === 'checks' && (path === 'scripts/check' || /^\.githooks\//.test(path))) return true;
  scan.headings ??= { pattern: /^#{1,6}\s+.*$/gm, current: '' };
  const headings = scan.headings;
  if (headings.next === undefined) headings.next = headings.pattern.exec(text);
  while (headings.next && headings.next.index + headings.next[0].length <= index) {
    headings.current = headings.next[0];
    headings.next = headings.pattern.exec(text);
  }
  const heading = headings.next && headings.next.index < index ?
    text.slice(headings.next.index, index).match(/^#{1,6}\s+.*$/m)?.[0] ?? headings.current : headings.current;
  let start = index;
  let end = index;
  for (let i = 0; i < 3; i++) {
    start = start <= 0 ? -1 : text.lastIndexOf('\n', start - 1);
    end = end < 0 ? -1 : text.indexOf('\n', end);
    if (end >= 0) end++;
  }
  const nearby = `${text.slice(start + 1, index)}\n${text.slice(index, end < 0 ? text.length : end - 1)}`;
  const context = `${heading}\n${nearby}`;
  if (kind === 'exclusion') return /\b(?:ignore[sd]?|exclud\w*|omit)\b|排除|忽略/i.test(context);
  if (kind === 'ticket-check') return /\bticket\b|工单|票据/i.test(context);
  return /\bscripts\/check\b|\bcheck(?:s|ers)?\b|检查|MMW[^\n]*(?:工单|ticket)/i.test(context);
}

function markerFindings(path) {
  let text;
  try {
    const stat = constants.O_NOFOLLOW === undefined ? lstatSync(path) : null;
    if (stat?.isDirectory()) return [];
    try {
      if (stat?.isSymbolicLink()) text = readlinkSync(path);
      else {
        const fd = openSync(path, constants.O_RDONLY | (constants.O_NOFOLLOW ?? 0));
        try {
          const prefix = Buffer.allocUnsafe(8192);
          const bytes = readSync(fd, prefix, 0, prefix.length, 0);
          if (prefix.subarray(0, bytes).includes(0)) return [];
          text = readFileSync(fd, 'utf8');
        } finally { closeSync(fd); }
      }
    } catch (error) {
      if (error.code !== 'ELOOP') throw error;
      text = readlinkSync(path);
    }
  } catch (error) {
    if (error.code === 'ENOENT' || error.code === 'EISDIR') return [];
    return [{ rule: 'tracked-read', path, message: `${JSON.stringify(path)}: cannot scan tracked file: ${error.message}` }];
  }
  if (text.includes('\0') || !anyLegacyMarker.test(text)) return [];
  const findings = [];
  for (const { marker, pattern, context } of legacyMarkers) {
    const scan = {};
    for (const match of text.matchAll(pattern)) {
      if (!markerContext(context, path, text, match.index, scan)) continue;
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
  const findings = [...integrationFindings(config), ...ciFindings(config), ...protectedFindings(config), ...templateFindings()];
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

function templateFindings() {
  return [['scripts/check', 'check'], ['.githooks/pre-commit', 'pre-commit'], ['.githooks/pre-push', 'pre-push']].flatMap(([path, template]) => {
    const expected = readFileSync(new URL(`../templates/${template}`, import.meta.url));
    try {
      if (readFileSync(path).equals(expected)) return [];
    } catch (error) { if (error.code !== 'ENOENT') throw error; }
    return [{ rule: 'template', path, message: `${path}: differs from canonical ${template} template` }];
  });
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

function newEnsure(check) {
  return { mode: 'ensure', ok: false, exit_code: 2, check, pending: [], changed: [], retained: [], findings: [] };
}

function ensure(schema, facts) {
  let config;
  try {
    config = JSON.parse(readFileSync(configPath, 'utf8'));
  } catch (error) {
    facts.findings.push({ rule: 'config-read', path: configPath, message: `${configPath}: ${error.message}` });
    return facts;
  }
  try {
    facts.findings.push(...configFindings(config, schema));
    if (!facts.findings.length) facts.findings.push(...integrationFindings(config), ...ciFindings(config), ...protectedFindings(config));
    if (facts.findings.length) return facts;
    facts.findings.push(...templateFindings());
    if (facts.findings.length) return facts;

    const actions = [];
    const plan = (kind, path, message, apply) => {
      const item = { kind, path, message };
      facts.pending.push(item);
      actions.push({ item, apply });
    };
    let hooksPath;
    try { hooksPath = git('config', '--get', 'core.hooksPath').trim(); }
    catch (error) { if (error.status !== 1) throw error; }
    if (hooksPath !== '.githooks') plan('hooks-path', 'core.hooksPath', 'set to .githooks',
      () => git('config', 'core.hooksPath', '.githooks'));
    for (const path of ['.githooks/pre-commit', '.githooks/pre-push']) {
      const mode = statSync(path).mode & 0o7777;
      if ((mode & 0o111) !== 0o111) plan('hook-executable', path, 'make executable',
        () => chmodSync(path, mode | 0o111));
    }
    const defaultHooks = resolve(git('rev-parse', '--git-common-dir').trim(), 'hooks');
    if (existsSync(defaultHooks)) for (const entry of readdirSync(defaultHooks, { withFileTypes: true })) {
      if (!entry.isFile()) continue;
      const path = relative(process.cwd(), join(defaultHooks, entry.name));
      if (readFileSync(path, 'utf8').startsWith('#!/bin/sh\n# File generated by prek: https://github.com/j178/prek\n')) {
        plan('prek-hook', path, 'remove prek-generated default hook', () => unlinkSync(path));
      }
    }
    if (!facts.check) for (const { item, apply } of actions) {
      apply();
      facts.pending.shift();
      facts.changed.push(item);
    }
    facts.exit_code = facts.pending.length ? 1 : 0;
    facts.ok = facts.exit_code === 0;
  } catch (error) {
    facts.findings.push({ rule: 'ensure', message: error.message });
    facts.exit_code = 2;
    facts.ok = false;
  }
  return facts;
}

const hash = bytes => createHash('sha256').update(bytes).digest('hex');
let loadedEngineHash;
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

function diffNames(...range) {
  return changedNames(git('diff', '--ignore-submodules=none', '--name-status', '-z', '--find-renames', ...range, '--'));
}

function newRun() {
  return {
    mode: 'run', ok: false, exit_code: 70, record_version: 1,
    request: { scope: 'changed', only: null, base: null },
    selection: [], results: [], summary: { selected: 0, passed: 0, failed: 0, skipped: 0, blocked: 0, 'internal-error': 0 },
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

async function collectChanges(config, facts, configHash) {
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
    config_hash: configHash,
    engine_hash: loadedEngineHash,
  };
  facts.identity.engine_version = facts.identity.engine_hash;
  if (facts.mode === 'push') {
    const paths = [];
    for (const range of facts.push.ranges) {
      range.base = git('merge-base', range.head, remote).trim();
      paths.push(...diffNames(range.base, range.head));
    }
    facts.changed_paths = [...new Set(paths)].sort();
    facts.identity.dirty = git('status', '--ignore-submodules=none', '--porcelain', '-z', '--untracked-files=all').length > 0;
    facts.push.dirty = facts.identity.dirty || facts.push.ranges.some(range => range.head !== facts.identity.head);
    if (facts.push.dirty) {
      facts.reuse_eligible = false;
      facts.events.push({ type: 'DIRTY' });
    }
    facts.timing.select_ms += performance.now() - start;
    return;
  }
  const ref = facts.request.base ?? remote;
  let base;
  try { base = git('merge-base', 'HEAD', ref).trim(); }
  catch (error) {
    if (!error.status) throw error;
    throw new RequestError(`Cannot find merge base with ${ref}: ${error.stderr?.toString().trim()}`);
  }
  facts.base = { ref, commit: base };
  const committed = diffNames(base, 'HEAD');
  const staged = diffNames('--cached');
  const unstaged = diffNames();
  const untracked = git('ls-files', '--others', '--exclude-standard', '-z').split('\0').filter(Boolean);
  facts.changed_paths = [...new Set([...committed, ...staged, ...unstaged, ...untracked])].sort();
  facts.identity.dirty = staged.length + unstaged.length + untracked.length > 0;
  facts.timing.select_ms += performance.now() - start;
}

function pushRun() {
  const facts = newRun();
  facts.mode = 'push';
  facts.push = {
    ranges: readFileSync(0, 'utf8').split('\n').filter(line => line.trim()).flatMap(line => {
      const [ref, head, remote_ref, remote_head] = line.trim().split(/\s+/);
      if (/^0+$/.test(head)) return [];
      if (!/^[a-f0-9]{40,64}$/.test(head) || !remote_ref || !remote_head) throw new RequestError('Invalid pre-push input');
      if (!remote_ref.startsWith('refs/heads/')) return [];
      return [{ ref, head, remote_ref, remote_head, base: null }];
    }),
    dirty: false,
  };
  return facts;
}

function audit(record) {
  const common = resolve(git('rev-parse', '--git-common-dir').trim());
  const folder = join(common, 'repo-checks', hash(git('rev-parse', '--show-toplevel').trim()).slice(0, 24));
  mkdirSync(folder, { recursive: true });
  appendFileSync(join(folder, 'audit.jsonl'), `${JSON.stringify({ ...record, time: new Date().toISOString() })}\n`);
}

async function staged() {
  if (!existsSync('prek.toml') && !existsSync('.pre-commit-config.yaml')) return 0;
  if (!commandExists('prek')) {
    console.error('Install prek: brew install prek (or uv tool install prek).');
    return 2;
  }
  const result = await supervisor({
    id: 'prek', command: 'prek run', timeout: 600, retry: 0, log: null, git_index: true,
  }, executionSlots(1), () => {});
  const attempt = result.attempts[0];
  process.stdout.write(attempt.stdout);
  process.stderr.write(attempt.stderr);
  return attempt.exit_code === 0 && !attempt.reason ? 0 : 1;
}

function newReport() {
  return {
    mode: 'report', ok: true, exit_code: 0,
    runs: { total: 0, passed: 0, failed: 0, blocked: 0, internal_error: 0 },
    bypasses: { count: 0, latest_reason: null, records: [] },
    engine_failures: { count: 0, records: [] },
    retry_recoveries: 0, slow: [], flaky: [], passed_push_commits: [], findings: [],
  };
}

function report(facts) {
  const root = resolve(git('rev-parse', '--git-common-dir').trim(), 'repo-checks');
  if (!existsSync(root)) return facts;
  const runs = [];
  const audits = [];
  for (const folder of readdirSync(root, { withFileTypes: true }).filter(entry => entry.isDirectory())) {
    const records = join(root, folder.name, 'records');
    if (existsSync(records)) for (const file of readdirSync(records).filter(name => name.endsWith('.json'))) {
      const path = join(records, file);
      const record = JSON.parse(readFileSync(path, 'utf8'));
      runs.push({ record, time: record.time ? Date.parse(record.time) : statSync(path).mtimeMs, path });
    }
    const auditPath = join(root, folder.name, 'audit.jsonl');
    if (existsSync(auditPath)) audits.push(...readFileSync(auditPath, 'utf8').split('\n').filter(Boolean).map(line => JSON.parse(line)));
  }
  runs.sort((a, b) => a.time - b.time || a.path.localeCompare(b.path));
  const cutoff = Date.now() - 14 * 24 * 60 * 60 * 1000;
  const recent = audits.filter(record => Date.parse(record.time) >= cutoff).sort((a, b) => a.time.localeCompare(b.time));
  facts.bypasses.records = recent.filter(record => record.type === 'bypass');
  facts.bypasses.count = facts.bypasses.records.length;
  facts.bypasses.latest_reason = facts.bypasses.records.at(-1)?.reason ?? null;
  facts.engine_failures.records = recent.filter(record => record.type === 'engine-failure');
  facts.engine_failures.count = facts.engine_failures.records.length;
  const samples = new Map();
  const recoveries = new Map();
  const commits = new Set();
  for (const { record, time } of runs) {
    facts.runs.total++;
    const category = { 0: 'passed', 1: 'failed', 2: 'blocked', 70: 'internal_error' }[record.exit_code];
    if (category) facts.runs[category]++;
    for (const result of record.results) {
      if (result.reused || !result.attempts.length) continue;
      if (!samples.has(result.id)) samples.set(result.id, []);
      samples.get(result.id).push({ seconds: result.seconds, timeout_s: result.timeout_s ?? 600 });
      if (time >= cutoff && result.recovered) {
        facts.retry_recoveries++;
        recoveries.set(result.id, (recoveries.get(result.id) ?? 0) + 1);
      }
    }
    if (record.mode === 'push' && record.ok && record.exit_code === 0 && !record.push.dirty &&
        record.identity && !record.identity.dirty &&
        (!record.identity_after || (!record.identity_after.dirty && record.identity_after.head === record.identity.head)) &&
        record.push.ranges.every(range => range.head === record.identity.head)) {
      for (const range of record.push.ranges) commits.add(range.head);
    }
  }
  for (const [id, history] of samples) {
    const last = history.slice(-20);
    const seconds = last.map(sample => sample.seconds).sort((a, b) => a - b);
    const p90_s = seconds[Math.ceil(seconds.length * 0.9) - 1];
    const timeout_s = last.at(-1).timeout_s;
    if (p90_s > timeout_s / 2) facts.slow.push({ id, samples: last.length, p90_s, timeout_s });
  }
  facts.slow.sort((a, b) => a.id.localeCompare(b.id));
  facts.flaky = [...recoveries].filter(([, count]) => count >= 2)
    .map(([id, count]) => ({ id, recoveries: count })).sort((a, b) => a.id.localeCompare(b.id));
  facts.passed_push_commits = [...commits].sort();
  return facts;
}

async function replay(schema, facts, args) {
  if (!json && args.length === 3 && args[1] === '--range') {
    const parts = args[2].split('..');
    if (parts.length !== 2 || parts.some(ref => !ref || ref.startsWith('-') || ref.startsWith('.'))) {
      throw new RequestError('Usage: scripts/check replay --range <base>..<head>.', 'usage');
    }
    let [base, head] = parts;
    try {
      base = git('rev-parse', '--verify', `${base}^{commit}`).trim();
      head = git('rev-parse', '--verify', `${head}^{commit}`).trim();
      facts.changed_paths = [...new Set(diffNames(base, head))].sort();
    } catch (error) { throw new RequestError(`Cannot read local replay range ${base}..${head}: ${error.message}`); }
    facts.range = { base, head };
  } else if (!json && args.length === 2 && /^[1-9]\d*$/.test(args[1])) {
    let pr;
    try {
      pr = JSON.parse(execFileSync('gh', ['pr', 'view', args[1], '--json', 'state'], {
        encoding: 'utf8', timeout: 15000, stdio: ['ignore', 'pipe', 'pipe'],
      }));
    } catch (error) { throw new RequestError(`Cannot read merged PR ${args[1]}: ${error.message}`); }
    if (pr.state !== 'MERGED') throw new RequestError(`PR ${args[1]} is not merged.`);
    try {
      const pages = JSON.parse(execFileSync('gh', [
        'api', '--paginate', '--slurp', `repos/{owner}/{repo}/pulls/${args[1]}/files`,
      ], { encoding: 'utf8', timeout: 15000, maxBuffer: 16 * 1024 * 1024, stdio: ['ignore', 'pipe', 'pipe'] }));
      facts.changed_paths = [...new Set(pages.flat().flatMap(file =>
        file.previous_filename ? [file.filename, file.previous_filename] : [file.filename]))].sort();
    } catch (error) { throw new RequestError(`Cannot read merged PR ${args[1]} files: ${error.message}`); }
  } else throw new RequestError('Usage: scripts/check replay <pr> | replay --range <base>..<head>.', 'usage');
  let config;
  try { config = JSON.parse(readFileSync(configPath, 'utf8')); }
  catch (error) { throw new RequestError(`${configPath}: ${error.message}`); }
  const findings = configFindings(config, schema);
  if (!findings.length) findings.push(...protectedFindings(config));
  if (findings.length) throw new RequestError(findings.map(finding => finding.message).join('\n'));
  await selectChecks(config, facts);
  facts.ok = true;
  facts.exit_code = 0;
}

function newSelftest() {
  return { mode: 'selftest', ok: false, exit_code: 1, assertions: [], findings: [] };
}

function selftest(facts) {
  const root = mkdtempSync(join(tmpdir(), 'repo-checks-selftest-'));
  let name = 'fixture';
  const assert = (label, ok, message) => {
    name = label;
    facts.assertions.push({ name: label, ok, ...(!ok ? { message } : {}) });
  };
  try {
    const repo = join(root, 'repo');
    const home = join(root, 'home');
    const hooks = join(root, 'hooks');
    for (const dir of [repo, home, hooks]) mkdirSync(dir);
    const env = {
      ...process.env, HOME: home, XDG_CONFIG_HOME: join(home, '.config'), XDG_CACHE_HOME: join(home, '.cache'),
      GIT_CONFIG_GLOBAL: join(home, '.gitconfig'),
      MMW_REPO_CHECKS_ENGINE: fileURLToPath(import.meta.url), GIT_TERMINAL_PROMPT: '0',
    };
    for (const key of ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR', 'MMW_CHECKS_SKIP', 'MMW_REPO_CHECKS_HOOK']) delete env[key];
    const gitFixture = (...args) => execFileSync('git', ['-c', `core.hooksPath=${hooks}`, ...args], {
      cwd: repo, env, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 15000,
    }).trim();
    const remote = join(root, 'origin.git');
    gitFixture('init', '--bare', '--template=', remote);
    gitFixture('--git-dir', remote, 'symbolic-ref', 'HEAD', 'refs/heads/main');
    gitFixture('init', '--template=', '-b', 'main');
    gitFixture('config', 'user.name', 'Repo Checks Selftest');
    gitFixture('config', 'user.email', 'selftest@example.invalid');
    gitFixture('remote', 'add', 'origin', remote);
    mkdirSync(join(repo, '.agents'));
    mkdirSync(join(repo, 'scripts'));
    mkdirSync(join(repo, 'src'));
    const checks = ['unit', 'unaffected'].map(id => ({
      id, run: `${shellQuote(process.execPath)} -e ${shellQuote(`console.log("${id} selftest output")`)}`,
      inputs: [`src/${id}.js`], tests: [], ci: false, ci_reason: 'Built-in local selftest.',
    }));
    writeFileSync(join(repo, configPath), JSON.stringify({
      integration: 'main', ci_workflow: null, test_files: [], inert: ['scripts/check'],
      affects_all: [configPath], checks, lanes: [], excluded: [],
    }));
    const entry = join(repo, 'scripts/check');
    writeFileSync(entry, readFileSync(new URL('../templates/check', import.meta.url)));
    chmodSync(entry, 0o755);
    gitFixture('add', '--all');
    gitFixture('commit', '-m', 'Selftest baseline');
    gitFixture('push', 'origin', 'main');
    writeFileSync(join(repo, 'src/unit.js'), 'selftest change\n');
    gitFixture('add', '--all');
    gitFixture('commit', '-m', 'Selftest input');
    assert('fixture', true);
    name = 'engine-run';
    const run = spawnSync(entry, ['--base', 'refs/remotes/origin/main', '--json'], {
      cwd: repo, env, encoding: 'utf8', timeout: 15000,
    });
    assert('engine-run', run.status === 0, run.error?.message ?? run.stderr + run.stdout);
    name = 'selection';
    const result = JSON.parse(run.stdout);
    assert('selection', result.selection.length === 1 && result.selection[0].check.id === 'unit',
      `Expected only unit; selected ${result.selection.map(item => item.check.id).join(', ')}`);
    assert('check-pass', result.results.length === 1 && result.results[0].id === 'unit' &&
      result.results[0].status === 'passed' && !result.results[0].reused && result.summary.passed === 1,
    'Expected one executed, passing unit check.');
    name = 'check-log';
    const log = result.results.find(item => item.id === 'unit')?.log;
    assert('check-log', Boolean(log) && readFileSync(log, 'utf8') === 'unit selftest output\n',
      'Expected unit selftest output in the check log.');
  } catch (error) {
    if (!facts.assertions.some(assertion => assertion.name === name && !assertion.ok)) {
      facts.assertions.push({ name, ok: false, message: error.message });
    }
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
  facts.ok = facts.assertions.every(assertion => assertion.ok);
  facts.exit_code = facts.ok ? 0 : 1;
  return facts;
}

function expandCommand(template, scope) {
  if (scope.kind === 'whole') return template;
  if (process.platform === 'win32' && /\{(?:files|tests)\}/.test(template)) {
    throw new RequestError('Filename interpolation requires a POSIX shell host; use whole-check commands on Windows.');
  }
  return template.replace(/\{(files|tests)\}/g, (_, list) => scope[list].map(shellQuote).join(' '));
}

async function selectorTests(check, files, facts) {
  const command = expandCommand(check.select, { kind: 'narrowed', files, tests: [] });
  const start = performance.now();
  let result;
  try {
    const supervised = await supervisor({
      id: check.id, command, timeout: check.timeout_s ?? 600, retry: 0, log: null,
    }, executionSlots(1), event => addEvent(facts, event));
    result = supervised.attempts[0];
  } finally {
    facts.timing.selector_ms += performance.now() - start;
  }
  if (result.reason) throw new RequestError(`Selector ${check.id}: ${result.reason}`);
  if (result.exit_code !== 0) throw new RequestError(`Selector ${check.id} failed (${result.exit_code ?? result.signal}): ${result.stderr.trim()}`);
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

async function selectChecks(config, facts) {
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
    facts.selection = [];
    for (const check of config.checks) {
      if (facts.request.only && !facts.request.only.includes(check.id)) continue;
      if (facts.request.scope === 'all' || widened) {
        facts.selection.push({ check, reason: facts.request.scope === 'all' ? '--all' : widened, scope: { kind: 'whole' } });
        continue;
      }
      const match = patternsMatch(check.inputs);
      const path = facts.changed_paths.find(match);
      if (path) {
        facts.selection.push({ check, reason: `inputs ${path}`, scope: { kind: 'whole' } });
        continue;
      }
      const files = facts.changed_paths.filter(patternsMatch(check.sources ?? []));
      if (!files.length) continue;
      const tests = await selectorTests(check, files, facts);
      if (tests.length) facts.selection.push({ check, reason: `sources ${files[0]}`, scope: { kind: 'narrowed', files, tests } });
    }
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
  writeFileSync(join(logs, '.active.json'), JSON.stringify({ pid: process.pid, start: processStart(process.pid) }));
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

function killTree(child) {
  if (!child.pid) return;
  if (process.platform === 'win32') {
    const result = spawnSync('taskkill', ['/PID', String(child.pid), '/T', '/F'], { stdio: 'ignore', timeout: 5000 });
    if (result.error) throw result.error;
  } else {
    try { process.kill(-child.pid, 'SIGKILL'); }
    catch (error) { if (error.code !== 'ESRCH') throw error; }
  }
}

let activeCommand = null;

async function commandProcess(command, timeout, log, gitIndex) {
  const fd = log ? openSync(log, 'a') : null;
  const start = performance.now();
  const env = { ...process.env };
  delete env.MMW_REPO_CHECKS_HOOK;
  delete env.GIT_DIR;
  delete env.GIT_WORK_TREE;
  if (!gitIndex) delete env.GIT_INDEX_FILE;
  delete env.GIT_COMMON_DIR;
  let child;
  try {
    child = spawn(command, {
      shell: true, detached: process.platform !== 'win32',
      stdio: ['ignore', fd ?? 'pipe', fd ?? 'pipe'],
      env,
    });
  } finally { if (fd !== null) closeSync(fd); }
  let reason = null;
  let failure = null;
  let stdout = '';
  let stderr = '';
  let size = 0;
  const stop = () => {
    try { killTree(child); }
    catch (error) { if (error.code !== 'ESRCH') failure ??= error; }
  };
  activeCommand = stop;
  const collect = stream => bytes => {
    size += bytes.length;
    if (size > 16 * 1024 * 1024) { reason = 'output exceeds 16 MiB'; stop(); }
    else if (stream === 'stdout') stdout += bytes;
    else stderr += bytes;
  };
  child.stdout?.on('data', collect('stdout'));
  child.stderr?.on('data', collect('stderr'));
  const closed = new Promise(resolveClose => child.once('close', resolveClose));
  const exited = new Promise(resolveExit => {
    child.once('error', error => { failure ??= error; resolveExit({ code: null, signal: null }); });
    child.once('exit', (code, signal) => resolveExit({ code, signal }));
  });
  const timer = setTimeout(() => { reason = 'timeout'; stop(); }, Math.max(1, timeout * 1000 - (performance.now() - start)));
  const { code, signal } = await exited;
  clearTimeout(timer);
  await closed;
  activeCommand = null;
  if (failure) throw failure;
  if (reason && log) appendFileSync(log, `${reason}\n`);
  return { exit_code: code, signal, seconds: (performance.now() - start) / 1000, log, reason, stdout, stderr };
}

function sendWorker(message) {
  if (process.connected) process.send(message, () => {});
}

function processStart(pid) {
  if (process.platform === 'linux') {
    try {
      const stat = readFileSync(`/proc/${pid}/stat`, 'utf8');
      return stat.slice(stat.lastIndexOf(')') + 2).split(' ')[19];
    } catch (error) { if (error.code === 'ENOENT') return null; throw error; }
  }
  const probe = process.platform === 'win32'
    ? spawnSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', `(Get-Process -Id ${Number(pid)} -ErrorAction SilentlyContinue).StartTime.ToUniversalTime().Ticks`], { encoding: 'utf8', timeout: 5000 })
    : spawnSync('ps', ['-p', String(pid), '-o', 'lstart='], { encoding: 'utf8', timeout: 2000 });
  if (probe.error) throw probe.error;
  return probe.status === 0 && probe.stdout.trim() ? probe.stdout.trim() : null;
}

function liveOwner(owner) {
  return Boolean(owner?.start && processStart(owner.pid) === owner.start);
}

function cacheLocks() {
  const root = process.platform === 'darwin' ? join(homedir(), 'Library', 'Caches')
    : process.platform === 'win32' ? process.env.LOCALAPPDATA ?? join(homedir(), 'AppData', 'Local')
      : process.env.XDG_CACHE_HOME ?? join(homedir(), '.cache');
  const folder = join(root, 'repo-checks', 'locks');
  mkdirSync(folder, { recursive: true });
  return folder;
}

function removeToken(directory, token) {
  try { if (token) unlinkSync(join(directory, token)); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  try { rmdirSync(directory); }
  catch (error) { if (!['ENOENT', 'ENOTEMPTY', 'EEXIST'].includes(error.code)) throw error; }
}

const sleep = ms => new Promise(resolveSleep => setTimeout(resolveSleep, ms));

async function acquireLock(name, timeout, cancelled) {
  if (!name) return { release() {} };
  const root = cacheLocks();
  const canonical = join(root, hash(name));
  const nonce = randomUUID();
  const token = `${nonce}.json`;
  const candidate = join(root, `.${nonce}`);
  const owner = { pid: process.pid, start: processStart(process.pid), nonce, name };
  mkdirSync(candidate);
  writeFileSync(join(candidate, token), JSON.stringify(owner), { flag: 'wx' });
  const deadline = performance.now() + timeout * 1000;
  let waited = false;
  try {
    for (;;) {
      if (cancelled()) return { release() {} };
      try {
        renameSync(candidate, canonical);
        return { release: () => removeToken(canonical, token) };
      } catch (error) {
        if (!['EEXIST', 'ENOTEMPTY', 'EPERM', 'EACCES'].includes(error.code)) throw error;
      }
      let observed = null;
      try {
        const tokens = readdirSync(canonical);
        if (!tokens.length) { removeToken(canonical, null); continue; }
        const observedToken = tokens[0];
        observed = JSON.parse(readFileSync(join(canonical, observedToken), 'utf8'));
        if (!liveOwner(observed)) { removeToken(canonical, observedToken); continue; }
      } catch (error) { if (error.code === 'ENOENT') continue; throw error; }
      if (!waited) { sendWorker({ type: 'event', event: { type: 'WAIT', lock: name, holder: observed } }); waited = true; }
      if (performance.now() >= deadline) return {
        blocked: true, holder: observed, release() {},
        reason: `lock ${name} timed out; holder pid=${observed.pid} start=${observed.start}`,
      };
      await sleep(Math.min(100, Math.max(1, deadline - performance.now())));
    }
  } finally {
    removeToken(candidate, token);
  }
}

function readOptionalJson(path) {
  try { return JSON.parse(readFileSync(path, 'utf8')); }
  catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}

function preparationHash(prepare) {
  const parts = [prepare.run];
  for (const pattern of prepare.stamps) {
    const paths = globSync(pattern, { exclude: ['.git/**'] }).sort();
    parts.push(JSON.stringify([pattern, paths]));
    for (const path of paths) {
      const stat = lstatSync(path);
      parts.push(JSON.stringify([path, stat.isSymbolicLink() ? 'link' : stat.isDirectory() ? 'directory' : 'file']));
      if (stat.isSymbolicLink()) parts.push(hash(readlinkSync(path)), hash(readFileSync(path)));
      else if (stat.isFile()) parts.push(hash(readFileSync(path)));
    }
  }
  return hash(JSON.stringify(parts));
}

async function worker(task) {
  let started = false;
  let cancelled = false;
  let cancelGrant;
  const granted = new Promise(resolveGrant => {
    cancelGrant = resolveGrant;
    process.once('message', () => { started = true; resolveGrant(); });
  });
  const abandon = () => { cancelled = true; if (activeCommand) activeCommand(); };
  process.on('SIGINT', abandon);
  process.on('SIGTERM', abandon);
  process.once('disconnect', () => { if (!started) { cancelled = true; cancelGrant(); } });
  const lease = await acquireLock(task.lock, task.timeout, () => cancelled);
  if (cancelled) {
    lease.release();
    return;
  }
  if (lease.blocked) {
    sendWorker({ type: 'result', result: { blocked: true, reason: lease.reason, holder: lease.holder } });
    if (process.connected) process.disconnect();
    return;
  }
  let heartbeat;
  try {
    let stamp;
    if (task.prepare) {
      stamp = preparationHash(task.prepare);
      const previous = readOptionalJson(task.stamp_file);
      if (previous?.hash === stamp && task.paths.every(path => existsSync(path))) {
        sendWorker({ type: 'result', result: { stamp, prepared: false, attempts: [], seconds: 0 } });
        return;
      }
    }
    sendWorker({ type: 'ready' });
    await granted;
    if (cancelled) return;
    const start = performance.now();
    heartbeat = setInterval(() => sendWorker({
      type: 'event', event: { type: 'RUNNING', id: task.id, seconds: (performance.now() - start) / 1000 },
    }), 19000);
    const attempts = [];
    for (let i = 0; i <= task.retry && !cancelled; i++) {
      const attempt = await commandProcess(task.command, task.timeout, task.log, task.git_index);
      attempts.push(attempt);
      if (attempt.exit_code === 0 && !attempt.reason) break;
    }
    if (task.prepare && attempts.at(-1).exit_code === 0 && !attempts.at(-1).reason) {
      const temporary = `${task.stamp_file}.${randomUUID()}.tmp`;
      writeFileSync(temporary, JSON.stringify({ hash: stamp }));
      renameSync(temporary, task.stamp_file);
    } else stamp = null;
    sendWorker({ type: 'result', result: { attempts, seconds: (performance.now() - start) / 1000, stamp, prepared: Boolean(task.prepare) } });
  } finally {
    clearInterval(heartbeat);
    lease.release();
    if (process.connected) process.disconnect();
  }
}

const runningChecks = new Set();

function supervisor(task, slot, event) {
  return new Promise((resolveTask, reject) => {
    const child = fork(fileURLToPath(import.meta.url), [], { detached: process.platform !== 'win32', stdio: ['ignore', 'ignore', 'ignore', 'ipc'] });
    runningChecks.add(child);
    let release = null;
    let result = null;
    child.on('message', message => {
      Promise.resolve().then(async () => {
        if (message.type === 'ready') {
          release = await slot();
          if (child.connected) child.send({ type: 'go' });
          else { release(); release = null; }
        } else if (message.type === 'event') event(message.event);
        else if (message.type === 'error') result = { error: message.message };
        else if (message.type === 'result') result = message.result;
      }).catch(error => { result = { error: error.message }; if (child.connected) child.disconnect(); });
    });
    child.once('error', error => { runningChecks.delete(child); reject(error); });
    child.once('exit', (code, signal) => {
      runningChecks.delete(child);
      release?.();
      if (!result || result.error || code !== 0) reject(new Error(result?.error ?? `Command supervisor exited without a successful result (${code ?? signal})`));
      else resolveTask(result);
    });
    child.send({ type: 'task', task });
  });
}

function executionSlots(cap) {
  let running = 0;
  const waiting = [];
  const grant = resolveSlot => {
    running++;
    resolveSlot(() => {
      running--;
      if (waiting.length) grant(waiting.shift());
    });
  };
  return () => new Promise(resolveSlot => {
    if (running < cap) grant(resolveSlot);
    else waiting.push(resolveSlot);
  });
}

const streamed = new WeakMap();
function streamFacts(facts) {
  const previous = streamed.get(facts) ?? 0;
  for (const event of facts.events.slice(previous)) {
    if (!json) for (const line of eventLines(event)) console.log(line);
    else if (['WAIT', 'RUNNING'].includes(event.type)) for (const line of eventLines(event)) console.error(line);
  }
  streamed.set(facts, facts.events.length);
}
function addEvent(facts, event) {
  facts.events.push(event);
  streamFacts(facts);
}

function currentIdentity() {
  return {
    head: git('rev-parse', 'HEAD').trim(),
    tree: git('rev-parse', 'HEAD^{tree}').trim(),
    config_hash: existsSync(configPath) ? hash(readFileSync(configPath)) : null,
    engine_hash: hash(readFileSync(new URL(import.meta.url))),
    dirty: git('status', '--ignore-submodules=none', '--porcelain', '-z', '--untracked-files=all').length > 0,
  };
}

function checkIdentity(facts) {
  const current = currentIdentity();
  facts.identity_after = current;
  const stable = !facts.identity.dirty && !current.dirty &&
    ['head', 'tree', 'config_hash', 'engine_hash'].every(key => current[key] === facts.identity[key]);
  facts.reuse_eligible = facts.reuse_eligible !== false && stable;
  return facts.reuse_eligible;
}

function reuseKey(id, command, identity) {
  return { id, command, tree: identity.tree, config_hash: identity.config_hash, engine_hash: identity.engine_hash };
}

function findReuse(facts, check, scope, command) {
  if (!checkIdentity(facts)) return null;
  const wholeCommand = check.run_all ?? check.run;
  const records = join(facts.storage.worktree_dir, 'records');
  for (const file of readdirSync(records).filter(name => name.endsWith('.json')).sort().reverse()) {
    const record = readOptionalJson(join(records, file));
    if (!record || record.record_version !== 1 || !record.reuse_eligible || record.preparation_stamp !== facts.preparation_stamp) continue;
    for (const result of record.results) {
      if (result.id !== check.id || result.status !== 'passed' || !result.reusable) continue;
      const whole = result.coverage?.kind === 'whole';
      if (scope.kind === 'whole' && !whole) continue;
      if (!whole && JSON.stringify(scope) !== JSON.stringify(result.coverage)) continue;
      const key = reuseKey(check.id, whole ? wholeCommand : command, facts.identity);
      if (JSON.stringify(result.reuse_key) === JSON.stringify(key)) return { result, record: join(records, file) };
    }
  }
  return null;
}

async function execute(facts) {
  const slot = executionSlots(Math.max(1, Math.min(4, Math.floor(cpus().length / 2))));
  const settled = await Promise.allSettled(facts.selection.map(async ({ check, scope }) => {
    const command = expandCommand(scope.kind === 'whole' ? check.run_all ?? check.run : check.run, scope);
    const missing = (check.needs ?? []).filter(need => !needSatisfied(need));
    if (missing.length) {
      const outcome = {
        id: check.id, status: 'skipped', reason: `needs ${missing.join(', ')}`,
        missing_needs: missing, gate_runs_it: check.ci,
        ci: check.ci, ci_reason: check.ci_reason ?? null,
        command, scope, seconds: 0, log: null, tail: [], attempts: [],
      };
      addEvent(facts, { type: 'SKIP', ...outcome });
      return outcome;
    }
    const log = join(facts.storage.logs, `${hash(check.id).slice(0, 24)}.log`);
    const previous = findReuse(facts, check, scope, command);
    if (previous && checkIdentity(facts)) {
      const prior = previous.result;
      let bytes;
      try { bytes = readFileSync(prior.log); }
      catch (error) { if (error.code !== 'ENOENT') throw error; bytes = `${prior.tail.join('\n')}\n`; }
      writeFileSync(log, bytes);
      const outcome = {
        id: check.id, status: 'passed', seconds: 0, command, scope, log, tail: prior.tail,
        ci: check.ci, ci_reason: check.ci_reason ?? null, attempts: [], recovered: false,
        reused: true, reusable: true, reuse_key: prior.reuse_key, coverage: prior.coverage,
        reused_from: { record: previous.record, coverage: prior.coverage, key: prior.reuse_key },
      };
      addEvent(facts, { type: 'PASS', ...outcome });
      return outcome;
    }
    const result = await supervisor({ id: check.id, command, log, lock: check.lock, timeout: check.timeout_s ?? 600, retry: check.retry ?? 0 }, slot, event => addEvent(facts, event));
    if (result.blocked) {
      const outcome = { id: check.id, status: 'blocked', reason: result.reason, holder: result.holder,
        command, scope, seconds: 0, log: null, tail: [], attempts: [], ci: check.ci, ci_reason: check.ci_reason ?? null };
      addEvent(facts, { type: 'BLOCKED', ...outcome });
      return outcome;
    }
    const last = result.attempts.at(-1);
    const status = last.exit_code === 0 && !last.reason ? 'passed' : 'failed';
    let tail;
    try { tail = readFileSync(log, 'utf8').replace(/\r\n/g, '\n').replace(/\n$/, '').split('\n').slice(-40); }
    catch (error) { return internalOutcome(facts, { check, scope }, error, { log, ...result }); }
    const outcome = {
      id: check.id, status, seconds: result.seconds, command, scope, log, tail, reason: last.reason,
      timeout_s: check.timeout_s ?? 600,
      ci: check.ci, ci_reason: check.ci_reason ?? null,
      attempts: result.attempts, recovered: status === 'passed' && result.attempts.length > 1,
      reused: false, reusable: checkIdentity(facts) && status === 'passed',
      reuse_key: reuseKey(check.id, command, facts.identity), coverage: scope,
    };
    addEvent(facts, { type: status === 'passed' ? 'PASS' : 'FAIL', ...outcome });
    return outcome;
  }));
  facts.results = settled.map((outcome, index) => outcome.status === 'fulfilled'
    ? outcome.value : internalOutcome(facts, facts.selection[index], outcome.reason));
}

function internalOutcome(facts, { check, scope }, error, execution = {}) {
  const outcome = {
    id: check.id, status: 'internal-error', reason: error.message,
    command: expandCommand(scope.kind === 'whole' ? check.run_all ?? check.run : check.run, scope),
    scope, seconds: execution.seconds ?? 0,
    log: execution.log ?? join(facts.storage.logs, `${hash(check.id).slice(0, 24)}.log`),
    tail: [], attempts: execution.attempts ?? [], reusable: false,
    ci: check.ci, ci_reason: check.ci_reason ?? null,
  };
  addEvent(facts, { type: 'ERROR', rule: 'engine', message: `${check.id}: ${error.message}`, ...outcome });
  return outcome;
}

async function prepare(config, facts) {
  if (!config.prepare || !facts.selection.length) return true;
  const log = join(facts.storage.logs, 'prepare.log');
  const result = await supervisor({
    id: 'prepare', command: config.prepare.run, prepare: config.prepare,
    stamp_file: join(facts.storage.worktree_dir, 'prepare.json'),
    paths: facts.selection.flatMap(({ check }) => (check.needs ?? []).filter(need => need.startsWith('path:')).map(need => need.slice(5))),
    lock: `prepare:${facts.identity.worktree}`, timeout: 600, retry: 0, log,
  }, executionSlots(1), event => addEvent(facts, event));
  facts.preparation_stamp = result.stamp ?? null;
  facts.preparation = { ...result, log: result.prepared ? log : null };
  if (result.stamp) return true;
  const tail = existsSync(log) ? readFileSync(log, 'utf8').trimEnd().split('\n').slice(-40) : [];
  facts.results = facts.selection.map(({ check, scope }) => {
    const outcome = {
      id: check.id, status: 'blocked', reason: result.reason ?? 'preparation failed',
      scope, command: expandCommand(scope.kind === 'whole' ? check.run_all ?? check.run : check.run, scope),
      log: existsSync(log) ? log : null, tail, attempts: [], seconds: 0,
      ci: check.ci, ci_reason: check.ci_reason ?? null,
    };
    addEvent(facts, { type: 'BLOCKED', ...outcome });
    return outcome;
  });
  return false;
}

function finishRun(facts) {
  let stable = false;
  try { stable = checkIdentity(facts); }
  catch (error) {
    facts.reuse_eligible = false;
    facts.events.push({ type: 'ERROR', rule: 'engine', message: error.message });
  }
  if (!stable) {
    for (const result of facts.results) result.reusable = false;
    for (const event of facts.events) if (event.type === 'PASS') event.reusable = false;
  }
  facts.summary.selected = facts.selection.length;
  for (const result of facts.results) facts.summary[result.status]++;
  const uncovered = facts.results.some(result => result.status === 'skipped' && !result.gate_runs_it);
  facts.exit_code = facts.summary['internal-error'] || facts.events.some(event => event.type === 'ERROR' && event.rule === 'engine')
    ? 70 : uncovered || facts.summary.blocked ? 2 : facts.summary.failed ? 1 : 0;
  facts.ok = facts.exit_code === 0;
  facts.events.push(...facts.lanes.map(lane => ({ type: 'LANE', ...lane })));
  facts.events.push({ type: 'SUMMARY', ...facts.summary });
  const temporary = `${facts.storage.record}.tmp`;
  writeFileSync(temporary, `${JSON.stringify(facts)}\n`);
  renameSync(temporary, facts.storage.record);
  writeFileSync(join(facts.storage.logs, '.completed.json'), JSON.stringify({ time: Date.now() }));
  unlinkSync(join(facts.storage.logs, '.active.json'));
  retainRuns(facts.storage.worktree_dir);
}

function retainRuns(folder) {
  const records = join(folder, 'records');
  const completed = [];
  for (const file of readdirSync(records).filter(name => name.endsWith('.json'))) {
    const path = join(records, file);
    try { completed.push({ path, time: statSync(path).mtimeMs }); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  completed.sort((a, b) => b.time - a.time || b.path.localeCompare(a.path));
  for (const { path } of completed.slice(50)) {
    try { unlinkSync(path); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  const logs = join(folder, 'logs');
  const sets = [];
  for (const entry of readdirSync(logs)) {
    const path = join(logs, entry);
    try {
      const names = readdirSync(path);
      const active = names.filter(name => name.endsWith('.active.json')).some(name => liveOwner(readOptionalJson(join(path, name))));
      if (!active) sets.push({ path, time: readOptionalJson(join(path, '.completed.json'))?.time ?? statSync(path).mtimeMs });
    } catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  sets.sort((a, b) => b.time - a.time || b.path.localeCompare(a.path));
  for (const { path } of sets.slice(20)) rmSync(path, { recursive: true, force: true });
}

async function run(schema, facts) {
  facts.time = new Date().toISOString();
  let config;
  let configBytes;
  const source = facts.mode === 'push' ? `HEAD:${configPath}` : configPath;
  try {
    configBytes = facts.mode === 'push' ? git('show', source) : readFileSync(configPath);
    config = JSON.parse(configBytes);
  } catch (error) { throw new RequestError(`${source}: ${error.message}`); }
  const findings = [...configFindings(config, schema)];
  if (findings.length) throw new RequestError(findings.map(x => x.message).join('\n'));
  findings.push(...protectedFindings(config));
  if (findings.length) throw new RequestError(findings.map(x => x.message).join('\n'));
  for (const id of facts.request.only ?? []) {
    if (!config.checks.some(check => check.id === id)) throw new RequestError(`Unknown check id ${JSON.stringify(id)}`, 'usage');
  }
  await collectChanges(config, facts, hash(configBytes));
  await selectChecks(config, facts);
  facts.lanes = config.lanes;
  runStorage(facts);
  streamFacts(facts);
  try {
    if (await prepare(config, facts)) await execute(facts);
  } catch (error) {
    facts.results = facts.selection.map(selected => internalOutcome(facts, selected, error));
  }
}

function eventLines(event) {
  const { type } = event;
  if (type === 'DIRTY') return ['DIRTY'];
  if (type === 'SELECT') return [`SELECT ${event.id} ${event.reason}`];
  if (type === 'BASE') return [`BASE ${event.reason}`];
  if (type === 'UNCLASSIFIED') return [`UNCLASSIFIED ${event.path}`];
  if (type === 'WIDEN') return [`WIDEN ${event.reason}`];
  if (type === 'SKIP') return [`SKIP ${event.id} ${event.reason}${event.gate_runs_it ? ' (gate runs it)' : ''}`];
  if (type === 'LANE') return [`not run here ${event.id} ${event.kind}: ${event.reason}; run_by=${event.run_by}`];
  if (type === 'PASS') return [`PASS ${event.id} ${event.seconds.toFixed(3)}s${event.reused ? ' (reused)' : event.recovered ? ' (recovered on retry)' : ''}`];
  if (type === 'RUNNING') return [`RUNNING ${event.id} ${event.seconds.toFixed(3)}s`];
  if (type === 'WAIT') return [`WAIT ${event.lock}`];
  if (type === 'BLOCKED') return [`BLOCKED ${event.id} ${event.reason}${event.log ? ` log=${event.log}` : ''}`, ...event.tail];
  if (type === 'FAIL') return [`FAIL ${event.id} ${event.seconds.toFixed(3)}s log=${event.log}`, ...event.tail];
  if (type === 'SUMMARY') return [event.selected === 0 ? 'SUMMARY nothing selected' :
    `SUMMARY ${event.selected} selected, ${event.passed} passed, ${event.failed} failed, ${event.skipped + event.blocked} skipped`];
  if (type === 'ERROR') return [`${event.rule.toUpperCase()} ${event.message}`];
  throw new Error(`Unknown event ${type}`);
}

function emit(facts, json) {
  if (interrupted) return;
  if (emitted) { process.exitCode = facts.exit_code; return; }
  emitted = true;
  if (json) console.log(JSON.stringify(facts));
  else if (facts.mode === 'lint') {
    if (facts.ok) console.log('LINT clean');
    else for (const finding of facts.findings) console.log(`LINT ${finding.rule} ${finding.message}`);
  } else if (facts.mode === 'ensure') {
    for (const item of facts.pending) console.log(`PENDING ${item.path}: ${item.message}`);
    for (const item of facts.changed) console.log(`CHANGED ${item.path}: ${item.message}`);
    for (const finding of facts.findings) console.log(`ENSURE ${finding.rule} ${finding.message}`);
  } else if (facts.mode === 'bypass') {
    console.log(`SKIPPED BY REASON ${facts.reason}`);
  } else if (facts.mode === 'report') {
    console.log(`RUNS ${facts.runs.total} total, ${facts.runs.passed} passed, ${facts.runs.failed} failed, ${facts.runs.blocked} blocked, ${facts.runs.internal_error} internal errors`);
    console.log(`BYPASSES ${facts.bypasses.count} in 14 days; latest reason: ${facts.bypasses.latest_reason ?? 'none'}`);
    for (const record of facts.bypasses.records) console.log(`BYPASS ${record.time} ${record.hook}: ${record.reason}`);
    console.log(`ENGINE_FAILURES ${facts.engine_failures.count} in 14 days`);
    console.log(`RETRY_RECOVERIES ${facts.retry_recoveries} in 14 days`);
    console.log('SLOW_THRESHOLD nearest-rank p90 of last 20 executions > half effective timeout (default 600s)');
    console.log('FLAKY_THRESHOLD at least 2 retry recoveries in 14 days');
    for (const check of facts.slow) console.log(`SLOW ${check.id} p90=${check.p90_s}s over last ${check.samples} executions > half timeout ${check.timeout_s}s`);
    for (const check of facts.flaky) console.log(`FLAKY ${check.id} ${check.recoveries} recoveries in 14 days (threshold 2)`);
    for (const commit of facts.passed_push_commits) console.log(`PASSED_PUSH ${commit}`);
    for (const finding of facts.findings) console.log(`REPORT ${finding.rule} ${finding.message}`);
  } else if (facts.mode === 'selftest') {
    for (const assertion of facts.assertions) console.log(`SELFTEST ${assertion.ok ? 'PASS' : 'FAIL'} ${assertion.name}${assertion.message ? `: ${assertion.message}` : ''}`);
    for (const finding of facts.findings) console.log(`SELFTEST ${finding.rule} ${finding.message}`);
  } else if (facts.mode === 'replay') {
    streamFacts(facts);
    if (facts.ok) console.log(facts.selection.length ? `SUMMARY ${facts.selection.length} selected (replay; no checks run)` : 'SUMMARY nothing selected');
  } else {
    streamFacts(facts);
  }
  process.exitCode = facts.exit_code;
}

const argv = process.argv.slice(2);
const json = argv.includes('--json');
const args = argv.filter(arg => arg !== '--json');
let facts = args[0] === 'lint' ? { mode: 'lint', findings: [] } :
  args[0] === 'ensure' ? newEnsure(args.includes('--check')) :
    args[0] === 'report' ? newReport() : args[0] === 'selftest' ? newSelftest() : newRun();
if (args[0] === 'replay') facts.mode = 'replay';
let emitted = false;
let interrupted = false;
function unexpected(error) {
  const message = error instanceof Error ? error.message : String(error);
  if (typeof process.send === 'function') {
    sendWorker({ type: 'error', message });
    process.exitCode = 70;
    if (process.connected) process.disconnect();
    return;
  }
  facts.ok = false;
  facts.exit_code = facts.mode === 'selftest' ? 1 : 70;
  if (facts.findings) facts.findings.push({ rule: 'engine', message });
  else facts.events.push({ type: 'ERROR', rule: 'engine', message });
  process.exitCode = facts.exit_code;
}
function finalOutput() {
  process.once('beforeExit', () => {
    try { if (facts.storage) finishRun(facts); }
    catch (error) { unexpected(error); }
    emit(facts, json);
  });
}
function interrupt(signal) {
  if (interrupted) return;
  interrupted = true;
  const code = signal === 'SIGINT' ? 130 : 143;
  process.exitCode = code;
  for (const child of runningChecks) child.kill(signal);
  const deadline = Date.now() + 5000;
  const wait = () => {
    if (runningChecks.size && Date.now() < deadline) setTimeout(wait, 25);
    else process.exit(code);
  };
  wait();
}
process.on('uncaughtException', unexpected);
process.on('unhandledRejection', unexpected);
for (const stream of [process.stdout, process.stderr]) stream.on('error', error => {
  if (error.code !== 'EPIPE') unexpected(error);
});
if (typeof process.send === 'function' && args.length === 0) {
  process.once('message', async ({ task }) => {
    try {
      loadedEngineHash = hash(readFileSync(new URL(import.meta.url)));
      await worker(task);
    } catch (error) { unexpected(error); }
  });
} else try {
  process.on('SIGINT', () => interrupt('SIGINT'));
  process.on('SIGTERM', () => interrupt('SIGTERM'));
  loadedEngineHash = hash(readFileSync(new URL(import.meta.url)));
  if (argv.length === 1 && argv[0] === '--help') {
    console.log([
      'Usage: scripts/check [--all] [--only <ids>] [--base <ref>] [--json]',
      '       scripts/check lint [--json]',
      '       scripts/check ensure [--check] [--json]',
      '       scripts/check report | selftest [--json]',
      '       scripts/check replay <pr> | replay --range <base>..<head>',
      '       scripts/check --staged | --push [--json]',
      '       scripts/check --help',
      '',
      'Default: committed changes since merge base plus staged, unstaged and untracked files.',
      '--all         Run whole checks instead of selecting affected tests.',
      '--only <ids>  Restrict to comma-separated ids; does not force selection without --all.',
      '--base <ref>  Override origin/<integration> for the merge base; no fetch.',
      '--json        Print facts for run, lint, ensure, report or selftest.',
      '--check       With ensure, report pending repairs without changing anything.',
      '--help        Show this help.',
      '--staged      Run prek on staged files when a prek config exists.',
      '--push        Select committed pre-push stdin ranges only; DIRTY disables reuse.',
      'report        Read retained history across worktrees; never run checks or fetch.',
      'replay        Select from a merged PR or local range; never prepare or run checks.',
      'selftest      Prove this engine with a temporary Git fixture.',
      'Filename interpolation requires a POSIX shell host.',
      '',
      'Exit codes:',
      '  0  Checks passed, gate-covered skips, nothing selected, or ensure done.',
      '  1  A check/selftest failed, lint found invalid configuration, or ensure --check has pending repairs.',
      '  2  Invalid request/configuration, selector failure, uncovered missing need, or ensure cannot repair.',
      ' 70  Engine unavailable or unexpected internal error.',
      '130  Interrupted by SIGINT.  143  Terminated by SIGTERM.',
    ].join('\n'));
  } else if (args[0] === 'report' || args[0] === 'selftest') {
    if (args.length !== 1) throw new RequestError(`Usage: scripts/check ${args[0]} [--json]. Use --help.`, 'usage');
    facts = args[0] === 'report' ? report(facts) : selftest(facts);
    finalOutput();
  } else if (process.env.MMW_CHECKS_SKIP?.trim() && args[0] !== 'replay') {
    const reason = process.env.MMW_CHECKS_SKIP;
    const hook = process.env.MMW_REPO_CHECKS_HOOK ?? (args[0] === '--staged' ? 'pre-commit' : args[0] === '--push' ? 'pre-push' : 'manual');
    audit({ type: 'bypass', reason, hook });
    facts = { mode: 'bypass', ok: true, exit_code: 0, reason, hook };
    emit(facts, json);
  } else if (args.length === 1 && args[0] === '--staged') {
    process.exitCode = await staged();
  } else if (args.length === 1 && args[0] === '--push') {
    facts = pushRun();
    if (facts.push.ranges.length) {
      const schema = JSON.parse(readFileSync(new URL('./checks.schema.json', import.meta.url), 'utf8'));
      await run(schema, facts);
    } else {
      facts.changed_paths = [];
      facts.ok = true;
      facts.exit_code = 0;
      facts.events.push({ type: 'SUMMARY', ...facts.summary });
    }
    finalOutput();
  } else {
    const schema = JSON.parse(readFileSync(new URL('./checks.schema.json', import.meta.url), 'utf8'));
    if (args[0] === 'replay') await replay(schema, facts, args);
    else if (args.length === 1 && args[0] === 'lint') facts = lint(schema);
    else if (args[0] === 'ensure') {
      if (!(args.length === 1 || (args.length === 2 && args[1] === '--check'))) {
        throw new RequestError('Usage: scripts/check ensure [--check] [--json]. Use --help.', 'usage');
      }
      facts = ensure(schema, facts);
    } else {
      if (args[0] === 'lint') throw new RequestError('Usage: scripts/check lint [--json]. Use --help.', 'usage');
      facts.request = parseRequest(args);
      await run(schema, facts);
    }
    finalOutput();
  }
} catch (error) {
  facts.ok = false;
  facts.exit_code = error instanceof RequestError ? 2 : facts.mode === 'selftest' ? 1 : 70;
  const finding = { rule: error instanceof RequestError ? error.rule : 'engine', message: error.message };
  if (facts.findings) facts.findings.push(finding);
  else facts.events.push({ type: 'ERROR', ...finding });
  finalOutput();
}
