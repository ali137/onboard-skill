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

export function loadDb(file: string): Db {
  const data = JSON.parse(readFileSync(file, 'utf8')) as Partial<Db>;
  const empty = emptyDb();
  return { ...empty, ...data, counters: { ...empty.counters, ...data.counters } };
}

export function saveDb(file: string, db: Db): void {
  mkdirSync(dirname(file), { recursive: true });
  const tmp = `${file}.tmp`;
  writeFileSync(tmp, JSON.stringify(db, null, 2) + '\n');
  renameSync(tmp, file);
}
