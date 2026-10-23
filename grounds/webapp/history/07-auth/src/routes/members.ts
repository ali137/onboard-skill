import type { AppRouter } from '../app.ts';
import { field, json, parseBody } from '../http.ts';
import { requireMember, requireStaff } from '../auth.ts';
import { findMembers, getMember, registerMember, updateMember } from '../members.ts';

export function memberRoutes(router: AppRouter): void {
  router.get('/api/members', (ctx) => {
    requireStaff(ctx.user);
    return json(200, findMembers(ctx.db, ctx.req.query.q ?? ''));
  });

  router.post('/api/members', (ctx) => {
    requireStaff(ctx.user);
    const body = parseBody(ctx.req);
    const member = registerMember(
      ctx.db,
      {
        name: field(body, 'name') ?? '',
        email: field(body, 'email') ?? '',
        phone: field(body, 'phone') ?? '',
        address: field(body, 'address') ?? '',
        memberNo: field(body, 'memberNo'),
      },
      ctx.today,
    );
    return json(201, member);
  });

  router.get('/api/members/:no', (ctx) => {
    requireMember(ctx.user, ctx.params.no);
    return json(200, getMember(ctx.db, ctx.params.no));
  });

  router.post('/api/members/:no', (ctx) => {
    requireStaff(ctx.user);
    const body = parseBody(ctx.req);
    const member = updateMember(ctx.db, ctx.params.no, {
      name: field(body, 'name'),
      email: field(body, 'email'),
      phone: field(body, 'phone'),
      address: field(body, 'address'),
    });
    return json(200, member);
  });
}
