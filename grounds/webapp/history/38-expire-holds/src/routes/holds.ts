import type { AppRouter } from '../app.ts';
import {
  HttpError,
  field,
  isFormPost,
  json,
  parseBody,
  redirect,
  requiredField,
} from '../http.ts';
import { requireMember, requireStaff, requireUser } from '../auth.ts';
import { cancelHold, expireHolds, getHold, placeHold, queueFor } from '../holds.ts';
import { getTool } from '../tools.ts';
import { holdsForMember } from '../store.ts';

export function holdRoutes(router: AppRouter): void {
  // Members place holds for themselves; staff say who the hold is for.
  router.post('/api/holds', (ctx) => {
    const user = requireUser(ctx.user);
    const body = parseBody(ctx.req);
    const memberNo = user.role === 'staff' ? requiredField(body, 'memberNo') : user.memberNo;
    if (!memberNo) throw new HttpError(403, `account ${user.username} has no member number`);
    const hold = placeHold(ctx.db, memberNo, field(body, 'tag') ?? '', ctx.today);
    return json(201, hold);
  });

  router.post('/api/holds/:id/cancel', (ctx) => {
    requireMember(ctx.user, getHold(ctx.db, ctx.params.id).memberNo);
    return json(200, cancelHold(ctx.db, ctx.params.id, ctx.today));
  });

  router.post('/api/holds/expire', (ctx) => {
    requireStaff(ctx.user);
    const expired = expireHolds(ctx.db, ctx.today);
    return isFormPost(ctx.req) ? redirect('/staff/today') : json(200, expired);
  });

  router.get('/api/members/:no/holds', (ctx) => {
    requireMember(ctx.user, ctx.params.no);
    return json(200, holdsForMember(ctx.db, ctx.params.no));
  });

  router.get('/api/tools/:tag/holds', (ctx) => {
    requireStaff(ctx.user);
    return json(200, queueFor(ctx.db, getTool(ctx.db, ctx.params.tag).id));
  });
}
