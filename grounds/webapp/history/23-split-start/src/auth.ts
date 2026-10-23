import { randomBytes, scryptSync, timingSafeEqual } from 'node:crypto';
import { HttpError } from './http.ts';
import type { AppRequest } from './http.ts';
import { addDays } from './calendar.ts';
import * as membersRepo from './repos/members.ts';
import type { Account, Db, Session } from './db.ts';

const SESSION_DAYS = 14;
const MIN_PASSWORD_LENGTH = 8;
const USERNAME = /^[a-z0-9._-]{3,32}$/;

export type Role = Account['role'];

export interface User {
  accountId: string;
  username: string;
  role: Role;
  memberNo: string | null;
}

export interface AccountInput {
  username: string;
  password: string;
  role: Role;
  memberNo?: string;
}

export function newSalt(): string {
  return randomBytes(16).toString('hex');
}

export function newToken(): string {
  return randomBytes(24).toString('base64url');
}

export function hashPassword(password: string, salt: string): string {
  return scryptSync(password, salt, 32).toString('hex');
}

function passwordMatches(account: Account, password: string): boolean {
  const expected = Buffer.from(account.passwordHash, 'hex');
  const actual = scryptSync(password, account.salt, expected.length);
  return timingSafeEqual(expected, actual);
}

export function createAccount(db: Db, input: AccountInput, makeSalt = newSalt): Account {
  const username = input.username.trim().toLowerCase();
  if (!USERNAME.test(username)) throw new HttpError(400, `bad username "${input.username}"`);
  if (db.accounts.some((account) => account.username === username)) {
    throw new HttpError(409, `username ${username} is taken`);
  }
  if (input.password.length < MIN_PASSWORD_LENGTH) {
    throw new HttpError(400, `passwords need at least ${MIN_PASSWORD_LENGTH} characters`);
  }
  let memberNo: string | null = null;
  if (input.role === 'member') {
    if (!input.memberNo || !membersRepo.byNumber(db, input.memberNo)) {
      throw new HttpError(400, `no member ${input.memberNo ?? ''} to link the account to`);
    }
    memberNo = input.memberNo;
  }
  const salt = makeSalt();
  db.counters.account += 1;
  const account: Account = {
    id: String(db.counters.account),
    username,
    role: input.role,
    memberNo,
    salt,
    passwordHash: hashPassword(input.password, salt),
  };
  db.accounts.push(account);
  return account;
}

export function login(
  db: Db,
  username: string,
  password: string,
  today: string,
  makeToken = newToken,
): Session | null {
  const account = db.accounts.find((a) => a.username === username.trim().toLowerCase());
  if (!account || !passwordMatches(account, password)) return null;
  const session: Session = { token: makeToken(), accountId: account.id, createdOn: today };
  db.sessions.push(session);
  return session;
}

export function logout(db: Db, token: string): void {
  const index = db.sessions.findIndex((session) => session.token === token);
  if (index !== -1) db.sessions.splice(index, 1);
}

export function userForToken(db: Db, token: string, today: string): User | null {
  const session = db.sessions.find((s) => s.token === token);
  if (!session || addDays(session.createdOn, SESSION_DAYS) < today) return null;
  const account = db.accounts.find((a) => a.id === session.accountId);
  if (!account) return null;
  return {
    accountId: account.id,
    username: account.username,
    role: account.role,
    memberNo: account.memberNo,
  };
}

// Browsers send the session cookie; scripts can use a bearer token.
export function tokenFromRequest(req: AppRequest): string | null {
  const auth = req.headers['authorization'];
  if (auth?.startsWith('Bearer ')) return auth.slice('Bearer '.length).trim();
  for (const part of (req.headers['cookie'] ?? '').split(';')) {
    const [name, ...value] = part.trim().split('=');
    if (name === 'session') return value.join('=');
  }
  return null;
}

export function requireUser(user: User | null): User {
  if (!user) throw new HttpError(401, 'please log in');
  return user;
}

export function requireStaff(user: User | null): User {
  const current = requireUser(user);
  if (current.role !== 'staff') throw new HttpError(403, 'staff only');
  return current;
}

// Staff can act for any member; a member only for themselves.
export function requireMember(user: User | null, memberNo: string): User {
  const current = requireUser(user);
  if (current.role === 'staff' || current.memberNo === memberNo) return current;
  throw new HttpError(403, 'not your account');
}
