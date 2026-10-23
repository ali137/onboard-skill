import { HttpError } from './http.ts';
import { addDays, nextOpenDay } from './calendar.ts';
import { getMember } from './members.ts';
import { getTool } from './tools.ts';
import { chargeLateFee } from './fees.ts';
import { queueFor } from './holds.ts';
import { findLoan, findTool, insertLoan, openLoanForTool, openLoansForMember } from './store.ts';
import type { Db, Fee, Loan } from './store.ts';

const LOAN_DAYS: Record<string, number> = { PT: 7, LD: 4, GD: 7, SW: 14, HT: 14 };
const MAX_LOANS = 5;
const MAX_RENEWALS = 2;

// Due back after the category's loan period, moved to a day we are open.
export function dueDate(checkedOut: string, category: string): string {
  return nextOpenDay(addDays(checkedOut, LOAN_DAYS[category]));
}

export function checkout(db: Db, memberNo: string, tag: string, today: string): Loan {
  const member = getMember(db, memberNo);
  const tool = getTool(db, tag);
  if (tool.retired) throw new HttpError(409, `${tag} has been retired`);
  if (openLoanForTool(db, tool.id)) throw new HttpError(409, `${tag} is already out on loan`);
  const next = queueFor(db, tool.id)[0];
  if (next && next.memberNo !== member.memberNo) {
    throw new HttpError(409, `${tag} is held for member ${next.memberNo}`);
  }

  const open = openLoansForMember(db, member.memberNo);
  if (open.length >= MAX_LOANS) {
    throw new HttpError(409, `member ${memberNo} already has ${open.length} tools out`);
  }

  const loan = insertLoan(db, {
    toolId: tool.id,
    memberNo: member.memberNo,
    checkedOut: today,
    due: dueDate(today, tool.category),
    renewals: 0,
    returned: null,
  });
  if (next) next.status = 'collected';
  return loan;
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
}

export function returnTool(db: Db, tag: string, today: string): ReturnResult {
  const tool = getTool(db, tag);
  const loan = openLoanForTool(db, tool.id);
  if (!loan) throw new HttpError(409, `${tag} is not out on loan`);
  loan.returned = today;
  const fee = chargeLateFee(db, loan, tool.category, today);
  return { loan, fee };
}

export function isOverdue(loan: Loan, today: string): boolean {
  return loan.returned === null && loan.due < today;
}
