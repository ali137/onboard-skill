import { daysBetween } from './calendar.ts';
import { findMember, findTool, openLoans } from './store.ts';
import type { Db, Hold, Loan, Member, Message, Tool } from './store.ts';

// TODO: send these by email once the library has an SMTP account (ask Wren)

const SIGNATURE = 'Tallowmere Tool Library';
const REMIND_EVERY_DAYS = 7;

interface Draft {
  subject: string;
  body: string;
}

export function queueMessage(
  db: Db,
  member: Member,
  kind: Message['kind'],
  draft: Draft,
  today: string,
): Message {
  db.counters.message += 1;
  const message: Message = {
    id: String(db.counters.message),
    memberNo: member.memberNo,
    to: member.email,
    kind,
    subject: draft.subject,
    body: draft.body,
    createdOn: today,
  };
  db.outbox.push(message);
  return message;
}

export function holdReadyMessage(member: Member, tool: Tool, hold: Hold): Draft {
  return {
    subject: `Ready to collect: ${tool.name}`,
    body: [
      `Hello ${member.name},`,
      '',
      `The ${tool.name} (${tool.tag}) you asked for is back and we have put it aside for you.`,
      `Please collect it by ${hold.pickupBy}.`,
      '',
      SIGNATURE,
    ].join('\n'),
  };
}

export function overdueMessage(member: Member, items: { loan: Loan; tool: Tool }[]): Draft {
  const lines = items.map(({ loan, tool }) => `- ${tool.name} (${tool.tag}), due ${loan.due}`);
  return {
    subject: items.length === 1 ? 'A tool is overdue' : `${items.length} tools are overdue`,
    body: [
      `Hello ${member.name},`,
      '',
      'These are past their due date:',
      ...lines,
      '',
      'Please bring them back or renew them at the counter. Late fees apply after two days.',
      '',
      SIGNATURE,
    ].join('\n'),
  };
}

export function notifyHoldReady(db: Db, hold: Hold, today: string): Message | null {
  const member = findMember(db, hold.memberNo);
  const tool = findTool(db, hold.toolId);
  if (!member || !tool) return null;
  return queueMessage(db, member, 'hold-ready', holdReadyMessage(member, tool, hold), today);
}

function remindedRecently(db: Db, memberNo: string, today: string): boolean {
  return db.outbox.some(
    (message) =>
      message.kind === 'overdue' &&
      message.memberNo === memberNo &&
      daysBetween(message.createdOn, today) < REMIND_EVERY_DAYS,
  );
}

// One reminder per member listing everything overdue, at most once a week.
export function queueOverdueReminders(db: Db, today: string): Message[] {
  const byMember = new Map<string, { loan: Loan; tool: Tool }[]>();
  for (const loan of openLoans(db)) {
    if (loan.due >= today) continue;
    const tool = findTool(db, loan.toolId);
    if (!tool) continue;
    const items = byMember.get(loan.memberNo) ?? [];
    items.push({ loan, tool });
    byMember.set(loan.memberNo, items);
  }
  const queued: Message[] = [];
  for (const [memberNo, items] of byMember) {
    const member = findMember(db, memberNo);
    if (!member || remindedRecently(db, memberNo, today)) continue;
    queued.push(queueMessage(db, member, 'overdue', overdueMessage(member, items), today));
  }
  return queued;
}
