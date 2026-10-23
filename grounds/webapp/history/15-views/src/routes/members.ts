import type { AppRouter } from '../app.ts';
import { field, html, json, parseBody, requiredField } from '../http.ts';
import { requireMember, requireStaff } from '../auth.ts';
import { findMembers, getMember, registerMember, updateMember } from '../members.ts';
import { balanceCents, feesFor, payFees, waiveFee } from '../fees.ts';
import { findTool, openLoansForMember } from '../store.ts';
import { memberPage } from '../views/member.ts';

export function memberRoutes(router: AppRouter): void {
  router.get('/members/:no', (ctx) => {
    requireMember(ctx.user, ctx.params.no);
    const member = getMember(ctx.db, ctx.params.no);
    const loans = openLoansForMember(ctx.db, member.memberNo).flatMap((loan) => {
      const tool = findTool(ctx.db, loan.toolId);
      return tool ? [{ loan, tool }] : [];
    });
    const balance = balanceCents(ctx.db, member.memberNo);
    return html(200, memberPage({ member, loans, balanceCents: balance }, ctx.today, ctx.user));
  });

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

  router.get('/api/members/:no/fees', (ctx) => {
    requireMember(ctx.user, ctx.params.no);
    const member = getMember(ctx.db, ctx.params.no);
    const fees = feesFor(ctx.db, member.memberNo);
    return json(200, { balanceCents: balanceCents(ctx.db, member.memberNo), fees });
  });

  router.post('/api/members/:no/payments', (ctx) => {
    requireStaff(ctx.user);
    const member = getMember(ctx.db, ctx.params.no);
    const cents = Number(requiredField(parseBody(ctx.req), 'cents'));
    return json(200, payFees(ctx.db, member.memberNo, cents));
  });

  router.post('/api/fees/:id/waive', (ctx) => {
    const staff = requireStaff(ctx.user);
    const reason = field(parseBody(ctx.req), 'reason') ?? '';
    return json(200, waiveFee(ctx.db, ctx.params.id, staff.username, reason, ctx.today));
  });
}
