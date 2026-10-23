import type { AppRouter } from '../app.ts';
import { html, json } from '../http.ts';
import { formatCents } from '../fees.ts';
import { requireStaff } from '../auth.ts';
import { queueOverdueReminders } from '../notify.ts';
import { feesOutstanding, mostBorrowed, overdueLoans } from '../reports.ts';
import { queueFor } from '../holds.ts';
import { findMembers } from '../members.ts';
import * as membersRepo from '../repos/members.ts';
import { allTools, findTool, openLoans } from '../store.ts';
import type { Db } from '../db.ts';
import { staffPage } from '../views/staff.ts';
import type { StaffPageData } from '../views/staff.ts';

function todayData(db: Db, today: string, q: string | undefined): StaffPageData {
  const dueToday = openLoans(db)
    .filter((loan) => loan.due === today)
    .flatMap((loan) => {
      const tool = findTool(db, loan.toolId);
      const member = membersRepo.byNumber(db, loan.memberNo);
      return tool && member ? [{ loan, tool, member }] : [];
    });
  const holdsReady = db.holds
    .filter((hold) => hold.status === 'ready')
    .sort((a, b) => (a.pickupBy ?? '').localeCompare(b.pickupBy ?? ''))
    .flatMap((hold) => {
      const tool = findTool(db, hold.toolId);
      const member = membersRepo.byNumber(db, hold.memberNo);
      return tool && member ? [{ hold, tool, member }] : [];
    });
  const waiting = allTools(db)
    .map((tool) => ({ tool, count: queueFor(db, tool.id).length }))
    .filter((row) => row.count > 0);
  const search = q ? { q, members: findMembers(db, q) } : null;
  return { dueToday, overdue: overdueLoans(db, today), holdsReady, waiting, search };
}

export function staffRoutes(router: AppRouter): void {
  router.get('/staff/today', (ctx) => {
    requireStaff(ctx.user);
    const data = todayData(ctx.db, ctx.today, ctx.req.query.q);
    return html(200, staffPage(data, ctx.today, ctx.user));
  });

  router.get('/api/outbox', (ctx) => {
    requireStaff(ctx.user);
    return json(200, ctx.db.outbox);
  });

  router.post('/api/reminders', (ctx) => {
    requireStaff(ctx.user);
    return json(200, queueOverdueReminders(ctx.db, ctx.today));
  });

  router.get('/api/reports/overdue', (ctx) => {
    requireStaff(ctx.user);
    const rows = overdueLoans(ctx.db, ctx.today).map((row) => ({
      tag: row.tool.tag,
      tool: row.tool.name,
      memberNo: row.member.memberNo,
      member: row.member.name,
      phone: row.member.phone,
      due: row.loan.due,
      daysOverdue: row.daysOverdue,
    }));
    return json(200, rows);
  });

  router.get('/api/reports/popular', (ctx) => {
    requireStaff(ctx.user);
    const { from, to } = ctx.req.query;
    const asked = Number(ctx.req.query.limit);
    const limit = Number.isInteger(asked) && asked > 0 ? asked : 10;
    const rows = mostBorrowed(ctx.db, { from, to, limit }).map((row) => ({
      tag: row.tool.tag,
      tool: row.tool.name,
      loans: row.loans,
    }));
    return json(200, rows);
  });

  router.get('/api/reports/fees', (ctx) => {
    requireStaff(ctx.user);
    const rows = feesOutstanding(ctx.db).map((row) => ({
      memberNo: row.member.memberNo,
      member: row.member.name,
      owedCents: row.owedCents,
      owed: formatCents(row.owedCents),
    }));
    return json(200, rows);
  });
}
