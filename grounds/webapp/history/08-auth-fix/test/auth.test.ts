import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  createAccount,
  hashPassword,
  login,
  logout,
  requireMember,
  requireStaff,
  tokenFromRequest,
  userForToken,
} from '../src/auth.ts';
import type { User } from '../src/auth.ts';
import { HttpError } from '../src/http.ts';
import { request, sampleDb } from './helpers.ts';

const TODAY = '2026-07-08';
const salt = () => 'fixed-salt';

function status(code: number) {
  return (err: unknown) => err instanceof HttpError && err.status === code;
}

test('hashes passwords with the salt', () => {
  const hash = hashPassword('correct horse', 'salt-a');
  assert.match(hash, /^[0-9a-f]{64}$/);
  assert.equal(hashPassword('correct horse', 'salt-a'), hash);
  assert.notEqual(hashPassword('correct horse', 'salt-b'), hash);
});

test('never stores the plain password', () => {
  const db = sampleDb();
  const input = { username: 'Wren', password: 'correct horse', role: 'staff' as const };
  const account = createAccount(db, input, salt);
  assert.equal(account.username, 'wren');
  assert.equal(account.salt, 'fixed-salt');
  assert.equal(account.passwordHash, hashPassword('correct horse', 'fixed-salt'));
  assert.ok(!JSON.stringify(db.accounts).includes('correct horse'));
});

test('rejects short passwords and taken usernames', () => {
  const db = sampleDb();
  createAccount(db, { username: 'wren', password: 'correct horse', role: 'staff' }, salt);
  assert.throws(
    () => createAccount(db, { username: 'pell', password: 'short', role: 'staff' }, salt),
    /at least 8 characters/,
  );
  assert.throws(
    () => createAccount(db, { username: 'WREN', password: 'correct horse', role: 'staff' }, salt),
    status(409),
  );
});

test('a member account must point at an existing member', () => {
  const db = sampleDb();
  const input = { username: 'hesper', password: 'correct horse', role: 'member' as const };
  assert.throws(() => createAccount(db, { ...input, memberNo: '77' }, salt), /no member 77/);
  assert.equal(createAccount(db, { ...input, memberNo: '1' }, salt).memberNo, '1');
});

test('logs in with the right password only', () => {
  const db = sampleDb();
  createAccount(db, { username: 'wren', password: 'correct horse', role: 'staff' });
  assert.equal(login(db, 'wren', 'wrong horse', TODAY), null);
  assert.equal(login(db, 'nobody', 'correct horse', TODAY), null);
  const session = login(db, ' Wren ', 'correct horse', TODAY, () => 'tok-1');
  assert.deepEqual(session, { token: 'tok-1', accountId: '1', createdOn: TODAY });
});

test('a session token identifies the user until it expires', () => {
  const db = sampleDb();
  createAccount(db, { username: 'wren', password: 'correct horse', role: 'staff' }, salt);
  login(db, 'wren', 'correct horse', TODAY, () => 'tok-1');
  const user = userForToken(db, 'tok-1', TODAY);
  assert.equal(user?.username, 'wren');
  assert.equal(user?.role, 'staff');
  assert.notEqual(userForToken(db, 'tok-1', '2026-07-22'), null);
  assert.equal(userForToken(db, 'tok-1', '2026-07-23'), null);
  assert.equal(userForToken(db, 'nope', TODAY), null);
});

test('logout ends the session', () => {
  const db = sampleDb();
  createAccount(db, { username: 'wren', password: 'correct horse', role: 'staff' }, salt);
  login(db, 'wren', 'correct horse', TODAY, () => 'tok-1');
  logout(db, 'tok-1');
  assert.equal(userForToken(db, 'tok-1', TODAY), null);
});

test('logging out with a stale token leaves other sessions alone', () => {
  const db = sampleDb();
  createAccount(db, { username: 'wren', password: 'correct horse', role: 'staff' }, salt);
  login(db, 'wren', 'correct horse', TODAY, () => 'tok-1');
  logout(db, 'tok-already-gone');
  assert.equal(userForToken(db, 'tok-1', TODAY)?.username, 'wren');
});

test('reads the token from a bearer header or the session cookie', () => {
  assert.equal(tokenFromRequest(request('GET', '/', { token: 'abc' })), 'abc');
  const withCookie = { ...request('GET', '/'), headers: { cookie: 'theme=dark; session=xyz=' } };
  assert.equal(tokenFromRequest(withCookie), 'xyz=');
  assert.equal(tokenFromRequest(request('GET', '/')), null);
});

test('staff and member checks', () => {
  const staff: User = { accountId: '1', username: 'wren', role: 'staff', memberNo: null };
  const member: User = { accountId: '2', username: 'hesper', role: 'member', memberNo: '1' };
  assert.throws(() => requireStaff(null), status(401));
  assert.throws(() => requireStaff(member), status(403));
  assert.equal(requireStaff(staff), staff);
  assert.equal(requireMember(member, '1'), member);
  assert.equal(requireMember(staff, '1'), staff);
  assert.throws(() => requireMember(member, '2'), status(403));
});
