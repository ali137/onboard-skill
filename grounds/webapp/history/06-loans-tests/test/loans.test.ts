import { test } from 'node:test';
import assert from 'node:assert/strict';
import { emptyDb } from '../src/store.ts';
import type { Db } from '../src/store.ts';
import { registerMember } from '../src/members.ts';
import { addTool, retireTool } from '../src/tools.ts';
import { checkout, dueDate, isOverdue, returnTool } from '../src/loans.ts';
import { HttpError } from '../src/http.ts';

function library(): Db {
  const db = emptyDb();
  for (const name of ['Hesper Lund', 'Odo Pickering']) {
    const email = `${name.split(' ')[0].toLowerCase()}@hollyfen.example`;
    const contact = { email, phone: '01632 960 000', address: 'Tallowmere' };
    registerMember(db, { name, ...contact }, '2026-07-01');
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

test('loan periods depend on the category', () => {
  assert.equal(dueDate('2026-07-07', 'PT'), '2026-07-14');
  assert.equal(dueDate('2026-07-07', 'SW'), '2026-07-21');
  assert.equal(dueDate('2026-07-07', 'LD'), '2026-07-11');
});

test('a due date on a closure day moves past it', () => {
  assert.equal(dueDate('2026-08-22', 'PT'), '2026-09-01');
});

test('a member can have at most five tools out', () => {
  const db = library();
  for (let i = 1; i <= 5; i++) {
    addTool(db, { tag: `HT-000${i}`, name: `Hand tool ${i}`, category: 'HT' }, '2026-07-01');
    checkout(db, '1', `HT-000${i}`, '2026-07-07');
  }
  assert.throws(() => checkout(db, '1', 'PT-0001', '2026-07-07'), /already has 5 tools out/);
  assert.equal(checkout(db, '2', 'PT-0001', '2026-07-07').memberNo, '2');
});

test('retired tools cannot be checked out', () => {
  const db = library();
  retireTool(db, 'SW-0001');
  assert.throws(() => checkout(db, '1', 'SW-0001', '2026-07-07'), /has been retired/);
});

test('unknown members and tags are 404s', () => {
  const db = library();
  const is404 = (err: unknown) => err instanceof HttpError && err.status === 404;
  assert.throws(() => checkout(db, '99', 'PT-0001', '2026-07-07'), is404);
  assert.throws(() => checkout(db, '1', 'PT-0999', '2026-07-07'), is404);
});

test('returning a tool that is not out is a conflict', () => {
  assert.throws(
    () => returnTool(library(), 'PT-0001', '2026-07-07'),
    (err: unknown) => err instanceof HttpError && err.status === 409,
  );
});
