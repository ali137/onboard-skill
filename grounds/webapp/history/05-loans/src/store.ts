import { mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import { dirname } from 'node:path';

export interface Member {
  memberNo: string;
  name: string;
  email: string;
  phone: string;
  address: string;
  joinedOn: string;
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
  returned: string | null;
}

export interface Db {
  members: Member[];
  tools: Tool[];
  loans: Loan[];
  counters: { member: number; tool: number; loan: number };
}

export function emptyDb(): Db {
  return { members: [], tools: [], loans: [], counters: { member: 0, tool: 0, loan: 0 } };
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

export function findMember(db: Db, memberNo: string): Member | undefined {
  return db.members.find((member) => member.memberNo === memberNo);
}

export function allMembers(db: Db): Member[] {
  return db.members;
}

export function insertMember(db: Db, member: Member): Member {
  db.members.push(member);
  return member;
}

// Paper-era members keep their old numbers, so skip any number already taken.
export function nextMemberNo(db: Db): string {
  let n = db.counters.member;
  do {
    n += 1;
  } while (findMember(db, String(n)));
  db.counters.member = n;
  return String(n);
}

export function findTool(db: Db, id: string): Tool | undefined {
  return db.tools.find((tool) => tool.id === id);
}

export function findToolByTag(db: Db, tag: string): Tool | undefined {
  return db.tools.find((tool) => tool.tag === tag);
}

export function allTools(db: Db): Tool[] {
  return db.tools;
}

export function insertTool(db: Db, tool: Omit<Tool, 'id'>): Tool {
  db.counters.tool += 1;
  const stored = { id: String(db.counters.tool), ...tool };
  db.tools.push(stored);
  return stored;
}

export function findLoan(db: Db, id: string): Loan | undefined {
  return db.loans.find((loan) => loan.id === id);
}

export function openLoans(db: Db): Loan[] {
  return db.loans.filter((loan) => loan.returned === null);
}

export function openLoanForTool(db: Db, toolId: string): Loan | undefined {
  return db.loans.find((loan) => loan.toolId === toolId && loan.returned === null);
}

export function openLoansForMember(db: Db, memberNo: string): Loan[] {
  return openLoans(db).filter((loan) => loan.memberNo === memberNo);
}

export function insertLoan(db: Db, loan: Omit<Loan, 'id'>): Loan {
  db.counters.loan += 1;
  const stored = { id: String(db.counters.loan), ...loan };
  db.loans.push(stored);
  return stored;
}
