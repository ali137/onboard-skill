export type Params = Record<string, string>;

interface Route<H> {
  method: string;
  segments: string[];
  handler: H;
}

export interface Match<H> {
  handler: H;
  params: Params;
}

export class Router<H> {
  #routes: Route<H>[] = [];

  add(method: string, pattern: string, handler: H): this {
    this.#routes.push({ method: method.toUpperCase(), segments: split(pattern), handler });
    return this;
  }

  get(pattern: string, handler: H): this {
    return this.add('GET', pattern, handler);
  }

  post(pattern: string, handler: H): this {
    return this.add('POST', pattern, handler);
  }

  match(method: string, path: string): Match<H> | null {
    const segments = split(path);
    for (const route of this.#routes) {
      if (route.method !== method.toUpperCase()) continue;
      const params = matchSegments(route.segments, segments);
      if (params) return { handler: route.handler, params };
    }
    return null;
  }

  // Methods that would have matched the path, for 405 responses.
  allowedMethods(path: string): string[] {
    const segments = split(path);
    const methods = this.#routes
      .filter((route) => matchSegments(route.segments, segments) !== null)
      .map((route) => route.method);
    return [...new Set(methods)];
  }
}

function split(path: string): string[] {
  return path.split('/').filter((segment) => segment !== '');
}

function matchSegments(pattern: string[], actual: string[]): Params | null {
  if (pattern.length !== actual.length) return null;
  const params: Params = {};
  for (let i = 0; i < pattern.length; i++) {
    const part = pattern[i];
    if (part.startsWith(':')) {
      const value = decode(actual[i]);
      if (value === null) return null;
      params[part.slice(1)] = value;
    } else if (part !== actual[i]) {
      return null;
    }
  }
  return params;
}

function decode(segment: string): string | null {
  try {
    return decodeURIComponent(segment);
  } catch {
    return null;
  }
}
