import type { AppRouter } from '../app.ts';
import { isFormPost, json, parseBody, redirect, requiredField } from '../http.ts';
import { requireMember, requireStaff } from '../auth.ts';
import { checkout, getLoan, renew, returnTool } from '../loans.ts';
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
    // The counter forms on the staff page post here too.
    return isFormPost(ctx.req) ? redirect('/staff/today') : json(201, loan);
  });

  router.post('/api/returns', (ctx) => {
    requireStaff(ctx.user);
    const body = parseBody(ctx.req);
    const result = returnTool(ctx.db, requiredField(body, 'tag'), ctx.today);
    return isFormPost(ctx.req) ? redirect('/staff/today') : json(200, result);
  });

  router.post('/api/loans/:id/renew', (ctx) => {
    requireMember(ctx.user, getLoan(ctx.db, ctx.params.id).memberNo);
    return json(200, renew(ctx.db, ctx.params.id, ctx.today));
  });

  router.get('/api/members/:no/loans', (ctx) => {
    requireMember(ctx.user, ctx.params.no);
    return json(200, openLoansForMember(ctx.db, ctx.params.no));
  });
}
