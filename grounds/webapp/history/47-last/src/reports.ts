import { daysBetween } from './calendar.ts';
import { owedCents } from './fees.ts';
import * as membersRepo from './repos/members.ts';
import * as toolsRepo from './repos/tools.ts';
import { openLoans } from './store.ts';
import type { Db, Loan, Member, Tool } from './db.ts';

export interface OverdueRow {
  loan: Loan;
  tool: Tool;
  member: Member;
  daysOverdue: number;
}

// Most overdue first.
export function overdueLoans(db: Db, today: string): OverdueRow[] {
  const rows: OverdueRow[] = [];
  for (const loan of openLoans(db)) {
    const daysOverdue = daysBetween(loan.due, today);
    if (daysOverdue <= 0) continue;
    const tool = toolsRepo.byId(db, loan.toolId);
    const member = membersRepo.byNumber(db, loan.memberNo);
    if (tool && member) rows.push({ loan, tool, member, daysOverdue });
  }
  return rows.sort(
    (a, b) => b.daysOverdue - a.daysOverdue || a.tool.tag.localeCompare(b.tool.tag),
  );
}

// Loans due back on the given day, for the staff page.
export function loansDueOn(db: Db, date: string): { loan: Loan; tool: Tool; member: Member }[] {
  return openLoans(db)
    .filter((loan) => loan.due === date)
    .flatMap((loan) => {
      const tool = toolsRepo.byId(db, loan.toolId);
      const member = membersRepo.byNumber(db, loan.memberNo);
      return tool && member ? [{ loan, tool, member }] : [];
    });
}

export interface PopularRow {
  tool: Tool;
  loans: number;
}

export interface PopularOptions {
  from?: string;
  to?: string;
  limit?: number;
}

// Loans checked out between from and to, both inclusive.
export function mostBorrowed(db: Db, options: PopularOptions = {}): PopularRow[] {
  const { from = '0000-01-01', to = '9999-12-31', limit = 10 } = options;
  const counts = new Map<string, number>();
  for (const loan of db.loans) {
    if (loan.checkedOut < from || loan.checkedOut > to) continue;
    counts.set(loan.toolId, (counts.get(loan.toolId) ?? 0) + 1);
  }
  const rows: PopularRow[] = [];
  for (const [toolId, loans] of counts) {
    const tool = toolsRepo.byId(db, toolId);
    if (tool) rows.push({ tool, loans });
  }
  rows.sort((a, b) => b.loans - a.loans || a.tool.tag.localeCompare(b.tool.tag));
  return rows.slice(0, limit);
}

export interface FeesRow {
  member: Member;
  owedCents: number;
}

// Members who owe anything, biggest balance first.
export function feesOutstanding(db: Db): FeesRow[] {
  const totals = new Map<string, number>();
  for (const fee of db.fees) {
    totals.set(fee.memberNo, (totals.get(fee.memberNo) ?? 0) + owedCents(fee));
  }
  const rows: FeesRow[] = [];
  for (const [memberNo, owed] of totals) {
    const member = membersRepo.byNumber(db, memberNo);
    if (member && owed > 0) rows.push({ member, owedCents: owed });
  }
  return rows.sort(
    (a, b) => b.owedCents - a.owedCents || a.member.name.localeCompare(b.member.name),
  );
}
