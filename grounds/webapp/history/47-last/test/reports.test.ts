import { test } from 'node:test';
import assert from 'node:assert/strict';
import { feesOutstanding, loansDueOn, mostBorrowed, overdueLoans } from '../src/reports.ts';
import { checkout, returnTool } from '../src/loans.ts';
import { payFees, waiveFee } from '../src/fees.ts';
import { addMember, sampleDb } from './helpers.ts';

test('lists overdue loans, most overdue first', () => {
  const db = sampleDb();
  checkout(db, '1', 'PT-0001', '2026-07-28');
  checkout(db, '2', 'LD-0003', '2026-07-25');
  checkout(db, '2', 'SW-0001', '2026-07-29');
  const rows = overdueLoans(db, '2026-08-06');
  assert.deepEqual(
    rows.map((row) => [row.tool.tag, row.member.memberNo, row.daysOverdue]),
    [
      ['LD-0003', '2', 8],
      ['PT-0001', '1', 2],
    ],
  );
});

test('loans overdue by the same number of days are listed by tag', () => {
  const db = sampleDb();
  checkout(db, '2', 'PT-0011', '2026-07-28');
  checkout(db, '1', 'PT-0001', '2026-07-28');
  const rows = overdueLoans(db, '2026-08-06');
  assert.deepEqual(rows.map((row) => row.tool.tag), ['PT-0001', 'PT-0011']);
});

test('returned loans are not overdue', () => {
  const db = sampleDb();
  checkout(db, '1', 'PT-0001', '2026-07-28');
  returnTool(db, 'PT-0001', '2026-08-06');
  assert.deepEqual(overdueLoans(db, '2026-08-07'), []);
});

test('lists the loans due back on a day', () => {
  const db = sampleDb();
  checkout(db, '1', 'PT-0001', '2026-07-28');
  checkout(db, '2', 'GD-0005', '2026-07-28');
  checkout(db, '2', 'SW-0001', '2026-07-28');
  returnTool(db, 'GD-0005', '2026-07-30');
  const rows = loansDueOn(db, '2026-08-04');
  assert.deepEqual(
    rows.map((row) => [row.tool.tag, row.member.memberNo]),
    [['PT-0001', '1']],
  );
  assert.deepEqual(loansDueOn(db, '2026-08-05'), []);
});

test('counts loans per tool, most borrowed first', () => {
  const db = sampleDb();
  for (const day of ['2026-07-01', '2026-07-08', '2026-07-15']) {
    checkout(db, '1', 'PT-0011', day);
    returnTool(db, 'PT-0011', day);
  }
  checkout(db, '2', 'GD-0005', '2026-07-15');
  const rows = mostBorrowed(db);
  assert.deepEqual(
    rows.map((row) => [row.tool.tag, row.loans]),
    [
      ['PT-0011', 3],
      ['GD-0005', 1],
    ],
  );
  assert.equal(mostBorrowed(db, { limit: 1 }).length, 1);
});

test('counts only loans in the date range', () => {
  const db = sampleDb();
  for (const day of ['2026-07-01', '2026-07-08', '2026-07-15']) {
    checkout(db, '1', 'PT-0011', day);
    returnTool(db, 'PT-0011', day);
  }
  const rows = mostBorrowed(db, { from: '2026-07-08', to: '2026-07-31' });
  assert.deepEqual(rows.map((row) => row.loans), [2]);
});

test('tools borrowed equally often are listed by tag', () => {
  const db = sampleDb();
  for (const tag of ['SW-0001', 'GD-0005', 'LD-0003']) {
    checkout(db, '1', tag, '2026-07-08');
    returnTool(db, tag, '2026-07-09');
  }
  const rows = mostBorrowed(db);
  assert.deepEqual(rows.map((row) => row.tool.tag), ['GD-0005', 'LD-0003', 'SW-0001']);
});

test('lists members with fees outstanding, biggest first', () => {
  const db = sampleDb();
  addMember(db, 'Ruth Amberley');
  checkout(db, '1', 'GD-0005', '2026-07-07');
  checkout(db, '2', 'PT-0001', '2026-07-07');
  checkout(db, '3', 'PT-0011', '2026-07-07');
  returnTool(db, 'GD-0005', '2026-07-20');
  returnTool(db, 'PT-0001', '2026-07-20');
  returnTool(db, 'PT-0011', '2026-07-20');
  waiveFee(db, '3', 'wren', 'hose split, not their fault', '2026-07-20');
  payFees(db, '1', 100);
  const rows = feesOutstanding(db);
  assert.deepEqual(
    rows.map((row) => [row.member.memberNo, row.owedCents]),
    [
      ['2', 400],
      ['1', 100],
    ],
  );
});
