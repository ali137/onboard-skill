import { HttpError } from './http.ts';
import { dueDateFrom, formatDate, toDate } from './calendar.ts';
import { getMember } from './members.ts';
import { getTool } from './tools.ts';
import { chargeLateFee } from './fees.ts';
import { insertLoan, openLoanForTool, openLoansForMember } from './store.ts';
import type { Db, Fee, Loan } from './store.ts';

const LOAN_DAYS: Record<string, number> = { PT: 7, LD: 4, GD: 7, SW: 14, HT: 14 };
const MAX_LOANS = 5;

// Due back after the category's loan period, moved to a day we are open.
export function dueDate(checkedOut: string, category: string): string {
  return formatDate(dueDateFrom(toDate(checkedOut), LOAN_DAYS[category]));
}

export function checkout(db: Db, memberNo: string, tag: string, today: string): Loan {
  const member = getMember(db, memberNo);
  const tool = getTool(db, tag);
  if (tool.retired) throw new HttpError(409, `${tag} has been retired`);
  if (openLoanForTool(db, tool.id)) throw new HttpError(409, `${tag} is already out on loan`);

  const open = openLoansForMember(db, member.memberNo);
  if (open.length >= MAX_LOANS) {
    throw new HttpError(409, `member ${memberNo} already has ${open.length} tools out`);
  }

  return insertLoan(db, {
    toolId: tool.id,
    memberNo: member.memberNo,
    checkedOut: today,
    due: dueDate(today, tool.category),
    returned: null,
  });
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
