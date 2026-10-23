import { test } from 'node:test';
import assert from 'node:assert/strict';
import { escapeHtml } from '../src/views/escape.ts';
import { layout } from '../src/views/layout.ts';
import { catalogPage } from '../src/views/catalog.ts';
import { memberPage } from '../src/views/member.ts';
import { staffPage } from '../src/views/staff.ts';
import { handle } from '../src/app.ts';
import { checkout, returnTool } from '../src/loans.ts';
import { placeHold } from '../src/holds.ts';
import { getMember } from '../src/members.ts';
import { getTool } from '../src/tools.ts';
import { request, sampleDb, signIn } from './helpers.ts';

test('escapes HTML special characters', () => {
  const escaped = '&lt;b&gt;&quot;Tom&#39;s&quot; &amp; co&lt;/b&gt;';
  assert.equal(escapeHtml(`<b>"Tom's" & co</b>`), escaped);
  assert.equal(escapeHtml(42), '42');
  assert.equal(escapeHtml(undefined), '');
});

test('the layout escapes the title', () => {
  const page = layout('Drills & <saws>', '<p>body</p>');
  assert.match(page, /<title>Drills &amp; &lt;saws&gt; - Tallowmere Tool Library<\/title>/);
  assert.match(page, /<p>body<\/p>/);
});

test('the catalog lists tools with their status', () => {
  const db = sampleDb();
  const tool = getTool(db, 'PT-0001');
  const page = catalogPage([{ tool, status: 'available' }], { q: 'drill' }, null);
  assert.match(page, /<td>PT-0001<\/td>\n<td>Cordless drill<\/td>\n<td>Power tools<\/td>/);
  assert.match(page, /value="drill"/);
});

test('an empty catalog search says so', () => {
  assert.match(catalogPage([], { q: 'anvil' }, null), /No tools match/);
});

test('the member page marks overdue loans', () => {
  const db = sampleDb();
  const loan = checkout(db, '1', 'LD-0003', '2026-07-08');
  const member = getMember(db, '1');
  const tool = getTool(db, 'LD-0003');
  const data = { member, loans: [{ loan, tool }], holds: [], balanceCents: 350 };
  const page = memberPage(data, '2026-07-16', null);
  assert.match(page, /<h1>Hesper Lund<\/h1>/);
  assert.match(page, /class="overdue">2026-07-14 \(overdue\)/);
  assert.match(page, /Fees owed: <strong>\$3\.50<\/strong>/);
});

test('the catalog page is served as HTML', () => {
  const db = sampleDb();
  checkout(db, '2', 'PT-0011', '2026-07-08');
  const req = request('GET', '/catalog', { query: { q: 'washer' } });
  const res = handle(req, db, { today: '2026-07-09' });
  assert.equal(res.status, 200);
  assert.match(res.headers['content-type'], /text\/html/);
  assert.match(res.body, /on loan, due 2026-07-15/);
});

test('member pages need the member or staff to be logged in', () => {
  const db = sampleDb();
  const token = signIn(db, 'odo', '2');
  const deps = { today: '2026-07-09' };
  assert.equal(handle(request('GET', '/members/2'), db, deps).status, 401);
  assert.equal(handle(request('GET', '/members/1', { token }), db, deps).status, 403);
  const page = handle(request('GET', '/members/2', { token }), db, deps);
  assert.equal(page.status, 200);
  assert.match(page.body, /Nothing out at the moment/);
});

test('the staff page shows what is due back and what is on the hold shelf', () => {
  const db = sampleDb();
  const token = signIn(db, 'wren', undefined, '2026-09-15');
  checkout(db, '1', 'PT-0001', '2026-09-08');
  checkout(db, '2', 'GD-0005', '2026-09-08');
  placeHold(db, '1', 'GD-0005', '2026-09-09');
  returnTool(db, 'GD-0005', '2026-09-12');
  const res = handle(request('GET', '/staff/today', { token }), db, { today: '2026-09-15' });
  assert.equal(res.status, 200);
  assert.match(res.body, /<h1>Today, 2026-09-15<\/h1>/);
  assert.match(res.body, /<td>PT-0001<\/td><td>Cordless drill<\/td><td><a href="\/members\/1">/);
  assert.match(res.body, /<td>GD-0005<\/td><td>Hedge trimmer<\/td>.*<td>2026-09-17<\/td>/);
  assert.match(res.body, /Nothing is overdue/);
});

test('the staff page lists waiting lists with their length', () => {
  const db = sampleDb();
  checkout(db, '1', 'SW-0001', '2026-09-08');
  placeHold(db, '2', 'SW-0001', '2026-09-09');
  const data = {
    dueToday: [],
    overdue: [],
    holdsReady: [],
    waiting: [{ tool: getTool(db, 'SW-0001'), count: 1 }],
    search: null,
  };
  const page = staffPage(data, '2026-09-15', null);
  assert.match(page, /<td>SW-0001<\/td><td>Sewing machine<\/td><td>1<\/td>/);
  assert.match(page, /Nothing is due back today/);
});

test('the staff page has the counter forms and finds members', () => {
  const db = sampleDb();
  const token = signIn(db, 'wren', undefined, '2026-09-15');
  const req = request('GET', '/staff/today', { token, query: { q: 'pick' } });
  const res = handle(req, db, { today: '2026-09-15' });
  assert.match(res.body, /<form method="post" action="\/api\/loans">/);
  assert.match(res.body, /<form method="post" action="\/api\/returns">/);
  assert.match(res.body, /name="q" value="pick"/);
  assert.match(res.body, /<li><a href="\/members\/2">Odo Pickering<\/a> \(2\)<\/li>/);
});

test('a member search with no hits says so', () => {
  const db = sampleDb();
  const token = signIn(db, 'wren', undefined, '2026-09-15');
  const req = request('GET', '/staff/today', { token, query: { q: 'nobody' } });
  assert.match(handle(req, db, { today: '2026-09-15' }).body, /No members match/);
});

test('only staff see the staff page', () => {
  const db = sampleDb();
  const token = signIn(db, 'hesper', '1', '2026-09-15');
  const res = handle(request('GET', '/staff/today', { token }), db, { today: '2026-09-15' });
  assert.equal(res.status, 403);
  assert.match(res.headers['content-type'], /text\/html/);
});
