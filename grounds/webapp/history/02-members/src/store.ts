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

export interface Db {
  members: Member[];
  counters: { member: number };
}

export function emptyDb(): Db {
  return { members: [], counters: { member: 0 } };
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
