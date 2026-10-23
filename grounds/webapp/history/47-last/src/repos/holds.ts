import type { Db, Hold } from '../db.ts';

export function byId(db: Db, id: string): Hold | undefined {
  return db.holds.find((hold) => hold.id === id);
}

export function forMember(db: Db, memberNo: string): Hold[] {
  return db.holds.filter((hold) => hold.memberNo === memberNo);
}

// Waiting holds, in no particular order.
export function openForTool(db: Db, toolId: string): Hold[] {
  return db.holds.filter((hold) => hold.toolId === toolId && hold.status === 'waiting');
}

export function readyForTool(db: Db, toolId: string): Hold | undefined {
  return db.holds.find((hold) => hold.toolId === toolId && hold.status === 'ready');
}

export function allReady(db: Db): Hold[] {
  return db.holds.filter((hold) => hold.status === 'ready');
}

export function insert(db: Db, hold: Omit<Hold, 'id'>): Hold {
  db.counters.hold += 1;
  const stored = { id: String(db.counters.hold), ...hold };
  db.holds.push(stored);
  return stored;
}
