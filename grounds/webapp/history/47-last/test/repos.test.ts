import { test } from 'node:test';
import assert from 'node:assert/strict';
import { emptyDb, parseDb, serializeDb } from '../src/db.ts';
import * as membersRepo from '../src/repos/members.ts';
import * as toolsRepo from '../src/repos/tools.ts';
import * as holdsRepo from '../src/repos/holds.ts';
import { checkout } from '../src/loans.ts';
import { placeHold } from '../src/holds.ts';
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

test('tools repo finds tools by id and by tag', () => {
  const db = sampleDb();
  const drill = toolsRepo.byTag(db, 'PT-0001');
  assert.equal(drill?.name, 'Cordless drill');
  assert.equal(toolsRepo.byId(db, drill?.id ?? ''), drill);
  assert.equal(toolsRepo.byTag(db, 'pt-0001'), undefined);
  assert.equal(toolsRepo.all(db).length, 5);
});

test('tools repo gives new tools the next id', () => {
  const db = sampleDb();
  const tool = toolsRepo.insert(db, {
    tag: 'HT-0014',
    name: 'Tile cutter',
    category: 'HT',
    condition: 'good',
    notes: '',
    retired: false,
    addedOn: '2026-10-20',
  });
  assert.equal(tool.id, '6');
  assert.equal(db.counters.tool, 6);
});

test('holds repo separates waiting and ready holds', () => {
  const db = sampleDb();
  addMember(db, 'Ruth Amberley');
  checkout(db, '1', 'LD-0003', '2026-10-13');
  const first = placeHold(db, '2', 'LD-0003', '2026-10-14');
  const second = placeHold(db, '3', 'LD-0003', '2026-10-15');
  first.status = 'ready';
  const toolId = first.toolId;
  assert.deepEqual(holdsRepo.openForTool(db, toolId), [second]);
  assert.equal(holdsRepo.readyForTool(db, toolId), first);
  assert.deepEqual(holdsRepo.allReady(db), [first]);
  assert.deepEqual(holdsRepo.forMember(db, '3'), [second]);
  assert.equal(holdsRepo.byId(db, second.id), second);
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
