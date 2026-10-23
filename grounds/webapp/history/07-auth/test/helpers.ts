import { emptyDb } from '../src/store.ts';
import type { Db, Member } from '../src/store.ts';
import { registerMember } from '../src/members.ts';
import { addTool } from '../src/tools.ts';
import { createAccount, login } from '../src/auth.ts';
import type { AppRequest } from '../src/http.ts';

export function addMember(db: Db, name: string, memberNo?: string): Member {
  const email = `${name.toLowerCase().replace(/[^a-z]+/g, '.')}@hollyfen.example`;
  const contact = { email, phone: '01632 960 000', address: '1 Gorse Row, Tallowmere' };
  return registerMember(db, { name, ...contact, memberNo }, '2026-07-01');
}

// Members 1 and 2 and a handful of tools.
export function sampleDb(): Db {
  const db = emptyDb();
  addMember(db, 'Hesper Lund');
  addMember(db, 'Odo Pickering');
  const tools = [
    ['PT-0001', 'Cordless drill', 'PT'],
    ['PT-0011', 'Pressure washer', 'PT'],
    ['LD-0003', 'Extension ladder', 'LD'],
    ['GD-0005', 'Hedge trimmer', 'GD'],
    ['SW-0001', 'Sewing machine', 'SW'],
  ];
  for (const [tag, name, category] of tools) addTool(db, { tag, name, category }, '2026-07-01');
  return db;
}

// Creates an account and a session with a known token.
export function signIn(db: Db, username: string, memberNo?: string): string {
  const role = memberNo ? 'member' : 'staff';
  createAccount(db, { username, password: 'correct horse', role, memberNo }, () => 'salt');
  const session = login(db, username, 'correct horse', '2026-07-01', () => `token-${username}`);
  if (!session) throw new Error('sign in failed');
  return session.token;
}

interface RequestOptions {
  token?: string;
  body?: Record<string, unknown>;
  form?: boolean;
  query?: Record<string, string>;
}

export function request(method: string, path: string, options: RequestOptions = {}): AppRequest {
  const headers: Record<string, string> = {};
  if (options.token) headers['authorization'] = `Bearer ${options.token}`;
  let body = '';
  if (options.body && options.form) {
    headers['content-type'] = 'application/x-www-form-urlencoded';
    body = new URLSearchParams(options.body as Record<string, string>).toString();
  } else if (options.body) {
    headers['content-type'] = 'application/json';
    body = JSON.stringify(options.body);
  }
  return { method, path, query: options.query ?? {}, headers, body };
}
