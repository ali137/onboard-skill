export interface AppRequest {
  method: string;
  path: string;
  query: Record<string, string>;
  headers: Record<string, string>;
  body: string;
}

export interface AppResponse {
  status: number;
  headers: Record<string, string>;
  body: string;
}

export class HttpError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function json(status: number, data: unknown): AppResponse {
  return {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
    body: JSON.stringify(data),
  };
}

export function text(status: number, body: string): AppResponse {
  return { status, headers: { 'content-type': 'text/plain; charset=utf-8' }, body };
}

export function parseQuery(search: string): Record<string, string> {
  const query: Record<string, string> = {};
  for (const [key, value] of new URLSearchParams(search)) query[key] = value;
  return query;
}

// Accepts JSON and plain HTML form posts.
export function parseBody(req: AppRequest): Record<string, unknown> {
  if (req.body.trim() === '') return {};
  const type = (req.headers['content-type'] ?? '').split(';')[0].trim().toLowerCase();
  if (type === 'application/json') {
    let data: unknown;
    try {
      data = JSON.parse(req.body);
    } catch {
      throw new HttpError(400, 'body is not valid JSON');
    }
    if (typeof data !== 'object' || data === null || Array.isArray(data)) {
      throw new HttpError(400, 'body must be a JSON object');
    }
    return data as Record<string, unknown>;
  }
  if (type === 'application/x-www-form-urlencoded') return parseQuery(req.body);
  throw new HttpError(415, `unsupported content type "${type}"`);
}
