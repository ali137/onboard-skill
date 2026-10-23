import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cancelHold, placeHold, placeInLine, queueFor } from '../src/holds.ts';
import { checkout, returnTool } from '../src/loans.ts';
import { getTool } from '../src/tools.ts';
import type { Db } from '../src/store.ts';
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
  cancelHold(db, first.id);
  assert.deepEqual(waiting(db, 'PT-0001'), ['3']);
  assert.throws(() => cancelHold(db, first.id), /cannot be canceled/);
});

test('only the member at the front of the line can borrow a returned tool', () => {
  const db = drillOut();
  placeHold(db, '2', 'PT-0001', '2026-07-29');
  placeHold(db, '3', 'PT-0001', '2026-07-29');
  returnTool(db, 'PT-0001', '2026-07-31');
  assert.throws(() => checkout(db, '3', 'PT-0001', '2026-07-31'), /held for member 2/);
  checkout(db, '2', 'PT-0001', '2026-07-31');
  assert.deepEqual(waiting(db, 'PT-0001'), ['3']);
});
