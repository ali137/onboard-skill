import { test } from 'node:test';
import assert from 'node:assert/strict';
import { emptyDb } from '../src/store.ts';
import type { Db } from '../src/store.ts';
import { registerMember } from '../src/members.ts';
import { addTool } from '../src/tools.ts';
import { checkout, dueDate, isOverdue, returnTool } from '../src/loans.ts';

function library(): Db {
  const db = emptyDb();
  for (const name of ['Hesper Lund', 'Odo Pickering']) {
    const email = `${name.split(' ')[0].toLowerCase()}@hollyfen.example`;
    registerMember(db, { name, email, phone: '01632 960 000', address: 'Tallowmere' }, '2026-07-01');
  }
  addTool(db, { tag: 'PT-0001', name: 'Cordless drill', category: 'PT' }, '2026-07-01');
  addTool(db, { tag: 'LD-0003', name: 'Extension ladder', category: 'LD' }, '2026-07-01');
  addTool(db, { tag: 'SW-0001', name: 'Sewing machine', category: 'SW' }, '2026-07-01');
  return db;
}

test('checkout records the loan with a due date', () => {
  const db = library();
  const loan = checkout(db, '1', 'PT-0001', '2026-07-07');
  assert.equal(loan.memberNo, '1');
  assert.equal(loan.checkedOut, '2026-07-07');
  assert.equal(loan.due, '2026-07-14');
  assert.equal(loan.returned, null);
});

test('a tool cannot be checked out twice', () => {
  const db = library();
  checkout(db, '1', 'PT-0001', '2026-07-07');
  assert.throws(() => checkout(db, '2', 'PT-0001', '2026-07-07'), /already out on loan/);
});

test('return closes the loan and frees the tool', () => {
  const db = library();
  checkout(db, '1', 'PT-0001', '2026-07-07');
  const loan = returnTool(db, 'PT-0001', '2026-07-10');
  assert.equal(loan.returned, '2026-07-10');
  assert.equal(checkout(db, '2', 'PT-0001', '2026-07-10').memberNo, '2');
});

test('due dates that land on a closed day move to the next open day', () => {
  assert.equal(dueDate('2026-07-09', 'LD'), '2026-07-14');
});

test('overdue means past the due date and not returned', () => {
  const db = library();
  const loan = checkout(db, '1', 'PT-0001', '2026-07-07');
  assert.equal(isOverdue(loan, '2026-07-14'), false);
  assert.equal(isOverdue(loan, '2026-07-15'), true);
});
