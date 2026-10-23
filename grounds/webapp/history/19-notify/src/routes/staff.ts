import type { AppRouter } from '../app.ts';
import { json } from '../http.ts';
import { requireStaff } from '../auth.ts';
import { queueOverdueReminders } from '../notify.ts';

export function staffRoutes(router: AppRouter): void {
  router.get('/api/outbox', (ctx) => {
    requireStaff(ctx.user);
    return json(200, ctx.db.outbox);
  });

  router.post('/api/reminders', (ctx) => {
    requireStaff(ctx.user);
    return json(200, queueOverdueReminders(ctx.db, ctx.today));
  });
}
