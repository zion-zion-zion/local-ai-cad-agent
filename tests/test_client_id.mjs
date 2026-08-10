import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

import { createClientId } from '../static/js/client-id.mjs';

test('uses native randomUUID when it is available', () => {
  assert.equal(
    createClientId({ randomUUID: () => 'native-uuid' }),
    'native-uuid',
  );
});

test('generates a UUID when randomUUID is unavailable', () => {
  const fakeCrypto = {
    getRandomValues(bytes) {
      bytes.fill(0x11);
      return bytes;
    },
  };

  const id = createClientId(fakeCrypto);

  assert.match(id, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
});

test('generates an ID when Web Crypto is unavailable', () => {
  const id = createClientId({});

  assert.match(id, /^[0-9a-z]+-[0-9a-z]+-[0-9a-z]+$/);
});

test('all app client IDs use the compatibility helper', () => {
  const appSource = fs.readFileSync(new URL('../static/js/app.js', import.meta.url), 'utf8');

  assert.doesNotMatch(appSource, /crypto\.randomUUID/);
  assert.equal((appSource.match(/createClientId\(\)/g) || []).length, 4);
});
