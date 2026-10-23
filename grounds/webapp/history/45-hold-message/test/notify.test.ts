import { test } from 'node:test';
import assert from 'node:assert/strict';
import { holdReadyMessage, queueOverdueReminders } from '../src/notify.ts';
import { checkout, returnTool } from '../src/loans.ts';
import { placeHold } from '../src/holds.ts';
import { getMember } from '../src/members.ts';
import { getTool } from '../src/tools.ts';
import type { Hold } from '../src/db.ts';
import { sampleDb } from './helpers.ts';

test('the hold-ready message names the tool and the pickup date', () => {
  const db = sampleDb();
  const hold: Hold = {
    id: '1',
    toolId: '1',
    memberNo: '2',
    requestedOn: '2026-07-29',
    status: 'ready',
    readyOn: '2026-07-31',
    pickupBy: '2026-08-05',
  };
  const draft = holdReadyMessage(getMember(db, '2'), getTool(db, 'PT-0001'), hold);
  assert.equal(draft.subject, 'Ready to collect: Cordless drill');
  assert.match(draft.body, /^Hello Odo,/);
  assert.match(draft.body, /the Cordless drill \(PT-0001\) you were waiting for is back/);
  assert.match(draft.body, /Please collect it by Wednesday, August 5\./);
  assert.match(draft.body, /Tallowmere Tool Library$/);
});

test('a message is queued when a hold becomes ready', () => {
  const db = sampleDb();
  checkout(db, '1', 'GD-0005', '2026-07-28');
  placeHold(db, '2', 'GD-0005', '2026-07-29');
  returnTool(db, 'GD-0005', '2026-07-30');
  assert.equal(db.outbox.length, 1);
  const [message] = db.outbox;
  assert.equal(message.kind, 'hold-ready');
  assert.equal(message.memberNo, '2');
  assert.equal(message.to, 'odo.pickering@hollyfen.example');
  assert.equal(message.createdOn, '2026-07-30');
});

test('one overdue reminder per member lists all their late tools', () => {
  const db = sampleDb();
  checkout(db, '1', 'PT-0001', '2026-07-28');
  checkout(db, '1', 'GD-0005', '2026-07-28');
  checkout(db, '2', 'SW-0001', '2026-07-28');
  const queued = queueOverdueReminders(db, '2026-08-06');
  assert.equal(queued.length, 1);
  assert.equal(queued[0].memberNo, '1');
  assert.equal(queued[0].subject, '2 tools are overdue');
  assert.match(queued[0].body, /- Cordless drill \(PT-0001\), due 2026-08-04/);
  assert.match(queued[0].body, /- Hedge trimmer \(GD-0005\), due 2026-08-04/);
});

test('overdue reminders go out at most once a week', () => {
  const db = sampleDb();
  checkout(db, '1', 'PT-0001', '2026-07-28');
  assert.equal(queueOverdueReminders(db, '2026-08-05').length, 1);
  assert.equal(queueOverdueReminders(db, '2026-08-08').length, 0);
  assert.equal(queueOverdueReminders(db, '2026-08-12').length, 1);
});

test('nothing is queued when nothing is overdue', () => {
  const db = sampleDb();
  checkout(db, '1', 'PT-0001', '2026-07-28');
  assert.deepEqual(queueOverdueReminders(db, '2026-08-04'), []);
});
