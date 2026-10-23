import { createServer } from 'node:http';
import type { IncomingMessage, ServerResponse } from 'node:http';
import { Router } from './router.ts';
import type { Params } from './router.ts';
import { HttpError, json, parseBody, parseQuery, text } from './http.ts';
import type { AppRequest, AppResponse } from './http.ts';
import { loadDb, saveDb } from './store.ts';
import { getMember, registerMember } from './members.ts';
import type { MemberInput } from './members.ts';

type Handler = (req: AppRequest, params: Params) => AppResponse;

const dataFile = process.env.DATA_FILE;
const db = loadDb(dataFile ?? 'data/dev.json');

function today(): string {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

const router = new Router<Handler>()
  .get('/', () => text(200, 'Tallowmere Tool Library\n'))
  .get('/members/:no', (_req, params) => json(200, getMember(db, params.no)))
  .post('/members', (req) => {
    const member = registerMember(db, parseBody(req) as unknown as MemberInput, today());
    return json(201, member);
  });

function handle(req: AppRequest): AppResponse {
  const match = router.match(req.method, req.path);
  if (!match) {
    const allowed = router.allowedMethods(req.path);
    if (allowed.length > 0) return json(405, { error: 'method not allowed' });
    return json(404, { error: 'not found' });
  }
  try {
    return match.handler(req, match.params);
  } catch (err) {
    if (err instanceof HttpError) return json(err.status, { error: err.message });
    throw err;
  }
}

async function readBody(incoming: IncomingMessage): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of incoming) chunks.push(chunk as Buffer);
  return Buffer.concat(chunks).toString('utf8');
}

async function toAppRequest(incoming: IncomingMessage): Promise<AppRequest> {
  const url = new URL(incoming.url ?? '/', 'http://localhost');
  const headers: Record<string, string> = {};
  for (const [key, value] of Object.entries(incoming.headers)) {
    if (typeof value === 'string') headers[key] = value;
  }
  return {
    method: incoming.method ?? 'GET',
    path: url.pathname,
    query: parseQuery(url.search),
    headers,
    body: await readBody(incoming),
  };
}

function send(outgoing: ServerResponse, res: AppResponse): void {
  outgoing.writeHead(res.status, res.headers);
  outgoing.end(res.body);
}

const port = Number(process.env.PORT ?? 8080);

createServer(async (incoming, outgoing) => {
  try {
    const req = await toAppRequest(incoming);
    const res = handle(req);
    // Only write back when pointed at a real data file, never over the sample data.
    if (dataFile && req.method !== 'GET' && res.status < 400) saveDb(dataFile, db);
    send(outgoing, res);
  } catch (err) {
    console.error(err);
    send(outgoing, text(500, 'internal error\n'));
  }
}).listen(port, () => {
  console.log(`listening on http://localhost:${port}`);
});
