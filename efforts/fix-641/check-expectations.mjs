import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { homedir } from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Worker } from 'node:worker_threads';

const installed = (await readFile(path.join(homedir(), '.mmw/installed-root'), 'utf8')).trim();
const gateRoot = path.join(installed, 'skills/verify-ticket/scripts/gate-check');
const { parseGates } = await import(pathToFileURL(path.join(gateRoot, 'lib/gates.mjs')).href);
const logs = process.argv[2];
assert.ok(logs, 'supply the original CHECK output directory');

async function matches(expect, output) {
  const ledger = '- [ ] AC: original success condition\n  CHECK: true\n  EXPECT: ' + expect + '\n  EVIDENCE: pending\n';
  const parsed = parseGates(ledger);
  assert.deepEqual(parsed.errors, []);
  const expectation = parsed.gates[0].expectation;
  if (expectation.kind === 'text') return output.includes(expectation.value);
  const worker = new Worker(path.join(gateRoot, 'lib/regex-worker.mjs'));
  try {
    return await new Promise((resolve, reject) => {
      worker.once('error', reject);
      worker.once('message', reply => reply.error ? reject(new Error(reply.error)) : resolve(reply.matched));
      worker.postMessage({ source: expectation.source, flags: expectation.flags, output });
    });
  } finally {
    await worker.terminate();
  }
}

const rows = [];
for (const number of [3, 4, 5, 6, 7, 8, 9, 10]) {
  const id = 'AC' + number;
  const count = number === 3 ? 3 : 1;
  const source = number === 3 || number === 10
    ? '^\\s*Tests\\s+' + count + ' passed \\(' + count + '\\)\\s*$' : '^OK$';
  const old = '(?m)' + source;
  const corrected = '/' + source + '/m';
  const output = await readFile(path.join(logs, id + '.log'), 'utf8');
  assert.equal(await matches(old, output), false, id + ' must reproduce the old mismatch');
  assert.equal(await matches(corrected, output), true, id + ' must accept the original successful output');
  const failures = number === 3 || number === 10
    ? ['Tests  1 failed | ' + count + ' passed (' + (count + 1) + ')\n', 'Tests  3 skipped (3)\n', 'Tests  2 passed (2)\n']
    : ['FAILED (failures=1)\n', 'OK (skipped=1)\n', 'Ran 0 tests\n'];
  for (const failure of failures) assert.equal(await matches(corrected, failure), false, id + ' must reject ' + failure);
  rows.push({ id, old, corrected, oldMatched: false, correctedMatched: true, rejectedControls: failures.length });
}
console.log(JSON.stringify({ installed, rows }, null, 2));
console.log('EXPECT_SYNTAX_CORRECTION_PROVEN');
