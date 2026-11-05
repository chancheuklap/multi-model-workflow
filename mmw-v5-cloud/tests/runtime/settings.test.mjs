import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import {fromPayload, render} from '../../../mmw-v5-cloud/board/page/settings.mjs';
import {installDom, walk, namedButton} from './fake-dom.mjs';

for (const nativeHost of ['cursor', 'codex']) test(`${nativeHost} settings show and save only their installed host`, async () => {
  const {document} = installDom();
  const host = document.createElement('div');
  const original = JSON.parse(readFileSync(new URL('../../../mmw-v5-cloud/models.json', import.meta.url)));
  const originalSnapshot = structuredClone(original);
  const directory = nativeHost === 'codex' ? '.agents' : '.cursor';
  const model = fromPayload({...original, host: nativeHost, store: `${directory}/models.json`});
  let saved;
  render(host, model, {saveSettings: async value => {
    saved = structuredClone(value);
    return {ok: true, json: async () => ({saved: true})};
  }});
  const input = label => walk(host).find(node => node.getAttribute?.('aria-label') === label);
  for (const role of Object.keys(original.rows.codex)) {
    assert.equal(input(`${nativeHost} ${role} model`).getAttribute('value'), original.rows[nativeHost][role].model);
    assert.equal(input(`${nativeHost === 'codex' ? 'cursor' : 'codex'} ${role} model`), undefined);
  }
  input(`${nativeHost} senior-worker model`).dispatchEvent({type: 'input', target: {value: 'chosen-native-model'}});
  if (nativeHost === 'cursor') {
    input('cursor senior-worker fast').dispatchEvent({type: 'change', target: {checked: false}});
    input('cursor senior-worker context').dispatchEvent({type: 'input', target: {value: '500k'}});
  } else {
    assert.equal(input('codex senior-worker context'), undefined);
    assert.equal(input('codex senior-worker fast'), undefined);
  }
  namedButton(host, '保存').dispatchEvent({type: 'click'});
  await new Promise(resolve => setTimeout(resolve, 0));
  assert.deepEqual(Object.keys(saved.rows), [nativeHost]);
  assert.deepEqual(saved.rows[nativeHost]['senior-worker'], {
    ...original.rows[nativeHost]['senior-worker'], model: 'chosen-native-model',
    ...(nativeHost === 'cursor' ? {context: '500k', fast: false} : {}),
  });
  assert.deepEqual(saved.rows[nativeHost]['junior-worker'], original.rows[nativeHost]['junior-worker']);
  assert.deepEqual(original, originalSnapshot);
});
