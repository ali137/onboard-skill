import { daysBetween } from './calendar.ts';
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

export function mostBorrowed(db: Db, limit = 10): PopularRow[] {
  const counts = new Map<string, number>();
  for (const loan of db.loans) counts.set(loan.toolId, (counts.get(loan.toolId) ?? 0) + 1);
  const rows: PopularRow[] = [];
  for (const [toolId, loans] of counts) {
    const tool = findTool(db, toolId);
    if (tool) rows.push({ tool, loans });
  }
  return rows.sort((a, b) => (a.loans < b.loans ? 1 : -1)).slice(0, limit);
}
