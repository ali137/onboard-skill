import { HttpError } from './http.ts';
import { daysBetween } from './calendar.ts';
import type { Db, Fee, Loan } from './db.ts';

// Cents per day late, by category.
const FEE_PER_DAY: Record<string, number> = { PT: 100, LD: 100, GD: 50, SW: 50, HT: 25 };
// Most we charge for a single loan, however late.
const FEE_CAP = 2000;
// Days after the due date before fees start.
const GRACE_DAYS = 2;

export function lateFeeCents(loan: Loan, category: string, returnedOn: string): number {
  const charged = daysBetween(loan.due, returnedOn) - GRACE_DAYS;
  if (charged <= 0) return 0;
  return Math.min(charged * FEE_PER_DAY[category], FEE_CAP);
}

export function chargeLateFee(db: Db, loan: Loan, category: string, today: string): Fee | null {
  const amountCents = lateFeeCents(loan, category, today);
  if (amountCents === 0) return null;
  db.counters.fee += 1;
  const fee: Fee = {
    id: String(db.counters.fee),
    memberNo: loan.memberNo,
    loanId: loan.id,
    amountCents,
    paidCents: 0,
    chargedOn: today,
    waived: null,
  };
  db.fees.push(fee);
  return fee;
}

export function owedCents(fee: Fee): number {
  return fee.waived ? 0 : fee.amountCents - fee.paidCents;
}

export function feesFor(db: Db, memberNo: string): Fee[] {
  return db.fees.filter((fee) => fee.memberNo === memberNo);
}

export function balanceCents(db: Db, memberNo: string): number {
  return feesFor(db, memberNo).reduce((sum, fee) => sum + owedCents(fee), 0);
}

// Pays off the oldest fees first.
export function payFees(db: Db, memberNo: string, cents: number): Fee[] {
  if (!Number.isInteger(cents) || cents <= 0) {
    throw new HttpError(400, 'payment must be a whole number of cents');
  }
  const balance = balanceCents(db, memberNo);
  if (cents > balance) {
    const owed = formatCents(balance);
    throw new HttpError(400, `payment of ${formatCents(cents)} is more than the ${owed} owed`);
  }
  let left = cents;
  const touched: Fee[] = [];
  for (const fee of feesFor(db, memberNo)) {
    const pay = Math.min(left, owedCents(fee));
    if (pay === 0) continue;
    fee.paidCents += pay;
    left -= pay;
    touched.push(fee);
  }
  return touched;
}

export function waiveFee(db: Db, feeId: string, by: string, reason: string, today: string): Fee {
  const fee = db.fees.find((f) => f.id === feeId);
  if (!fee) throw new HttpError(404, `no fee ${feeId}`);
  if (reason.trim() === '') throw new HttpError(400, 'a waiver needs a reason');
  if (fee.waived) throw new HttpError(409, `fee ${feeId} was already waived`);
  fee.waived = { by, reason: reason.trim(), on: today };
  return fee;
}

export function formatCents(cents: number): string {
  const sign = cents < 0 ? '-' : '';
  const abs = Math.abs(cents);
  return `${sign}$${Math.floor(abs / 100)}.${String(abs % 100).padStart(2, '0')}`;
}
