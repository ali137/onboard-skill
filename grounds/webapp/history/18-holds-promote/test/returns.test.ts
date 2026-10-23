import { test } from 'node:test';
import assert from 'node:assert/strict';
import { checkout, returnTool } from '../src/loans.ts';
import { balanceCents } from '../src/fees.ts';
import { placeHold } from '../src/holds.ts';
import { getTool, toolStatus } from '../src/tools.ts';
import { sampleDb } from './helpers.ts';

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
