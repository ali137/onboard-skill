import { escapeHtml } from './escape.ts';
import { layout } from './layout.ts';
import type { User } from '../auth.ts';
import type { Loan, Member, Tool } from '../store.ts';
import { formatCents } from '../fees.ts';

export interface MemberPageData {
  member: Member;
  loans: { loan: Loan; tool: Tool }[];
  balanceCents: number;
}

function loanRows(loans: MemberPageData['loans'], today: string): string {
  return loans
    .map(({ loan, tool }) => {
      const overdue = loan.due < today;
      const due = overdue
        ? `<span class="overdue">${escapeHtml(loan.due)} (overdue)</span>`
        : escapeHtml(loan.due);
      return `<tr><td>${escapeHtml(tool.tag)}</td><td>${escapeHtml(tool.name)}</td>` +
        `<td>${due}</td><td>${loan.renewals}</td></tr>`;
    })
    .join('\n');
}

export function memberPage(data: MemberPageData, today: string, user: User | null): string {
  const { member } = data;
  const contact = `${escapeHtml(member.email)} · ${escapeHtml(member.phone)}`;
  const parts = [
    `<p>Member no. ${escapeHtml(member.memberNo)} · joined ${escapeHtml(member.joinedOn)}</p>`,
    `<p>${contact}<br>${escapeHtml(member.address)}</p>`,
    '<h2>On loan</h2>',
  ];
  if (data.loans.length === 0) {
    parts.push('<p>Nothing out at the moment.</p>');
  } else {
    parts.push(`<table>
<thead><tr><th>Tag</th><th>Tool</th><th>Due</th><th>Renewals</th></tr></thead>
<tbody>
${loanRows(data.loans, today)}
</tbody>
</table>`);
  }
  if (data.balanceCents > 0) {
    parts.push(`<p>Fees owed: <strong>${formatCents(data.balanceCents)}</strong></p>`);
  }
  return layout(member.name, parts.join('\n'), user);
}
