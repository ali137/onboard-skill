import { test } from 'node:test';
import assert from 'node:assert/strict';
import { Router } from '../src/router.ts';

function router(): Router<string> {
  return new Router<string>()
    .get('/', 'home')
    .get('/tools', 'list tools')
    .get('/tools/:tag', 'show tool')
    .post('/tools/:tag', 'update tool')
    .get('/members/:no/loans/:id', 'member loan');
}

test('matches a static path', () => {
  assert.deepEqual(router().match('GET', '/tools'), { handler: 'list tools', params: {} });
});

test('matches the root path', () => {
  assert.equal(router().match('GET', '/')?.handler, 'home');
});

test('extracts named params', () => {
  const match = router().match('GET', '/members/12/loans/7');
  assert.equal(match?.handler, 'member loan');
  assert.deepEqual(match?.params, { no: '12', id: '7' });
});

test('picks the route for the request method', () => {
  assert.equal(router().match('POST', '/tools/PT-0001')?.handler, 'update tool');
  assert.equal(router().match('get', '/tools/PT-0001')?.handler, 'show tool');
});

test('decodes percent-encoded params', () => {
  assert.equal(router().match('GET', '/tools/PT%2D0001')?.params.tag, 'PT-0001');
});

test('ignores trailing slashes', () => {
  assert.equal(router().match('GET', '/tools/')?.handler, 'list tools');
});

test('returns null when nothing matches', () => {
  assert.equal(router().match('GET', '/tools/PT-0001/extra'), null);
  assert.equal(router().match('DELETE', '/tools'), null);
});

test('a malformed escape does not match instead of throwing', () => {
  assert.equal(router().match('GET', '/tools/%E0%A4%A'), null);
});

test('lists the allowed methods for a path', () => {
  assert.deepEqual(router().allowedMethods('/tools/LD-0003'), ['GET', 'POST']);
  assert.deepEqual(router().allowedMethods('/nowhere'), []);
});
