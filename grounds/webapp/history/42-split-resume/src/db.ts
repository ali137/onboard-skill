import { mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import { dirname } from 'node:path';

export interface Member {
  memberNo: string;
  name: string;
  email: string;
  phone: string;
  address: string;
  joinedOn: string;
  // older records have no suspended field at all
  suspended?: { on: string; reason: string } | null;
}

export interface Tool {
  id: string;
  tag: string;
  name: string;
  category: string;
  condition: string;
  notes: string;
  retired: boolean;
  addedOn: string;
}

export interface Loan {
  id: string;
  toolId: string;
  memberNo: string;
  checkedOut: string;
  due: string;
  renewals: number;
  returned: string | null;
}

export interface Hold {
  id: string;
  toolId: string;
  memberNo: string;
  requestedOn: string;
  status: 'waiting' | 'ready' | 'collected' | 'canceled' | 'expired';
  readyOn: string | null;
  pickupBy: string | null;
}

export interface Fee {
  id: string;
  memberNo: string;
  loanId: string;
  amountCents: number;
  paidCents: number;
  chargedOn: string;
  waived: { by: string; reason: string; on: string } | null;
}

export interface Message {
  id: string;
  memberNo: string;
  to: string;
  kind: 'hold-ready' | 'overdue';
  subject: string;
  body: string;
  createdOn: string;
}

export interface Account {
  id: string;
  username: string;
  role: 'staff' | 'member';
  memberNo: string | null;
  salt: string;
  passwordHash: string;
}

export interface Session {
  token: string;
  accountId: string;
  createdOn: string;
}

export interface Db {
  members: Member[];
  accounts: Account[];
  sessions: Session[];
  tools: Tool[];
  loans: Loan[];
  holds: Hold[];
  fees: Fee[];
  outbox: Message[];
  counters: {
    member: number;
    account: number;
    tool: number;
    loan: number;
    hold: number;
    fee: number;
    message: number;
  };
}

export function emptyDb(): Db {
  return {
    members: [],
    accounts: [],
    sessions: [],
    tools: [],
    loans: [],
    holds: [],
    fees: [],
    outbox: [],
    counters: { member: 0, account: 0, tool: 0, loan: 0, hold: 0, fee: 0, message: 0 },
  };
}

// Data files written by older versions miss fields added since; fill them in.
export function parseDb(text: string): Db {
  const data = JSON.parse(text) as Partial<Db>;
  if (typeof data !== 'object' || data === null || Array.isArray(data)) {
    throw new Error('data file must hold a JSON object');
  }
  const empty = emptyDb();
  const db: Db = { ...empty, ...data, counters: { ...empty.counters, ...data.counters } };
  for (const member of db.members) member.suspended ??= null;
  for (const hold of db.holds) {
    hold.readyOn ??= null;
    hold.pickupBy ??= null;
  }
  return db;
}

export function serializeDb(db: Db): string {
  return JSON.stringify(db, null, 2) + '\n';
}

export function loadDb(file: string): Db {
  return parseDb(readFileSync(file, 'utf8'));
}

// Write to a temporary file first so a crash never leaves half a data file.
export function saveDb(file: string, db: Db): void {
  mkdirSync(dirname(file), { recursive: true });
  const tmp = `${file}.tmp`;
  writeFileSync(tmp, serializeDb(db));
  renameSync(tmp, file);
}
