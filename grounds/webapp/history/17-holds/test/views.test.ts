import { test } from 'node:test';
import assert from 'node:assert/strict';
import { escapeHtml } from '../src/views/escape.ts';
import { layout } from '../src/views/layout.ts';
import { catalogPage } from '../src/views/catalog.ts';
import { memberPage } from '../src/views/member.ts';
import { handle } from '../src/app.ts';
import { checkout } from '../src/loans.ts';
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
