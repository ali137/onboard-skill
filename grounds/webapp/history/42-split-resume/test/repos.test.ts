import { test } from 'node:test';
import assert from 'node:assert/strict';
import { emptyDb, parseDb, serializeDb } from '../src/db.ts';
import * as membersRepo from '../src/repos/members.ts';
import { addMember, sampleDb } from './helpers.ts';

test('members repo finds members by number', () => {
  const db = sampleDb();
  assert.equal(membersRepo.byNumber(db, '2')?.name, 'Odo Pickering');
  assert.equal(membersRepo.byNumber(db, '02'), undefined);
  assert.equal(membersRepo.byNumber(db, '99'), undefined);
});

test('members repo lists and inserts members', () => {
  const db = emptyDb();
  const member = {
    memberNo: '387',
    name: 'Bettany Crull',
    email: 'bettany@hollyfen.example',
    phone: '01632 960 552',
    address: '9 Lantern Street',
    joinedOn: '2019-04-13',
    suspended: null,
  };
  membersRepo.insert(db, member);
  assert.deepEqual(membersRepo.all(db), [member]);
});

test('next member number skips numbers from the paper cards', () => {
  const db = emptyDb();
  addMember(db, 'Bettany Crull', '1');
  addMember(db, 'Hollis Brandt', '2');
  addMember(db, 'Ines Calloway', '4');
  assert.equal(membersRepo.nextNumber(db), '3');
  assert.equal(membersRepo.nextNumber(db), '5');
  assert.equal(db.counters.member, 5);
});

test('a data file round-trips', () => {
  const db = sampleDb();
  assert.deepEqual(parseDb(serializeDb(db)), db);
});

test('an older data file gets the fields added since', () => {
  const old = JSON.stringify({
    members: [{ memberNo: '1', name: 'Hesper Lund', email: 'h@hollyfen.example' }],
    holds: [{ id: '1', toolId: '3', memberNo: '1', requestedOn: '2026-07-01', status: 'waiting' }],
    counters: { member: 1, hold: 1 },
  });
  const db = parseDb(old);
  assert.equal(db.members[0].suspended, null);
  assert.equal(db.holds[0].pickupBy, null);
  assert.deepEqual(db.outbox, []);
  assert.equal(db.counters.member, 1);
  assert.equal(db.counters.message, 0);
});

test('a data file that is not an object is refused', () => {
  assert.throws(() => parseDb('[]'), /must hold a JSON object/);
  assert.throws(() => parseDb('{"members": ['), SyntaxError);
});
