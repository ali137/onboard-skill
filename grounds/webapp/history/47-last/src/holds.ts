import { HttpError } from './http.ts';
import { addOpenDays } from './calendar.ts';
import { config } from './config.ts';
import { getMember, isSuspended } from './members.ts';
import { getTool } from './tools.ts';
import { notifyHoldReady } from './notify.ts';
import { currentLoan } from './loans.ts';
import * as holdsRepo from './repos/holds.ts';
import type { Db, Hold } from './db.ts';

function byRequestTime(a: Hold, b: Hold): number {
  if (a.requestedOn !== b.requestedOn) return a.requestedOn < b.requestedOn ? -1 : 1;
  return Number(a.id) - Number(b.id);
}

export function queueFor(db: Db, toolId: string): Hold[] {
  const open = holdsRepo.openForTool(db, toolId).sort(byRequestTime);
  const firstPerMember = new Map<string, Hold>();
  for (const hold of open) {
    if (!firstPerMember.has(hold.memberNo)) firstPerMember.set(hold.memberNo, hold);
  }
  return [...firstPerMember.values()];
}

// 1 for the front of the line, 0 if the member is not waiting.
export function placeInLine(db: Db, toolId: string, memberNo: string): number {
  return queueFor(db, toolId).findIndex((hold) => hold.memberNo === memberNo) + 1;
}

export function getHold(db: Db, holdId: string): Hold {
  const hold = holdsRepo.byId(db, holdId);
  if (!hold) throw new HttpError(404, `no hold ${holdId}`);
  return hold;
}

export function placeHold(db: Db, memberNo: string, tag: string, today: string): Hold {
  const member = getMember(db, memberNo);
  if (isSuspended(member)) throw new HttpError(409, `member ${memberNo} is suspended`);
  const tool = getTool(db, tag);
  if (tool.retired) throw new HttpError(409, `${tag} has been retired`);
  const loan = currentLoan(db, tool.id);
  if (!loan) throw new HttpError(409, `${tag} is on the shelf; no need to wait for it`);
  if (loan.memberNo === member.memberNo) {
    throw new HttpError(409, `member ${memberNo} has ${tag} already`);
  }
  return holdsRepo.insert(db, {
    toolId: tool.id,
    memberNo: member.memberNo,
    requestedOn: today,
    status: 'waiting',
    readyOn: null,
    pickupBy: null,
  });
}

// The next member in line gets the tool put aside for them.
export function promoteNextHold(db: Db, toolId: string, today: string): Hold | null {
  const next = queueFor(db, toolId)[0];
  if (!next) return null;
  next.status = 'ready';
  next.readyOn = today;
  next.pickupBy = addOpenDays(today, config.holdPickupDays);
  notifyHoldReady(db, next, today);
  return next;
}

// Holds nobody collected by the pickup date lapse, and the tool goes to the
// next member in line. Run once a day.
export function expireHolds(db: Db, today: string): Hold[] {
  const expired: Hold[] = [];
  for (const hold of holdsRepo.allReady(db)) {
    if (hold.pickupBy === null || hold.pickupBy >= today) continue;
    hold.status = 'expired';
    expired.push(hold);
    promoteNextHold(db, hold.toolId, today);
  }
  return expired;
}

// Called on checkout: the member's holds on this tool are done with.
export function collectHolds(db: Db, toolId: string, memberNo: string): void {
  for (const hold of holdsRepo.forMember(db, memberNo)) {
    if (hold.toolId !== toolId) continue;
    if (hold.status === 'waiting' || hold.status === 'ready') hold.status = 'collected';
  }
}

export function cancelHold(db: Db, holdId: string, today: string): Hold {
  const hold = getHold(db, holdId);
  if (hold.status !== 'waiting' && hold.status !== 'ready') {
    throw new HttpError(409, `hold ${holdId} is ${hold.status}, it cannot be canceled`);
  }
  const wasReady = hold.status === 'ready';
  hold.status = 'canceled';
  if (wasReady) promoteNextHold(db, hold.toolId, today);
  return hold;
}
