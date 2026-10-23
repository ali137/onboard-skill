import type { Db, Member } from '../db.ts';

export function byNumber(db: Db, memberNo: string): Member | undefined {
  return db.members.find((member) => member.memberNo === memberNo);
}

export function all(db: Db): Member[] {
  return db.members;
}

export function insert(db: Db, member: Member): Member {
  db.members.push(member);
  return member;
}

// Paper-era members keep their old numbers, so skip any number already taken.
export function nextNumber(db: Db): string {
  let n = db.counters.member;
  do {
    n += 1;
  } while (byNumber(db, String(n)));
  db.counters.member = n;
  return String(n);
}
