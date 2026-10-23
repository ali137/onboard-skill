import { test } from 'node:test';
import assert from 'node:assert/strict';
import { checkout, returnTool, toolStatus } from '../src/loans.ts';
import { balanceCents } from '../src/fees.ts';
import { placeHold } from '../src/holds.ts';
import { getTool } from '../src/tools.ts';
import { addMember, sampleDb } from './helpers.ts';

test('an on-time return charges nothing', () => {
  const db = sampleDb();
  checkout(db, '1', 'PT-0001', '2026-07-07');
  const { fee } = returnTool(db, 'PT-0001', '2026-07-14');
  assert.equal(fee, null);
  assert.equal(balanceCents(db, '1'), 0);
});

test('a late return charges the fee after the grace days', () => {
  const db = sampleDb();
  checkout(db, '1', 'PT-0001', '2026-07-07');
  const { fee } = returnTool(db, 'PT-0001', '2026-07-18');
  assert.equal(fee?.amountCents, 200);
  assert.equal(balanceCents(db, '1'), 200);
});

test('a returned tool is held for the member waiting for it', () => {
  const db = sampleDb();
  checkout(db, '1', 'PT-0001', '2026-07-28');
  placeHold(db, '2', 'PT-0001', '2026-07-29');
  const { hold } = returnTool(db, 'PT-0001', '2026-07-31');
  assert.equal(hold?.memberNo, '2');
  assert.equal(hold?.status, 'ready');
  assert.equal(hold?.readyOn, '2026-07-31');
  assert.equal(hold?.pickupBy, '2026-08-05');
});

test('a return with nobody waiting puts the tool back on the shelf', () => {
  const db = sampleDb();
  checkout(db, '1', 'PT-0001', '2026-07-28');
  const { hold } = returnTool(db, 'PT-0001', '2026-07-31');
  assert.equal(hold, null);
  assert.equal(toolStatus(db, getTool(db, 'PT-0001')), 'available');
});

test('a tool dropped off on a closed day gets a pickup deadline in open days', () => {
  const db = sampleDb();
  checkout(db, '1', 'PT-0001', '2026-07-28');
  placeHold(db, '2', 'PT-0001', '2026-07-29');
  const { fee, hold } = returnTool(db, 'PT-0001', '2026-08-03');
  assert.equal(fee, null);
  assert.equal(hold?.readyOn, '2026-08-03');
  assert.equal(hold?.pickupBy, '2026-08-06');
});

test('a returned tool is held for the member who asked first', () => {
  const db = sampleDb();
  addMember(db, 'Hollis Brandt', '1042');
  addMember(db, 'Bettany Crull', '387');
  checkout(db, '1', 'PT-0011', '2026-09-29');
  const first = placeHold(db, '1042', 'PT-0011', '2026-09-30');
  const second = placeHold(db, '387', 'PT-0011', '2026-10-01');
  const { hold } = returnTool(db, 'PT-0011', '2026-10-03');
  assert.equal(hold?.id, first.id);
  assert.equal(first.status, 'ready');
  assert.equal(second.status, 'waiting');
  const message = db.outbox.find((m) => m.kind === 'hold-ready');
  assert.equal(message?.memberNo, '1042');
});

test('a member who asked twice keeps their first place in line', () => {
  const db = sampleDb();
  addMember(db, 'Ines Calloway', '15');
  addMember(db, 'Dov Ferreira', '16');
  checkout(db, '1', 'LD-0003', '2026-09-29');
  placeHold(db, '15', 'LD-0003', '2026-09-30');
  const other = placeHold(db, '16', 'LD-0003', '2026-09-30');
  placeHold(db, '15', 'LD-0003', '2026-10-01');
  const { hold } = returnTool(db, 'LD-0003', '2026-10-02');
  assert.equal(hold?.memberNo, '15');
  assert.equal(other.status, 'waiting');
});
