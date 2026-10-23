import { test } from 'node:test';
import assert from 'node:assert/strict';
import { handle } from '../src/app.ts';
import type { Db } from '../src/store.ts';
import { createAccount } from '../src/auth.ts';
import type { AppRequest } from '../src/http.ts';
import { request, sampleDb, signIn } from './helpers.ts';

const TODAY = '2026-07-08';

function call(db: Db, req: AppRequest) {
  const res = handle(req, db, { today: TODAY, newToken: () => 'fresh-token' });
  const isJson = res.headers['content-type']?.startsWith('application/json');
  return { ...res, data: isJson ? JSON.parse(res.body) : null };
}

test('logs in and sets the session cookie', () => {
  const db = sampleDb();
  createAccount(db, { username: 'wren', password: 'correct horse', role: 'staff' });
  const body = { username: 'wren', password: 'correct horse' };
  const res = call(db, request('POST', '/login', { body }));
  assert.equal(res.status, 200);
  assert.equal(res.data.token, 'fresh-token');
  assert.match(res.headers['set-cookie'], /^session=fresh-token; HttpOnly/);
});

test('a wrong password is a 401', () => {
  const db = sampleDb();
  createAccount(db, { username: 'wren', password: 'correct horse', role: 'staff' });
  const res = call(db, request('POST', '/login', { body: { username: 'wren', password: 'nope' } }));
  assert.equal(res.status, 401);
});

test('unknown paths are 404 and wrong methods 405', () => {
  const db = sampleDb();
  assert.equal(call(db, request('GET', '/nowhere')).status, 404);
  const res = call(db, request('DELETE', '/api/tools'));
  assert.equal(res.status, 405);
  assert.equal(res.headers['allow'], 'GET, POST');
});

test('anyone can browse the catalog', () => {
  const res = call(sampleDb(), request('GET', '/api/tools', { query: { q: 'drill' } }));
  assert.equal(res.status, 200);
  assert.deepEqual(res.data.map((t: { tag: string }) => t.tag), ['PT-0001']);
});

test('adding a tool needs a staff login', () => {
  const db = sampleDb();
  const member = signIn(db, 'hesper', '1');
  const staff = signIn(db, 'wren');
  const body = { tag: 'HT-0010', name: 'Socket set', category: 'HT' };
  assert.equal(call(db, request('POST', '/api/tools', { body })).status, 401);
  assert.equal(call(db, request('POST', '/api/tools', { body, token: member })).status, 403);
  assert.equal(call(db, request('POST', '/api/tools', { body, token: staff })).status, 201);
});

test('a member can see their own record but not someone else\'s', () => {
  const db = sampleDb();
  const token = signIn(db, 'hesper', '1');
  assert.equal(call(db, request('GET', '/api/members/1', { token })).data.name, 'Hesper Lund');
  assert.equal(call(db, request('GET', '/api/members/2', { token })).status, 403);
});

test('staff check a tool out and back in', () => {
  const db = sampleDb();
  const token = signIn(db, 'wren');
  const body = { memberNo: '2', tag: 'PT-0011' };
  const out = call(db, request('POST', '/api/loans', { token, body }));
  assert.equal(out.status, 201);
  assert.equal(out.data.due, '2026-07-15');
  const loans = call(db, request('GET', '/api/members/2/loans', { token }));
  assert.equal(loans.data.length, 1);
  const form = { tag: 'PT-0011' };
  const back = call(db, request('POST', '/api/returns', { token, body: form, form: true }));
  assert.equal(back.status, 200);
  assert.equal(back.data.returned, TODAY);
});

test('rule errors come back as JSON with their status', () => {
  const db = sampleDb();
  const token = signIn(db, 'wren');
  const res = call(db, request('POST', '/api/loans', { token, body: { memberNo: '2' } }));
  assert.equal(res.status, 400);
  assert.deepEqual(res.data, { error: 'tag is required' });
});

test('logout drops the session', () => {
  const db = sampleDb();
  const token = signIn(db, 'wren');
  assert.equal(call(db, request('GET', '/api/me', { token })).status, 200);
  call(db, request('POST', '/logout', { token }));
  assert.equal(call(db, request('GET', '/api/me', { token })).status, 401);
});
