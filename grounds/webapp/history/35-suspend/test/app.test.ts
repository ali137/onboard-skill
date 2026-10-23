import { test } from 'node:test';
import assert from 'node:assert/strict';
import { handle } from '../src/app.ts';
import type { Db } from '../src/db.ts';
import { createAccount } from '../src/auth.ts';
import { addTool } from '../src/tools.ts';
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
  const back = call(db, request('POST', '/api/returns', { token, body: { tag: 'PT-0011' } }));
  assert.equal(back.status, 200);
  assert.equal(back.data.loan.returned, TODAY);
  assert.equal(back.data.fee, null);
});

test('the counter forms go back to the staff page', () => {
  const db = sampleDb();
  const token = signIn(db, 'wren');
  const lend = { memberNo: '1', tag: 'GD-0005' };
  const out = call(db, request('POST', '/api/loans', { token, body: lend, form: true }));
  assert.equal(out.status, 303);
  assert.equal(out.headers['location'], '/staff/today');
  const form = { tag: 'GD-0005' };
  const back = call(db, request('POST', '/api/returns', { token, body: form, form: true }));
  assert.equal(back.status, 303);
  assert.equal(db.loans[0].returned, TODAY);
});

test('a refused counter form shows the reason as a page', () => {
  const db = sampleDb();
  const token = signIn(db, 'wren');
  const lend = { memberNo: '1', tag: 'GD-0005' };
  call(db, request('POST', '/api/loans', { token, body: lend }));
  const res = call(db, request('POST', '/api/loans', { token, body: lend, form: true }));
  assert.equal(res.status, 409);
  assert.match(res.headers['content-type'], /text\/html/);
  assert.match(res.body, /GD-0005 is already out on loan/);
  assert.match(res.body, /Back to today/);
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

test('a member can renew their own loan but not someone else\'s', () => {
  const db = sampleDb();
  const staff = signIn(db, 'wren');
  const member = signIn(db, 'hesper', '1');
  const body = { memberNo: '2', tag: 'PT-0011' };
  const loan = call(db, request('POST', '/api/loans', { token: staff, body })).data;
  const path = `/api/loans/${loan.id}/renew`;
  assert.equal(call(db, request('POST', path, { token: member })).status, 403);
  const renewed = call(db, request('POST', path, { token: staff }));
  assert.equal(renewed.status, 200);
  assert.equal(renewed.data.renewals, 1);
});

test('a member joins the waiting list for themselves', () => {
  const db = sampleDb();
  const staff = signIn(db, 'wren');
  const member = signIn(db, 'hesper', '1');
  const loan = { memberNo: '2', tag: 'PT-0011' };
  call(db, request('POST', '/api/loans', { token: staff, body: loan }));
  const res = call(db, request('POST', '/api/holds', { token: member, body: { tag: 'PT-0011' } }));
  assert.equal(res.status, 201);
  assert.equal(res.data.memberNo, '1');
  const queue = call(db, request('GET', '/api/tools/PT-0011/holds', { token: staff }));
  assert.deepEqual(queue.data.map((h: { memberNo: string }) => h.memberNo), ['1']);
});

test('checkout over a limit is a 409 with the reason', () => {
  const db = sampleDb();
  const token = signIn(db, 'wren');
  addTool(db, { tag: 'SW-0003', name: 'Overlocker', category: 'SW' }, TODAY);
  const lend = (tag: string) =>
    call(db, request('POST', '/api/loans', { token, body: { memberNo: '1', tag } }));
  assert.equal(lend('SW-0001').status, 201);
  const res = lend('SW-0003');
  assert.equal(res.status, 409);
  assert.match(res.data.error, /can't borrow more sewing/);
});

test('only staff can import the inventory sheet', () => {
  const db = sampleDb();
  const staff = signIn(db, 'wren');
  const member = signIn(db, 'hesper', '1');
  const sheet = 'Tag,Name,Category,Condition,Notes\nHT-0010,Socket set,HT,good,\n';
  const upload = (token: string) => ({
    ...request('POST', '/api/import/inventory', { token }),
    headers: { authorization: `Bearer ${token}`, 'content-type': 'text/csv' },
    body: sheet,
  });
  assert.equal(call(db, upload(member)).status, 403);
  const res = call(db, upload(staff));
  assert.equal(res.status, 200);
  assert.deepEqual(res.data, { added: 1, updated: 0, rejected: [] });
});

test('suspending from the member page form goes back to the page', () => {
  const db = sampleDb();
  const token = signIn(db, 'wren');
  const body = { reason: 'lost the hedge trimmer' };
  const res = call(db, request('POST', '/api/members/1/suspend', { token, body, form: true }));
  assert.equal(res.status, 303);
  assert.equal(res.headers['location'], '/members/1');
  const back = call(db, request('POST', '/api/members/1/reinstate', { token }));
  assert.equal(back.status, 200);
  assert.equal(back.data.suspended, null);
});
