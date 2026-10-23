import { HttpError } from './http.ts';
import * as membersRepo from './repos/members.ts';
import type { Db, Member } from './db.ts';

export interface MemberInput {
  name: string;
  email: string;
  phone: string;
  address: string;
  memberNo?: string;
}

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE = /^\+?[\d ()-]{6,20}$/;
const MEMBER_NO = /^[1-9]\d*$/;

function required(value: unknown, field: string): string {
  if (typeof value !== 'string' || value.trim() === '') {
    throw new HttpError(400, `${field} is required`);
  }
  return value.trim();
}

function checkContact(email: string, phone: string): void {
  if (!EMAIL.test(email)) throw new HttpError(400, `"${email}" is not an email address`);
  if (!PHONE.test(phone)) throw new HttpError(400, `"${phone}" is not a phone number`);
}

export function registerMember(db: Db, input: MemberInput, today: string): Member {
  const name = required(input.name, 'name');
  const email = required(input.email, 'email').toLowerCase();
  const phone = required(input.phone, 'phone');
  const address = required(input.address, 'address');
  checkContact(email, phone);

  let memberNo: string;
  if (input.memberNo !== undefined) {
    // Members moving over from the paper cards keep their number.
    memberNo = input.memberNo.trim();
    if (!MEMBER_NO.test(memberNo)) throw new HttpError(400, `bad member number "${memberNo}"`);
    if (membersRepo.byNumber(db, memberNo)) {
      throw new HttpError(409, `member ${memberNo} already exists`);
    }
  } else {
    memberNo = membersRepo.nextNumber(db);
  }
  return membersRepo.insert(db, { memberNo, name, email, phone, address, joinedOn: today });
}

export function getMember(db: Db, memberNo: string): Member {
  const member = membersRepo.byNumber(db, memberNo);
  if (!member) throw new HttpError(404, `no member ${memberNo}`);
  return member;
}

export function updateMember(db: Db, memberNo: string, changes: Partial<MemberInput>): Member {
  const member = getMember(db, memberNo);
  const next = {
    name: changes.name === undefined ? member.name : required(changes.name, 'name'),
    email: changes.email === undefined ? member.email : required(changes.email, 'email'),
    phone: changes.phone === undefined ? member.phone : required(changes.phone, 'phone'),
    address: changes.address === undefined ? member.address : required(changes.address, 'address'),
  };
  next.email = next.email.toLowerCase();
  checkContact(next.email, next.phone);
  Object.assign(member, next);
  return member;
}

export function findMembers(db: Db, text: string): Member[] {
  const needle = text.trim().toLowerCase();
  if (needle === '') return [];
  return membersRepo.all(db).filter(
    (member) =>
      member.memberNo === needle ||
      member.name.toLowerCase().includes(needle) ||
      member.email.includes(needle),
  );
}
