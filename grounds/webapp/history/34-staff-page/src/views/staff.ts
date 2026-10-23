import { escapeHtml } from './escape.ts';
import { layout } from './layout.ts';
import type { User } from '../auth.ts';
import type { Hold, Loan, Member, Tool } from '../db.ts';

export interface StaffPageData {
  dueToday: { loan: Loan; tool: Tool; member: Member }[];
  overdue: { loan: Loan; tool: Tool; member: Member; daysOverdue: number }[];
  holdsReady: { hold: Hold; tool: Tool; member: Member }[];
  waiting: { tool: Tool; count: number }[];
  search: { q: string; members: Member[] } | null;
}

function table(headings: string[], rows: string[][]): string {
  const head = headings.map((h) => `<th>${escapeHtml(h)}</th>`).join('');
  const body = rows
    .map((cells) => `<tr>${cells.map((c) => `<td>${c}</td>`).join('')}</tr>`)
    .join('\n');
  return `<table>\n<thead><tr>${head}</tr></thead>\n<tbody>\n${body}\n</tbody>\n</table>`;
}

function memberLink(member: Member): string {
  const no = escapeHtml(member.memberNo);
  return `<a href="/members/${no}">${escapeHtml(member.name)}</a> (${no})`;
}

function section(title: string, empty: string, headings: string[], rows: string[][]): string {
  const content = rows.length === 0 ? `<p class="muted">${empty}</p>` : table(headings, rows);
  return `<h2>${escapeHtml(title)}</h2>\n${content}`;
}

function searchResults(search: StaffPageData['search']): string {
  if (!search) return '';
  if (search.members.length === 0) return '<p class="muted">No members match.</p>';
  const items = search.members.map((member) => `<li>${memberLink(member)}</li>`);
  return `<ul>${items.join('')}</ul>`;
}

// Check-out, check-in and member lookup, the three things done most at the counter.
function counterForms(search: StaffPageData['search']): string {
  return `<form method="post" action="/api/loans">
<label>Member no. <input name="memberNo" required></label>
<label>Tag <input name="tag" required placeholder="PT-0042"></label>
<button>Check out</button>
</form>
<form method="post" action="/api/returns">
<label>Tag <input name="tag" required></label>
<button>Check in</button>
</form>
<form method="get" action="/staff/today">
<label>Find a member <input type="search" name="q" value="${escapeHtml(search?.q ?? '')}"></label>
<button>Search</button>
</form>
${searchResults(search)}`;
}

export function staffPage(data: StaffPageData, today: string, user: User | null): string {
  const parts = [
    counterForms(data.search),
    section(
      'Due back today',
      'Nothing is due back today.',
      ['Tag', 'Tool', 'Member'],
      data.dueToday.map(({ tool, member }) => [
        escapeHtml(tool.tag),
        escapeHtml(tool.name),
        memberLink(member),
      ]),
    ),
    section(
      'Holds ready for pickup',
      'No holds are waiting on the shelf.',
      ['Tag', 'Tool', 'For', 'Collect by'],
      data.holdsReady.map(({ hold, tool, member }) => [
        escapeHtml(tool.tag),
        escapeHtml(tool.name),
        memberLink(member),
        escapeHtml(hold.pickupBy ?? ''),
      ]),
    ),
    section(
      'Overdue',
      'Nothing is overdue.',
      ['Tag', 'Tool', 'Member', 'Phone', 'Days late'],
      data.overdue.map(({ tool, member, daysOverdue }) => [
        escapeHtml(tool.tag),
        escapeHtml(tool.name),
        memberLink(member),
        escapeHtml(member.phone),
        `<span class="overdue">${daysOverdue}</span>`,
      ]),
    ),
    section(
      'Waiting lists',
      'Nobody is waiting for anything.',
      ['Tag', 'Tool', 'Waiting'],
      data.waiting.map(({ tool, count }) => [
        escapeHtml(tool.tag),
        escapeHtml(tool.name),
        String(count),
      ]),
    ),
  ];
  return layout(`Today, ${today}`, parts.join('\n'), user);
}
