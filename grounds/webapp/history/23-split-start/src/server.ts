import { createServer } from 'node:http';
import type { IncomingMessage, ServerResponse } from 'node:http';
import { parseQuery, text } from './http.ts';
import type { AppRequest, AppResponse } from './http.ts';
import { handle } from './app.ts';
import { loadDb, saveDb } from './db.ts';
import { toIsoDate } from './calendar.ts';

const dataFile = process.env.DATA_FILE;
const db = loadDb(dataFile ?? 'data/dev.json');
const port = Number(process.env.PORT ?? 8080);

// The only place that reads the clock. The counter PC is set to library time.
function today(): string {
  const now = new Date();
  return toIsoDate(now.getFullYear(), now.getMonth() + 1, now.getDate());
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

createServer(async (incoming, outgoing) => {
  try {
    const req = await toAppRequest(incoming);
    const res = handle(req, db, { today: today() });
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
