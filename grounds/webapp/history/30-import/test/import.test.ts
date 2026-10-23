import { test } from 'node:test';
import assert from 'node:assert/strict';
import { importInventory } from '../src/import.ts';
import { emptyDb } from '../src/db.ts';
import { getTool, searchTools } from '../src/tools.ts';

const TODAY = '2026-09-05';

const SHEET = [
  'Tag,Name,Category,Condition,Notes',
  'PT-0042,Orbital sander,PT,worn pad,sanding sheets sold separately',
  'LD-0007,Roof ladder,LD,fair,hook end repainted 2025',
  'GD-0012,Wheelbarrow,GD,tire patched,',
  'SW-0003,Overlocker,SW,good,threaded for black',
  '',
].join('\n');

test('adds the tools from a new sheet', () => {
  const db = emptyDb();
  const result = importInventory(db, SHEET, TODAY);
  assert.deepEqual(result, { added: 4, updated: 0, rejected: [] });
  assert.equal(getTool(db, 'LD-0007').name, 'Roof ladder');
  assert.equal(getTool(db, 'GD-0012').condition, 'tire patched');
});

test('updates tools that are already in the catalog', () => {
  const db = emptyDb();
  importInventory(db, SHEET, TODAY);
  const again = SHEET.replace('worn pad', 'new pad fitted');
  assert.deepEqual(importInventory(db, again, TODAY), { added: 0, updated: 4, rejected: [] });
  assert.equal(getTool(db, 'PT-0042').condition, 'new pad fitted');
  assert.equal(searchTools(db).length, 4);
});

test('a row with a missing name is rejected with its row number', () => {
  const db = emptyDb();
  const sheet = SHEET + 'HT-0010,,HT,good,\n';
  const result = importInventory(db, sheet, TODAY);
  assert.equal(result.added, 4);
  assert.deepEqual(result.rejected, [{ row: 6, reason: 'name is required' }]);
});

test('a row with an unknown category is rejected', () => {
  const db = emptyDb();
  const sheet = 'Tag,Name,Category,Condition,Notes\nKT-0001,Stand mixer,Kitchen,good,\n';
  assert.deepEqual(importInventory(db, sheet, TODAY).rejected, [
    { row: 2, reason: 'unknown category "Kitchen"' },
  ]);
});

test('empty lines are skipped', () => {
  const db = emptyDb();
  const sheet = 'Tag,Name,Category,Condition,Notes\n\nHT-0014,Tile cutter,HT,good,\n,,,,\n';
  assert.deepEqual(importInventory(db, sheet, TODAY), { added: 1, updated: 0, rejected: [] });
});

test('quoted names may contain commas', () => {
  const db = emptyDb();
  const sheet = 'Tag,Name,Category,Condition,Notes\nLD-0001,"Step ladder, 6 tread",LD,good,""\n';
  importInventory(db, sheet, TODAY);
  assert.equal(getTool(db, 'LD-0001').name, 'Step ladder, 6 tread');
});

test('a sheet without the expected columns is refused', () => {
  const sheet = 'Tag,Name\nPT-0001,Drill\n';
  assert.throws(() => importInventory(emptyDb(), sheet, TODAY), /no "Category" column/);
  assert.throws(() => importInventory(emptyDb(), '', TODAY), /the sheet is empty/);
});
