// Loan rules and fees as set by the library board. Ask Wren before changing them.

export interface CategoryRules {
  name: string;
  loanDays: number;
  // most tools of this category one member can have out at once
  maxPerMember: number;
  feePerDayCents: number;
}

export const categories: Record<string, CategoryRules> = {
  PT: { name: 'Power tools', loanDays: 7, maxPerMember: 2, feePerDayCents: 100 },
  LD: { name: 'Ladders', loanDays: 4, maxPerMember: 1, feePerDayCents: 100 },
  GD: { name: 'Garden', loanDays: 7, maxPerMember: 3, feePerDayCents: 50 },
  SW: { name: 'Sewing', loanDays: 14, maxPerMember: 1, feePerDayCents: 50 },
  HT: { name: 'Hand tools', loanDays: 14, maxPerMember: 4, feePerDayCents: 25 },
};

export const config = {
  maxLoansPerMember: 5,
  maxRenewals: 2,
  // days after the due date before late fees start
  graceDays: 2,
  // most we charge for a single loan, however late
  feeCapCents: 2000,
  // no checkouts while a member owes this much or more
  feeBlockCents: 1000,
  // open days a member has to collect a tool put aside for them
  holdPickupDays: 3,
  // 0 = Sunday; open Tuesday to Saturday
  closedWeekdays: [0, 1],
  closures: [
    '2026-08-29',
    '2026-12-24',
    '2026-12-25',
    '2026-12-26',
    '2026-12-31',
    '2027-01-01',
    '2027-01-02',
  ],
};
