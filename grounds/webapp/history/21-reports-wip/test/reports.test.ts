import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mostBorrowed, overdueLoans } from '../src/reports.ts';
import { checkout, returnTool } from '../src/loans.ts';
import { sampleDb } from './helpers.ts';

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

test('returned loans are not overdue', () => {
  const db = sampleDb();
  checkout(db, '1', 'PT-0001', '2026-07-28');
  returnTool(db, 'PT-0001', '2026-08-06');
  assert.deepEqual(overdueLoans(db, '2026-08-07'), []);
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
