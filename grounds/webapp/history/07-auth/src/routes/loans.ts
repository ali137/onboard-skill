import type { AppRouter } from '../app.ts';
import { json, parseBody, requiredField } from '../http.ts';
import { requireMember, requireStaff } from '../auth.ts';
import { checkout, returnTool } from '../loans.ts';
import { openLoansForMember } from '../store.ts';

export function loanRoutes(router: AppRouter): void {
  router.post('/api/loans', (ctx) => {
    requireStaff(ctx.user);
    const body = parseBody(ctx.req);
    const loan = checkout(
      ctx.db,
      requiredField(body, 'memberNo'),
      requiredField(body, 'tag'),
      ctx.today,
    );
    return json(201, loan);
  });

  router.post('/api/returns', (ctx) => {
    requireStaff(ctx.user);
    const body = parseBody(ctx.req);
    return json(200, returnTool(ctx.db, requiredField(body, 'tag'), ctx.today));
  });

  router.get('/api/members/:no/loans', (ctx) => {
    requireMember(ctx.user, ctx.params.no);
    return json(200, openLoansForMember(ctx.db, ctx.params.no));
  });
}
