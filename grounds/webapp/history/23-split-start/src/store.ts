// TODO: this file is being split up into src/repos/ (one file per entity) so
// the services stop reaching into the whole Db. Members are done. -wren
import type { Db, Hold, Loan, Tool } from './db.ts';

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

export function findHold(db: Db, id: string): Hold | undefined {
  return db.holds.find((hold) => hold.id === id);
}

export function holdsForMember(db: Db, memberNo: string): Hold[] {
  return db.holds.filter((hold) => hold.memberNo === memberNo);
}

export function openHoldsForTool(db: Db, toolId: string): Hold[] {
  return db.holds.filter((hold) => hold.toolId === toolId && hold.status === 'waiting');
}

export function readyHoldForTool(db: Db, toolId: string): Hold | undefined {
  return db.holds.find((hold) => hold.toolId === toolId && hold.status === 'ready');
}

export function insertHold(db: Db, hold: Omit<Hold, 'id'>): Hold {
  db.counters.hold += 1;
  const stored = { id: String(db.counters.hold), ...hold };
  db.holds.push(stored);
  return stored;
}
