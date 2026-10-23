import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  addDays,
  addOpenDays,
  daysBetween,
  dueDateFrom,
  formatDate,
  isOpen,
  isValidDate,
  nextOpenDay,
  toDate,
  toIsoDate,
  weekday,
} from '../src/calendar.ts';

const NO_CLOSURES: string[] = [];

test('adds days across month and year ends', () => {
  assert.equal(addDays('2026-07-30', 3), '2026-08-02');
  assert.equal(addDays('2026-12-30', 5), '2027-01-04');
  assert.equal(addDays('2028-02-28', 1), '2028-02-29');
  assert.equal(addDays('2026-03-01', -1), '2026-02-28');
});

test('adding days is not thrown off by daylight saving changes', () => {
  assert.equal(addDays('2026-03-28', 1), '2026-03-29');
  assert.equal(addDays('2026-03-29', 1), '2026-03-30');
  assert.equal(addDays('2026-10-24', 2), '2026-10-26');
});

test('knows the weekday', () => {
  assert.equal(weekday('2026-07-01'), 3);
  assert.equal(weekday('2026-07-05'), 0);
  assert.equal(weekday('2026-07-11'), 6);
});

test('counts the days between two dates', () => {
  assert.equal(daysBetween('2026-07-01', '2026-07-08'), 7);
  assert.equal(daysBetween('2026-07-08', '2026-07-01'), -7);
  assert.equal(daysBetween('2026-12-31', '2027-01-01'), 1);
});

test('the library is closed on Sundays and Mondays', () => {
  assert.equal(isOpen('2026-07-05', NO_CLOSURES), false);
  assert.equal(isOpen('2026-07-06', NO_CLOSURES), false);
  for (const date of ['2026-07-07', '2026-07-08', '2026-07-09', '2026-07-10', '2026-07-11']) {
    assert.equal(isOpen(date, NO_CLOSURES), true, date);
  }
});

test('the library is closed on closure dates', () => {
  assert.equal(isOpen('2026-07-08', ['2026-07-08']), false);
  assert.equal(isOpen('2026-12-24'), false);
});

test('next open day skips the weekend closing and closures', () => {
  assert.equal(nextOpenDay('2026-07-08', NO_CLOSURES), '2026-07-08');
  assert.equal(nextOpenDay('2026-07-05', NO_CLOSURES), '2026-07-07');
  assert.equal(nextOpenDay('2026-07-05', ['2026-07-07']), '2026-07-08');
  assert.equal(nextOpenDay('2026-08-29'), '2026-09-01');
});

test('adds open days', () => {
  assert.equal(addOpenDays('2026-07-09', 3, NO_CLOSURES), '2026-07-14');
  assert.equal(addOpenDays('2026-07-11', 1, NO_CLOSURES), '2026-07-14');
  assert.equal(addOpenDays('2026-07-09', 0, NO_CLOSURES), '2026-07-09');
});

test('validates dates', () => {
  assert.equal(isValidDate('2026-07-31'), true);
  assert.equal(isValidDate('2026-02-29'), false);
  assert.equal(isValidDate('2026-7-1'), false);
  assert.equal(isValidDate('yesterday'), false);
  assert.throws(() => addDays('2026/07/01', 1), /not a YYYY-MM-DD date/);
});

test('formats date parts with zero padding', () => {
  assert.equal(toIsoDate(2026, 7, 4), '2026-07-04');
});

test('computes due dates as Date objects', () => {
  assert.equal(formatDate(dueDateFrom(toDate('2026-07-07'), 7, NO_CLOSURES)), '2026-07-14');
  assert.equal(formatDate(dueDateFrom(toDate('2026-07-09'), 4, NO_CLOSURES)), '2026-07-14');
  assert.equal(formatDate(dueDateFrom(toDate('2026-08-22'), 7)), '2026-09-01');
});
