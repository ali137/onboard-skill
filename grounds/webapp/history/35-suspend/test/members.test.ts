import { test } from 'node:test';
import assert from 'node:assert/strict';
import { emptyDb } from '../src/db.ts';
import {
  findMembers,
  getMember,
  isSuspended,
  registerMember,
  reinstateMember,
  suspendMember,
  updateMember,
} from '../src/members.ts';
import { HttpError } from '../src/http.ts';

const TODAY = '2026-06-30';

function input(name: string, extra: Record<string, string> = {}) {
  const handle = name.toLowerCase().replace(/[^a-z]+/g, '.');
  return {
    name,
    email: `${handle}@hollyfen.example`,
    phone: '01632 960 000',
    address: '1 Gorse Row, Tallowmere',
    ...extra,
  };
}

test('issues member numbers in sequence starting at 1', () => {
  const db = emptyDb();
  assert.equal(registerMember(db, input('Hesper Lund'), TODAY).memberNo, '1');
  assert.equal(registerMember(db, input('Odo Pickering'), TODAY).memberNo, '2');
  assert.equal(registerMember(db, input('Ruth Amberley'), TODAY).memberNo, '3');
});

test('keeps the old number of a member moved over from the paper cards', () => {
  const db = emptyDb();
  const member = registerMember(db, input('Bettany Crull', { memberNo: '387' }), TODAY);
  assert.equal(member.memberNo, '387');
  assert.equal(getMember(db, '387').name, 'Bettany Crull');
});

test('skips numbers already taken by paper-card members', () => {
  const db = emptyDb();
  registerMember(db, input('Bettany Crull', { memberNo: '2' }), TODAY);
  assert.equal(registerMember(db, input('Hesper Lund'), TODAY).memberNo, '1');
  assert.equal(registerMember(db, input('Odo Pickering'), TODAY).memberNo, '3');
});

test('rejects member numbers with leading zeros or letters', () => {
  const db = emptyDb();
  for (const memberNo of ['0042', 'A12', '0', '']) {
    assert.throws(
      () => registerMember(db, input('Hesper Lund', { memberNo }), TODAY),
      (err: unknown) => err instanceof HttpError && err.status === 400,
    );
  }
});

test('rejects a number that is already in use', () => {
  const db = emptyDb();
  registerMember(db, input('Hesper Lund', { memberNo: '1042' }), TODAY);
  assert.throws(
    () => registerMember(db, input('Odo Pickering', { memberNo: '1042' }), TODAY),
    /member 1042 already exists/,
  );
});

test('requires name, email, phone and address', () => {
  const db = emptyDb();
  assert.throws(() => registerMember(db, input('  '), TODAY), /name is required/);
  assert.throws(
    () => registerMember(db, input('Hesper Lund', { email: 'hesper' }), TODAY),
    /not an email address/,
  );
  assert.throws(
    () => registerMember(db, input('Hesper Lund', { phone: 'call me' }), TODAY),
    /not a phone number/,
  );
});

test('stores emails in lower case and trims fields', () => {
  const db = emptyDb();
  const member = registerMember(
    db,
    input(' Hesper Lund ', { email: 'Hesper@Hollyfen.example' }),
    TODAY,
  );
  assert.equal(member.name, 'Hesper Lund');
  assert.equal(member.email, 'hesper@hollyfen.example');
  assert.equal(member.joinedOn, TODAY);
});

test('updates contact details', () => {
  const db = emptyDb();
  registerMember(db, input('Hesper Lund'), TODAY);
  const member = updateMember(db, '1', { phone: '01632 960 999', address: '8 Weir Close' });
  assert.equal(member.phone, '01632 960 999');
  assert.equal(member.address, '8 Weir Close');
  assert.equal(member.name, 'Hesper Lund');
});

test('looking up an unknown member is a 404', () => {
  assert.throws(
    () => getMember(emptyDb(), '99'),
    (err: unknown) => err instanceof HttpError && err.status === 404,
  );
});

test('finds members by number, name or email', () => {
  const db = emptyDb();
  registerMember(db, input('Hesper Lund'), TODAY);
  registerMember(db, input('Odo Pickering'), TODAY);
  assert.deepEqual(findMembers(db, 'pick').map((m) => m.memberNo), ['2']);
  assert.deepEqual(findMembers(db, '1').map((m) => m.name), ['Hesper Lund']);
  assert.deepEqual(findMembers(db, ' '), []);
});

test('suspends a member with a reason and reinstates them', () => {
  const db = emptyDb();
  registerMember(db, input('Hesper Lund'), TODAY);
  const member = suspendMember(db, '1', ' ladder never came back ', '2026-09-19');
  assert.deepEqual(member.suspended, { on: '2026-09-19', reason: 'ladder never came back' });
  assert.equal(isSuspended(member), true);
  reinstateMember(db, '1');
  assert.equal(isSuspended(getMember(db, '1')), false);
});

test('a suspension needs a reason and cannot be doubled', () => {
  const db = emptyDb();
  registerMember(db, input('Hesper Lund'), TODAY);
  assert.throws(() => suspendMember(db, '1', '', '2026-09-19'), /say why/);
  suspendMember(db, '1', 'unpaid fees', '2026-09-19');
  assert.throws(() => suspendMember(db, '1', 'again', '2026-09-20'), /already suspended/);
});

test('reinstating a member who is not suspended is a conflict', () => {
  const db = emptyDb();
  registerMember(db, input('Hesper Lund'), TODAY);
  assert.throws(() => reinstateMember(db, '1'), /is not suspended/);
});

test('members from before suspensions existed count as not suspended', () => {
  const db = emptyDb();
  const member = registerMember(db, input('Bettany Crull', { memberNo: '387' }), TODAY);
  delete member.suspended;
  assert.equal(isSuspended(member), false);
});
