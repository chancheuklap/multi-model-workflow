#!/usr/bin/env node
import { lstatSync, readFileSync, readlinkSync } from 'node:fs';
import { execFileSync } from 'node:child_process';

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

function emit(facts, json) {
  if (json) console.log(JSON.stringify(facts));
  else if (facts.ok) console.log('LINT clean');
  else for (const finding of facts.findings) console.log(`LINT ${finding.rule} ${finding.message}`);
  process.exitCode = facts.exit_code;
}

const argv = process.argv.slice(2);
const json = argv.includes('--json');
const args = argv.filter(arg => arg !== '--json');
try {
  if (argv.length === 1 && argv[0] === '--help') {
    console.log('Usage: scripts/check lint [--json]\n       scripts/check --help\n\nExit codes: 0 clean, 1 findings, 2 unreadable config or usage, 70 engine error.');
  } else if (args.length !== 1 || args[0] !== 'lint') {
    emit({ mode: 'lint', ok: false, exit_code: 2, findings: [{
      rule: 'usage', message: 'Usage: scripts/check lint [--json]. Use --help for exit codes.',
    }] }, json);
  } else {
    const schema = JSON.parse(readFileSync(new URL('./checks.schema.json', import.meta.url), 'utf8'));
    emit(lint(schema), json);
  }
} catch (error) {
  emit({ mode: 'lint', ok: false, exit_code: 70, findings: [{
    rule: 'engine', message: `Engine error: ${error.message}`,
  }] }, json);
}
