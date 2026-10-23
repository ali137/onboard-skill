import { test } from 'node:test';
import assert from 'node:assert/strict';
import { importInventory } from '../src/import.ts';
import { emptyDb } from '../src/db.ts';
import { getTool, searchTools } from '../src/tools.ts';

const TODAY = '2026-09-05';

// Hand-typed tags mixed in with the printed ones, as the board's sheet arrives.
const SHEET = [
  'Tag,Name,Category,Condition,Notes',
  'PT-0042,Orbital sander,PT,worn pad,sanding sheets sold separately',
  'pt 0043,Belt sander,PT,good,',
  'LD0007,Roof ladder,LD,fair,hook end repainted 2025',
  'GD-0002,Lawn aerator,GD,good,',
  'SW-0001,Sewing machine,SW,good,manual in the lid',
  'gd-0012,Wheelbarrow,GD,tire patched,',
  'HT-0010,Socket set,HT,two sockets missing,8 mm and 13 mm gone',
  'PT-0001,"Cordless drill, 18V",PT,good,two batteries',
  ' sw 0003 ,Overlocker,SW,good,threaded for black',
  'HT-0014,Tile cutter,HT,good,',
  'pt-0011,Pressure washer,PT,good,needs an outdoor socket',
  'LD-0001,"Step ladder, 6 tread",LD,good,',
  '',
].join('\n');

const TAGS = [
  'GD-0002',
  'GD-0012',
  'HT-0010',
  'HT-0014',
  'LD-0001',
  'LD-0007',
  'PT-0001',
  'PT-0011',
  'PT-0042',
  'PT-0043',
  'SW-0001',
  'SW-0003',
];

test('imports every row of a new inventory sheet', () => {
  const db = emptyDb();
  const result = importInventory(db, SHEET, TODAY);
  assert.deepEqual(result, { added: 12, updated: 0, rejected: [] });
  assert.deepEqual(searchTools(db).map((tool) => tool.tag), TAGS);
  assert.equal(getTool(db, 'LD-0007').name, 'Roof ladder');
  assert.equal(getTool(db, 'SW-0003').notes, 'threaded for black');
});

test('a re-import updates every tool and adds none', () => {
  const db = emptyDb();
  importInventory(db, SHEET, TODAY);
  const again = SHEET.replace('worn pad', 'new pad fitted').replace('tire patched', 'new tire');
  assert.deepEqual(importInventory(db, again, TODAY), { added: 0, updated: 12, rejected: [] });
  assert.equal(searchTools(db).length, 12);
  assert.equal(getTool(db, 'PT-0042').condition, 'new pad fitted');
  assert.equal(getTool(db, 'GD-0012').condition, 'new tire');
});

test('a tag that cannot be read is rejected, not guessed', () => {
  const db = emptyDb();
  const sheet = [
    'Tag,Name,Category,Condition,Notes',
    'PT-42,Jigsaw,PT,good,',
    'P-0004,Jigsaw,PT,good,',
  ].join('\n');
  assert.deepEqual(importInventory(db, sheet, TODAY).rejected, [
    { row: 2, reason: 'asset tag "PT-42" must look like AB-1234' },
    { row: 3, reason: 'asset tag "P-0004" must look like AB-1234' },
  ]);
});

test('header case, spacing and column order do not matter', () => {
  const db = emptyDb();
  const sheet = 'TAG, name ,Notes,CATEGORY,condition\nHT-0014,Tile cutter,spare wheel,HT,good\n';
  assert.deepEqual(importInventory(db, sheet, TODAY), { added: 1, updated: 0, rejected: [] });
  const tool = getTool(db, 'HT-0014');
  assert.equal(tool.notes, 'spare wheel');
  assert.equal(tool.condition, 'good');
});

test('a row with a missing name is rejected with its row number', () => {
  const db = emptyDb();
  const sheet = SHEET + 'HT-0012,,HT,good,\n';
  const result = importInventory(db, sheet, TODAY);
  assert.equal(result.added, 12);
  assert.deepEqual(result.rejected, [{ row: 14, reason: 'name is required' }]);
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
