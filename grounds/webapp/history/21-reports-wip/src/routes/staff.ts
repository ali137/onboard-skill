import type { AppRouter } from '../app.ts';
import { json } from '../http.ts';
import { requireStaff } from '../auth.ts';
import { queueOverdueReminders } from '../notify.ts';
import { mostBorrowed, overdueLoans } from '../reports.ts';

export function staffRoutes(router: AppRouter): void {
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
    const limit = Number(ctx.req.query.limit ?? 10);
    const rows = mostBorrowed(ctx.db, { from, to, limit }).map((row) => ({
      tag: row.tool.tag,
      tool: row.tool.name,
      loans: row.loans,
    }));
    return json(200, rows);
  });
}
