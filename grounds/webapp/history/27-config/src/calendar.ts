// Library dates are plain YYYY-MM-DD strings. All the arithmetic goes through
// Date.UTC on the parsed parts so the machine's time zone never matters.

import { config } from './config.ts';

const DATE = /^(\d{4})-(\d{2})-(\d{2})$/;
const DAY_MS = 24 * 60 * 60 * 1000;

function pad(n: number): string {
  return String(n).padStart(2, '0');
}

export function toIsoDate(year: number, month: number, day: number): string {
  return `${year}-${pad(month)}-${pad(day)}`;
}

function toDayNumber(date: string): number {
  const match = DATE.exec(date);
  if (!match) throw new Error(`not a YYYY-MM-DD date: "${date}"`);
  return Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])) / DAY_MS;
}

function fromDayNumber(day: number): string {
  const d = new Date(day * DAY_MS);
  return toIsoDate(d.getUTCFullYear(), d.getUTCMonth() + 1, d.getUTCDate());
}

export function isValidDate(date: string): boolean {
  if (!DATE.test(date)) return false;
  return fromDayNumber(toDayNumber(date)) === date;
}

export function addDays(date: string, days: number): string {
  return fromDayNumber(toDayNumber(date) + days);
}

// 0 = Sunday ... 6 = Saturday
export function weekday(date: string): number {
  return new Date(toDayNumber(date) * DAY_MS).getUTCDay();
}

export function daysBetween(from: string, to: string): number {
  return toDayNumber(to) - toDayNumber(from);
}

export function isOpen(date: string, closures: string[] = config.closures): boolean {
  return !config.closedWeekdays.includes(weekday(date)) && !closures.includes(date);
}

// The date itself if the library is open that day, otherwise the next open day.
export function nextOpenDay(date: string, closures: string[] = config.closures): string {
  let day = date;
  while (!isOpen(day, closures)) day = addDays(day, 1);
  return day;
}

// The nth open day after date (not counting date itself).
export function addOpenDays(date: string, n: number, closures = config.closures): string {
  let day = date;
  for (let i = 0; i < n; i++) day = nextOpenDay(addDays(day, 1), closures);
  return day;
}
