import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import {fromPayload, render} from '../../../mmw-v5-cloud/board/page/settings.mjs';
import {installDom, walk, namedButton} from '../board/fake-dom.mjs';

test('host-specific settings remain separate when editing and saving Cursor options', async () => {
  const {document} = installDom();
  const host = document.createElement('div');
  const original = JSON.parse(readFileSync(new URL('../../../mmw-v5-cloud/models.json', import.meta.url)));
  const originalSnapshot = structuredClone(original);
  const model = fromPayload({...original, store: '.cursor/models.json'});
  let saved;
  render(host, model, {saveSettings: async value => {
    saved = structuredClone(value);
    return {ok: true, json: async () => ({saved: true})};
  }});
  const input = label => walk(host).find(node => node.getAttribute?.('aria-label') === label);
  for (const role of Object.keys(original.rows.codex)) {
    assert.equal(input(`codex ${role} model`).getAttribute('value'), original.rows.codex[role].model);
    assert.equal(input(`cursor ${role} model`).getAttribute('value'), original.rows.cursor[role].model);
    assert.equal(input(`cursor ${role} context`).getAttribute('value'), original.rows.cursor[role].context);
    assert.equal(input(`cursor ${role} fast`).getAttribute('checked') !== null, original.rows.cursor[role].fast);
  }
  input('cursor senior-worker fast').dispatchEvent({type: 'change', target: {checked: false}});
  input('cursor senior-worker context').dispatchEvent({type: 'input', target: {value: '500k'}});
  namedButton(host, '保存').dispatchEvent({type: 'click'});
  await new Promise(resolve => setTimeout(resolve, 0));
  assert.deepEqual(saved.rows.codex, original.rows.codex);
  assert.deepEqual(saved.rows.cursor['senior-worker'], {...original.rows.cursor['senior-worker'], context: '500k', fast: false});
  assert.deepEqual(saved.rows.cursor['junior-worker'], original.rows.cursor['junior-worker']);
  assert.deepEqual(original, originalSnapshot);
});
