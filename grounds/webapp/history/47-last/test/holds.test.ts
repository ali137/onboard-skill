import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cancelHold, expireHolds, placeHold, placeInLine, queueFor } from '../src/holds.ts';
import { checkout, returnTool, toolStatus } from '../src/loans.ts';
import { getTool } from '../src/tools.ts';
import { suspendMember } from '../src/members.ts';
import type { Db } from '../src/db.ts';
import { addMember, sampleDb } from './helpers.ts';

// PT-0001 is out with member 1; members 2-4 can wait for it.
function drillOut(): Db {
  const db = sampleDb();
  addMember(db, 'Ruth Amberley');
  addMember(db, 'Ivo Stannard');
  checkout(db, '1', 'PT-0001', '2026-07-28');
  return db;
}

function waiting(db: Db, tag: string): string[] {
  return queueFor(db, getTool(db, tag).id).map((hold) => hold.memberNo);
}

test('a member can wait for a tool that is out', () => {
  const db = drillOut();
  const hold = placeHold(db, '2', 'PT-0001', '2026-07-29');
  assert.equal(hold.status, 'waiting');
  assert.equal(hold.requestedOn, '2026-07-29');
  assert.deepEqual(waiting(db, 'PT-0001'), ['2']);
});

test('the waiting list is in order of request', () => {
  const db = drillOut();
  placeHold(db, '2', 'PT-0001', '2026-07-29');
  placeHold(db, '3', 'PT-0001', '2026-07-30');
  placeHold(db, '4', 'PT-0001', '2026-07-30');
  assert.deepEqual(waiting(db, 'PT-0001'), ['2', '3', '4']);
  assert.equal(placeInLine(db, getTool(db, 'PT-0001').id, '3'), 2);
  assert.equal(placeInLine(db, getTool(db, 'PT-0001').id, '1'), 0);
});

test('a member who asked twice only counts once in the line', () => {
  const db = drillOut();
  placeHold(db, '2', 'PT-0001', '2026-07-29');
  placeHold(db, '3', 'PT-0001', '2026-07-29');
  placeHold(db, '2', 'PT-0001', '2026-07-30');
  assert.deepEqual(waiting(db, 'PT-0001'), ['2', '3']);
  assert.equal(placeInLine(db, getTool(db, 'PT-0001').id, '3'), 2);
});

test('no hold on a tool that is on the shelf', () => {
  assert.throws(() => placeHold(drillOut(), '2', 'PT-0011', '2026-07-29'), /on the shelf/);
});

test('no hold on a tool the member already has', () => {
  assert.throws(() => placeHold(drillOut(), '1', 'PT-0001', '2026-07-29'), /has PT-0001 already/);
});

test('a canceled hold leaves the line', () => {
  const db = drillOut();
  const first = placeHold(db, '2', 'PT-0001', '2026-07-29');
  placeHold(db, '3', 'PT-0001', '2026-07-29');
  cancelHold(db, first.id, '2026-07-30');
  assert.deepEqual(waiting(db, 'PT-0001'), ['3']);
  assert.throws(() => cancelHold(db, first.id, '2026-07-30'), /cannot be canceled/);
});

test('only the member the tool is held for can borrow it', () => {
  const db = drillOut();
  const first = placeHold(db, '2', 'PT-0001', '2026-07-29');
  placeHold(db, '3', 'PT-0001', '2026-07-29');
  returnTool(db, 'PT-0001', '2026-07-31');
  assert.equal(toolStatus(db, getTool(db, 'PT-0001')), 'on the hold shelf');
  assert.throws(() => checkout(db, '3', 'PT-0001', '2026-07-31'), /hold shelf for member 2/);
  checkout(db, '2', 'PT-0001', '2026-07-31');
  assert.equal(first.status, 'collected');
  assert.deepEqual(waiting(db, 'PT-0001'), ['3']);
});

test('canceling a ready hold passes the tool to the next in line', () => {
  const db = drillOut();
  const first = placeHold(db, '2', 'PT-0001', '2026-07-29');
  const second = placeHold(db, '3', 'PT-0001', '2026-07-29');
  returnTool(db, 'PT-0001', '2026-07-31');
  cancelHold(db, first.id, '2026-08-01');
  assert.equal(second.status, 'ready');
  assert.equal(second.pickupBy, '2026-08-06');
});

test('a suspended member cannot join a waiting list', () => {
  const db = drillOut();
  suspendMember(db, '2', 'unpaid fees', '2026-07-28');
  assert.throws(() => placeHold(db, '2', 'PT-0001', '2026-07-29'), /member 2 is suspended/);
});

test('a hold not collected by the pickup date expires and the next member gets the tool', () => {
  const db = drillOut();
  const first = placeHold(db, '2', 'PT-0001', '2026-07-29');
  const second = placeHold(db, '3', 'PT-0001', '2026-07-30');
  returnTool(db, 'PT-0001', '2026-07-31');
  assert.equal(first.pickupBy, '2026-08-05');
  assert.deepEqual(expireHolds(db, '2026-08-05'), []);
  assert.deepEqual(expireHolds(db, '2026-08-06'), [first]);
  assert.equal(first.status, 'expired');
  assert.equal(second.status, 'ready');
  assert.equal(second.pickupBy, '2026-08-11');
  assert.equal(db.outbox.at(-1)?.memberNo, '3');
});

test('an expired hold with nobody behind it frees the tool', () => {
  const db = drillOut();
  placeHold(db, '2', 'PT-0001', '2026-07-29');
  returnTool(db, 'PT-0001', '2026-07-31');
  expireHolds(db, '2026-08-06');
  assert.equal(toolStatus(db, getTool(db, 'PT-0001')), 'available');
});

test('collected and waiting holds never expire', () => {
  const db = drillOut();
  placeHold(db, '2', 'PT-0001', '2026-07-29');
  placeHold(db, '3', 'PT-0001', '2026-07-30');
  returnTool(db, 'PT-0001', '2026-07-31');
  checkout(db, '2', 'PT-0001', '2026-08-01');
  assert.deepEqual(expireHolds(db, '2026-09-30'), []);
  assert.deepEqual(waiting(db, 'PT-0001'), ['3']);
});
