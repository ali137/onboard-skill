import { test } from 'node:test';
import assert from 'node:assert/strict';
import { HttpError, field, json, parseBody, parseQuery, requiredField } from '../src/http.ts';
import { request } from './helpers.ts';

test('parses a JSON body', () => {
  const req = request('POST', '/x', { body: { tag: 'PT-0001', count: 2 } });
  assert.deepEqual(parseBody(req), { tag: 'PT-0001', count: 2 });
});

test('parses a form body', () => {
  const req = request('POST', '/x', { body: { name: 'Hesper Lund', note: 'a&b' }, form: true });
  assert.deepEqual(parseBody(req), { name: 'Hesper Lund', note: 'a&b' });
});

test('an empty body parses to an empty object', () => {
  assert.deepEqual(parseBody(request('POST', '/x')), {});
});

test('rejects broken JSON and non-object JSON', () => {
  const broken = { ...request('POST', '/x', { body: {} }), body: '{"tag":' };
  assert.throws(() => parseBody(broken), /not valid JSON/);
  const list = { ...request('POST', '/x', { body: {} }), body: '[1, 2]' };
  assert.throws(() => parseBody(list), /must be a JSON object/);
});

test('rejects other content types with a 415', () => {
  const req = { ...request('POST', '/x'), headers: { 'content-type': 'text/xml' }, body: '<a/>' };
  assert.throws(
    () => parseBody(req),
    (err: unknown) => err instanceof HttpError && err.status === 415,
  );
});

test('reads query strings', () => {
  assert.deepEqual(parseQuery('?q=drill+bit&category=PT'), { q: 'drill bit', category: 'PT' });
  assert.deepEqual(parseQuery(''), {});
});

test('reads optional and required fields', () => {
  const body = { memberNo: 42, tag: '  ', name: 'Odo' };
  assert.equal(field(body, 'memberNo'), '42');
  assert.equal(field(body, 'missing'), undefined);
  assert.equal(requiredField(body, 'name'), 'Odo');
  assert.throws(() => requiredField(body, 'tag'), /tag is required/);
});

test('json responses carry a content type', () => {
  const res = json(201, { ok: true });
  assert.equal(res.status, 201);
  assert.match(res.headers['content-type'], /application\/json/);
  assert.equal(res.body, '{"ok":true}');
});
