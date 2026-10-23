import { daysBetween } from './calendar.ts';
import { owedCents } from './fees.ts';
import { findMember, findTool, openLoans } from './store.ts';
import type { Db, Loan, Member, Tool } from './store.ts';

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
    const tool = findTool(db, loan.toolId);
    const member = findMember(db, loan.memberNo);
    if (tool && member) rows.push({ loan, tool, member, daysOverdue });
  }
  return rows.sort((a, b) => b.daysOverdue - a.daysOverdue);
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
    const tool = findTool(db, toolId);
    if (tool) rows.push({ tool, loans });
  }
  return rows.sort((a, b) => (a.loans < b.loans ? 1 : -1)).slice(0, limit);
}

export interface FeesRow {
  member: Member;
  owedCents: number;
}

// wip: still needs sorting and the route
export function feesOutstanding(db: Db): FeesRow[] {
  const totals = new Map<string, number>();
  for (const fee of db.fees) {
    totals.set(fee.memberNo, (totals.get(fee.memberNo) ?? 0) + owedCents(fee));
  }
  const rows: FeesRow[] = [];
  for (const [memberNo, owed] of totals) {
    const member = findMember(db, memberNo);
    if (member) rows.push({ member, owedCents: owed });
  }
  return rows;
}
