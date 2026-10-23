import type { Db, Tool } from '../db.ts';

export function byId(db: Db, id: string): Tool | undefined {
  return db.tools.find((tool) => tool.id === id);
}

export function byTag(db: Db, tag: string): Tool | undefined {
  return db.tools.find((tool) => tool.tag === tag);
}

export function all(db: Db): Tool[] {
  return db.tools;
}

export function insert(db: Db, tool: Omit<Tool, 'id'>): Tool {
  db.counters.tool += 1;
  const stored = { id: String(db.counters.tool), ...tool };
  db.tools.push(stored);
  return stored;
}
