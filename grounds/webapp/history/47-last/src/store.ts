// TODO(pell): finish the split. Loans are the last thing left in here: move them
// to src/repos/loans.ts like members/tools/holds, switch the callers (loans.ts,
// reports.ts, routes/loans.ts), then delete this file. Done when store.ts is gone
// and `npm test` is green.
import type { Db, Loan } from './db.ts';

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
