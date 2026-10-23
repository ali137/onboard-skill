import { test } from 'node:test';
import assert from 'node:assert/strict';
import { checkout, returnTool } from '../src/loans.ts';
import { balanceCents } from '../src/fees.ts';
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
