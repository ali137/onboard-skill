import { test } from 'node:test';
import assert from 'node:assert/strict';
import { checkout } from '../src/loans.ts';
import { placeHold, placeInLine, queueFor } from '../src/holds.ts';
import { getTool } from '../src/tools.ts';
import { addMember, sampleDb } from './helpers.ts';

test('the line is in request order whatever the member numbers', () => {
  const db = sampleDb();
  addMember(db, 'Hollis Brandt', '1042');
  addMember(db, 'Bettany Crull', '387');
  addMember(db, 'Ines Calloway', '55');
  checkout(db, '1', 'PT-0011', '2026-09-29');
  placeHold(db, '1042', 'PT-0011', '2026-09-30');
  placeHold(db, '387', 'PT-0011', '2026-10-01');
  placeHold(db, '55', 'PT-0011', '2026-10-02');
  placeHold(db, '1042', 'PT-0011', '2026-10-03');
  const toolId = getTool(db, 'PT-0011').id;
  assert.deepEqual(queueFor(db, toolId).map((hold) => hold.memberNo), ['1042', '387', '55']);
  assert.equal(placeInLine(db, toolId, '55'), 3);
});
