import { HttpError, html, json, parseBody, redirect, requiredField } from './http.ts';
import type { AppRequest, AppResponse } from './http.ts';
import { Router } from './router.ts';
import type { Params } from './router.ts';
import { login, logout, tokenFromRequest, userForToken } from './auth.ts';
import type { User } from './auth.ts';
import type { Db } from './db.ts';
import { memberRoutes } from './routes/members.ts';
import { toolRoutes } from './routes/tools.ts';
import { loanRoutes } from './routes/loans.ts';
import { holdRoutes } from './routes/holds.ts';
import { staffRoutes } from './routes/staff.ts';
import { errorPage, loginPage } from './views/layout.ts';

export interface Deps {
  today: string;
  newToken?: () => string;
}

export interface Ctx {
  req: AppRequest;
  params: Params;
  db: Db;
  deps: Deps;
  today: string;
  user: User | null;
}

export type Handler = (ctx: Ctx) => AppResponse;
export type AppRouter = Router<Handler>;

const router: AppRouter = new Router<Handler>();

function isForm(req: AppRequest): boolean {
  return (req.headers['content-type'] ?? '').startsWith('application/x-www-form-urlencoded');
}

router.get('/login', () => html(200, loginPage()));

router.post('/login', (ctx) => {
  const body = parseBody(ctx.req);
  const username = requiredField(body, 'username');
  const password = requiredField(body, 'password');
  const session = login(ctx.db, username, password, ctx.today, ctx.deps.newToken);
  if (!session) {
    if (isForm(ctx.req)) return html(401, loginPage('Wrong username or password.'));
    throw new HttpError(401, 'wrong username or password');
  }
  const res = isForm(ctx.req) ? redirect('/catalog') : json(200, { token: session.token });
  res.headers['set-cookie'] = `session=${session.token}; HttpOnly; SameSite=Lax; Path=/`;
  return res;
});

router.post('/logout', (ctx) => {
  const token = tokenFromRequest(ctx.req);
  if (token) logout(ctx.db, token);
  const res = json(200, { ok: true });
  res.headers['set-cookie'] = 'session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0';
  return res;
});

router.get('/api/me', (ctx) => {
  if (!ctx.user) throw new HttpError(401, 'please log in');
  return json(200, ctx.user);
});

memberRoutes(router);
toolRoutes(router);
loanRoutes(router);
holdRoutes(router);
staffRoutes(router);

// API callers get JSON errors, browsers get a page.
function errorResponse(req: AppRequest, err: HttpError, user: User | null): AppResponse {
  if (req.path.startsWith('/api/') || req.method !== 'GET') {
    return json(err.status, { error: err.message });
  }
  return html(err.status, errorPage(err.status, err.message, user));
}

export function handle(req: AppRequest, db: Db, deps: Deps): AppResponse {
  const match = router.match(req.method, req.path);
  if (!match) {
    const allowed = router.allowedMethods(req.path);
    if (allowed.length === 0) return errorResponse(req, new HttpError(404, 'not found'), null);
    const res = json(405, { error: 'method not allowed' });
    res.headers['allow'] = allowed.join(', ');
    return res;
  }
  const token = tokenFromRequest(req);
  const user = token ? userForToken(db, token, deps.today) : null;
  try {
    return match.handler({ req, params: match.params, db, deps, today: deps.today, user });
  } catch (err) {
    if (err instanceof HttpError) return errorResponse(req, err, user);
    throw err;
  }
}
