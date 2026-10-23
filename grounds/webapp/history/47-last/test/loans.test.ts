import { test } from 'node:test';
import assert from 'node:assert/strict';
import { emptyDb } from '../src/db.ts';
import type { Db } from '../src/db.ts';
import { registerMember } from '../src/members.ts';
import { addTool, getTool, retireTool } from '../src/tools.ts';
import {
  checkout,
  dueDate,
  isOverdue,
  loanAllowance,
  memberLoans,
  renew,
  returnTool,
  toolStatus,
} from '../src/loans.ts';
import { HttpError } from '../src/http.ts';
import { suspendMember } from '../src/members.ts';
import { payFees } from '../src/fees.ts';
import { cancelHold, placeHold } from '../src/holds.ts';

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
  const { loan } = returnTool(db, 'PT-0001', '2026-07-10');
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
  for (const [tag, category] of [['HT-0001', 'HT'], ['HT-0002', 'HT'], ['GD-0001', 'GD']]) {
    addTool(db, { tag, name: `Tool ${tag}`, category }, '2026-07-01');
    checkout(db, '1', tag, '2026-07-07');
  }
  checkout(db, '1', 'LD-0003', '2026-07-07');
  checkout(db, '1', 'SW-0001', '2026-07-07');
  assert.throws(() => checkout(db, '1', 'PT-0001', '2026-07-07'), /already has 5 tools out/);
  assert.equal(checkout(db, '2', 'PT-0001', '2026-07-07').memberNo, '2');
});

test('a member can have only one ladder out', () => {
  const db = library();
  addTool(db, { tag: 'LD-0001', name: 'Step ladder', category: 'LD' }, '2026-07-01');
  checkout(db, '1', 'LD-0003', '2026-07-07');
  assert.throws(
    () => checkout(db, '1', 'LD-0001', '2026-07-07'),
    /can't borrow more ladders \(limit 1\)/,
  );
  assert.equal(checkout(db, '1', 'PT-0001', '2026-07-07').memberNo, '1');
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

test('renewing adds another loan period from the due date', () => {
  const db = library();
  const loan = checkout(db, '1', 'PT-0001', '2026-07-07');
  renew(db, loan.id, '2026-07-10');
  assert.equal(loan.due, '2026-07-21');
  assert.equal(loan.renewals, 1);
});

test('a loan can be renewed twice', () => {
  const db = library();
  const loan = checkout(db, '1', 'SW-0001', '2026-07-07');
  renew(db, loan.id, '2026-07-08');
  renew(db, loan.id, '2026-07-08');
  assert.equal(loan.due, '2026-08-18');
  assert.throws(() => renew(db, loan.id, '2026-07-08'), /renewed 2 times already/);
});

test('overdue and returned loans cannot be renewed', () => {
  const db = library();
  const loan = checkout(db, '1', 'PT-0001', '2026-07-07');
  assert.throws(() => renew(db, loan.id, '2026-07-15'), /is overdue/);
  returnTool(db, 'PT-0001', '2026-07-15');
  assert.throws(() => renew(db, loan.id, '2026-07-15'), /already returned/);
});

test('a new member has the full allowance', () => {
  assert.deepEqual(loanAllowance(library(), '1'), {
    total: 5,
    byCategory: { PT: 2, LD: 1, GD: 3, SW: 1, HT: 4 },
  });
});

test('open loans use up the allowance and returns give it back', () => {
  const db = library();
  checkout(db, '1', 'PT-0001', '2026-07-07');
  checkout(db, '1', 'SW-0001', '2026-07-07');
  let allowance = loanAllowance(db, '1');
  assert.equal(allowance.total, 3);
  assert.equal(allowance.byCategory.PT, 1);
  assert.equal(allowance.byCategory.SW, 0);
  returnTool(db, 'SW-0001', '2026-07-09');
  allowance = loanAllowance(db, '1');
  assert.equal(allowance.total, 4);
  assert.equal(allowance.byCategory.SW, 1);
});

test('one member reaching a limit does not affect another', () => {
  const db = library();
  checkout(db, '1', 'SW-0001', '2026-07-07');
  assert.equal(loanAllowance(db, '2').byCategory.SW, 1);
});

test('the per-category limit applies to power tools too', () => {
  const db = library();
  addTool(db, { tag: 'PT-0002', name: 'Hammer drill', category: 'PT' }, '2026-07-01');
  addTool(db, { tag: 'PT-0004', name: 'Jigsaw', category: 'PT' }, '2026-07-01');
  checkout(db, '2', 'PT-0001', '2026-07-07');
  checkout(db, '2', 'PT-0002', '2026-07-07');
  assert.throws(() => checkout(db, '2', 'PT-0004', '2026-07-07'), /more power tools \(limit 2\)/);
});

test('a suspended member cannot borrow', () => {
  const db = library();
  suspendMember(db, '2', 'damaged the tile cutter', '2026-07-06');
  assert.throws(() => checkout(db, '2', 'PT-0001', '2026-07-07'), /member 2 is suspended/);
});

test('checkout is blocked once a member owes ten dollars', () => {
  const db = library();
  checkout(db, '1', 'PT-0001', '2026-07-07');
  const { fee } = returnTool(db, 'PT-0001', '2026-07-26');
  assert.equal(fee?.amountCents, 1000);
  assert.throws(
    () => checkout(db, '1', 'SW-0001', '2026-07-28'),
    /member 1 owes \$10\.00 \(limit \$10\.00\)/,
  );
  payFees(db, '1', 1);
  assert.equal(checkout(db, '1', 'SW-0001', '2026-07-28').memberNo, '1');
});

test('a suspended member cannot renew either', () => {
  const db = library();
  const loan = checkout(db, '2', 'PT-0001', '2026-07-07');
  suspendMember(db, '2', 'damaged the tile cutter', '2026-07-08');
  assert.throws(() => renew(db, loan.id, '2026-07-09'), /member 2 is suspended/);
});

test('a loan cannot be renewed while someone is waiting for the tool', () => {
  const db = library();
  const loan = checkout(db, '1', 'PT-0001', '2026-07-07');
  const hold = placeHold(db, '2', 'PT-0001', '2026-07-08');
  assert.throws(() => renew(db, loan.id, '2026-07-10'), /someone is waiting for PT-0001/);
  cancelHold(db, hold.id, '2026-07-10');
  assert.equal(renew(db, loan.id, '2026-07-10').renewals, 1);
});

test('lists a member\'s open loans with their tools', () => {
  const db = library();
  checkout(db, '1', 'PT-0001', '2026-07-07');
  checkout(db, '1', 'SW-0001', '2026-07-07');
  checkout(db, '2', 'LD-0003', '2026-07-07');
  returnTool(db, 'SW-0001', '2026-07-09');
  const loans = memberLoans(db, '1');
  assert.deepEqual(loans.map(({ tool }) => tool.tag), ['PT-0001']);
  assert.equal(loans[0].loan.due, '2026-07-14');
});

test('the catalog status says whether a tool is out, put aside or retired', () => {
  const db = library();
  checkout(db, '1', 'PT-0001', '2026-07-07');
  placeHold(db, '2', 'PT-0001', '2026-07-08');
  retireTool(db, 'SW-0001');
  assert.equal(toolStatus(db, getTool(db, 'PT-0001')), 'on loan, due 2026-07-14');
  assert.equal(toolStatus(db, getTool(db, 'SW-0001')), 'retired');
  assert.equal(toolStatus(db, getTool(db, 'LD-0003')), 'available');
  returnTool(db, 'PT-0001', '2026-07-10');
  assert.equal(toolStatus(db, getTool(db, 'PT-0001')), 'on the hold shelf');
});
