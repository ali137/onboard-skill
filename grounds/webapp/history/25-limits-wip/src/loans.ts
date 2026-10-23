import { HttpError } from './http.ts';
import { addDays, nextOpenDay } from './calendar.ts';
import { getMember } from './members.ts';
import { CATEGORIES, getTool } from './tools.ts';
import { chargeLateFee } from './fees.ts';
import { collectHolds, promoteNextHold } from './holds.ts';
import {
  findLoan,
  findTool,
  insertLoan,
  openLoanForTool,
  openLoansForMember,
  readyHoldForTool,
} from './store.ts';
import type { Db, Fee, Hold, Loan } from './db.ts';

const LOAN_DAYS: Record<string, number> = { PT: 7, LD: 4, GD: 7, SW: 14, HT: 14 };
const MAX_LOANS = 5;
const MAX_RENEWALS = 2;
// Most tools of one category a member can have out at once.
const CATEGORY_LIMITS: Record<string, number> = { PT: 2, LD: 1, GD: 3, SW: 1, HT: 4 };

// Due back after the category's loan period, moved to a day we are open.
export function dueDate(checkedOut: string, category: string): string {
  return nextOpenDay(addDays(checkedOut, LOAN_DAYS[category]));
}

export function checkout(db: Db, memberNo: string, tag: string, today: string): Loan {
  const member = getMember(db, memberNo);
  const tool = getTool(db, tag);
  if (tool.retired) throw new HttpError(409, `${tag} has been retired`);
  if (openLoanForTool(db, tool.id)) throw new HttpError(409, `${tag} is already out on loan`);
  const ready = readyHoldForTool(db, tool.id);
  if (ready && ready.memberNo !== member.memberNo) {
    throw new HttpError(409, `${tag} is on the hold shelf for member ${ready.memberNo}`);
  }

  const allowance = loanAllowance(db, member.memberNo);
  if (allowance.total <= 0) {
    throw new HttpError(409, `member ${memberNo} already has ${MAX_LOANS} tools out`);
  }
  if (allowance.byCategory[tool.category] <= 0) {
    const what = CATEGORIES[tool.category].toLowerCase();
    const limit = CATEGORY_LIMITS[tool.category];
    throw new HttpError(409, `member ${memberNo} can't borrow more ${what} (limit ${limit})`);
  }

  const loan = insertLoan(db, {
    toolId: tool.id,
    memberNo: member.memberNo,
    checkedOut: today,
    due: dueDate(today, tool.category),
    renewals: 0,
    returned: null,
  });
  collectHolds(db, tool.id, member.memberNo);
  return loan;
}

export interface Allowance {
  total: number;
  byCategory: Record<string, number>;
}

// How many more tools the member may borrow, overall and per category.
export function loanAllowance(db: Db, memberNo: string): Allowance {
  const open = openLoansForMember(db, memberNo);
  const byCategory = { ...CATEGORY_LIMITS };
  for (const loan of open) {
    const category = findTool(db, loan.toolId)?.category;
    if (category) byCategory[category] -= 1;
  }
  return { total: MAX_LOANS - open.length, byCategory };
}

export function getLoan(db: Db, loanId: string): Loan {
  const loan = findLoan(db, loanId);
  if (!loan) throw new HttpError(404, `no loan ${loanId}`);
  return loan;
}

// Another loan period, counted from the current due date.
export function renew(db: Db, loanId: string, today: string): Loan {
  const loan = getLoan(db, loanId);
  if (loan.returned !== null) throw new HttpError(409, `loan ${loanId} is already returned`);
  if (isOverdue(loan, today)) {
    throw new HttpError(409, `loan ${loanId} is overdue; bring the tool in to renew it`);
  }
  if (loan.renewals >= MAX_RENEWALS) {
    throw new HttpError(409, `loan ${loanId} has been renewed ${MAX_RENEWALS} times already`);
  }
  const tool = findTool(db, loan.toolId);
  if (!tool) throw new HttpError(500, `loan ${loanId} points at a missing tool`);
  loan.due = dueDate(loan.due, tool.category);
  loan.renewals += 1;
  return loan;
}

export interface ReturnResult {
  loan: Loan;
  fee: Fee | null;
  hold: Hold | null;
}

export function returnTool(db: Db, tag: string, today: string): ReturnResult {
  const tool = getTool(db, tag);
  const loan = openLoanForTool(db, tool.id);
  if (!loan) throw new HttpError(409, `${tag} is not out on loan`);
  loan.returned = today;
  const fee = chargeLateFee(db, loan, tool.category, today);
  const hold = promoteNextHold(db, tool.id, today);
  return { loan, fee, hold };
}

export function isOverdue(loan: Loan, today: string): boolean {
  return loan.returned === null && loan.due < today;
}
