import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  balanceCents,
  chargeLateFee,
  formatCents,
  lateFeeCents,
  payFees,
  waiveFee,
} from '../src/fees.ts';
import type { Db, Loan } from '../src/store.ts';
import { sampleDb } from './helpers.ts';

function loan(due: string, memberNo = '1', id = '1'): Loan {
  return { id, toolId: '1', memberNo, checkedOut: '2026-07-01', due, returned: null };
}

function owing(memberNo: string, ...amounts: number[]): Db {
  const db = sampleDb();
  for (const amountCents of amounts) {
    const id = String(++db.counters.fee);
    const fee = { id, memberNo, loanId: id, amountCents, paidCents: 0, chargedOn: '2026-07-14' };
    db.fees.push({ ...fee, waived: null });
  }
  return db;
}

test('nothing is charged for an on-time return', () => {
  assert.equal(lateFeeCents(loan('2026-07-14'), 'PT', '2026-07-14'), 0);
  assert.equal(lateFeeCents(loan('2026-07-14'), 'PT', '2026-07-10'), 0);
});

test('charges per day late at the category rate', () => {
  assert.equal(lateFeeCents(loan('2026-07-14'), 'PT', '2026-07-17'), 300);
  assert.equal(lateFeeCents(loan('2026-07-14'), 'GD', '2026-07-17'), 150);
});

test('caps the fee for a single loan', () => {
  assert.equal(lateFeeCents(loan('2026-07-14'), 'PT', '2026-09-30'), 2000);
});

test('records a fee against the member', () => {
  const db = sampleDb();
  const fee = chargeLateFee(db, loan('2026-07-14', '2'), 'PT', '2026-07-18');
  assert.equal(fee?.memberNo, '2');
  assert.equal(fee?.amountCents, 400);
  assert.equal(balanceCents(db, '2'), 400);
  assert.equal(chargeLateFee(db, loan('2026-07-20', '2'), 'PT', '2026-07-18'), null);
});

test('payments go to the oldest fee first', () => {
  const db = owing('1', 300, 500);
  payFees(db, '1', 400);
  assert.deepEqual(db.fees.map((f) => f.paidCents), [300, 100]);
  assert.equal(balanceCents(db, '1'), 400);
});

test('a payment cannot be more than what is owed', () => {
  const db = owing('1', 300);
  assert.throws(() => payFees(db, '1', 301), /more than the \$3\.00 owed/);
  assert.throws(() => payFees(db, '1', 2.5), /whole number of cents/);
});

test('a waived fee no longer counts', () => {
  const db = owing('1', 300, 500);
  const fee = waiveFee(db, '2', 'wren', 'ladder was returned to the wrong branch', '2026-07-20');
  assert.equal(fee.waived?.by, 'wren');
  assert.equal(balanceCents(db, '1'), 300);
  assert.throws(() => waiveFee(db, '2', 'wren', 'again', '2026-07-20'), /already waived/);
});

test('a waiver needs a reason', () => {
  assert.throws(() => waiveFee(owing('1', 300), '1', 'wren', '  ', '2026-07-20'), /needs a reason/);
});

test('formats cents as dollars', () => {
  assert.equal(formatCents(0), '$0.00');
  assert.equal(formatCents(5), '$0.05');
  assert.equal(formatCents(1250), '$12.50');
});
