import { test } from 'node:test';
import assert from 'node:assert/strict';
import { emptyDb } from '../src/store.ts';
import type { Db } from '../src/store.ts';
import {
  addTool,
  categoryCode,
  checkTag,
  getTool,
  retireTool,
  searchTools,
  updateTool,
} from '../src/tools.ts';

const TODAY = '2026-06-30';

function catalog(): Db {
  const db = emptyDb();
  addTool(db, { tag: 'PT-0001', name: 'Cordless drill', category: 'PT' }, TODAY);
  addTool(db, { tag: 'PT-0011', name: 'Pressure washer', category: 'PT' }, TODAY);
  addTool(db, { tag: 'LD-0003', name: 'Extension ladder', category: 'LD' }, TODAY);
  const notes = 'manual in the lid';
  addTool(db, { tag: 'SW-0001', name: 'Sewing machine', category: 'SW', notes }, TODAY);
  return db;
}

test('accepts asset tags in the AB-1234 form', () => {
  assert.equal(checkTag('PT-0042'), 'PT-0042');
  assert.equal(checkTag('HT-9999'), 'HT-9999');
});

test('rejects anything that is not exactly AB-1234', () => {
  for (const tag of ['pt-0042', 'PT0042', 'PT 0042', 'PT-42', 'PTX-0042', ' PT-0042']) {
    assert.throws(() => checkTag(tag), new RegExp(`asset tag "${tag}" must look like AB-1234`));
  }
});

test('knows categories by code or by name', () => {
  assert.equal(categoryCode('pt'), 'PT');
  assert.equal(categoryCode('Ladders'), 'LD');
  assert.equal(categoryCode(' hand tools '), 'HT');
  assert.throws(() => categoryCode('Kitchen'), /unknown category "Kitchen"/);
});

test('adds a tool and gives it an id', () => {
  const db = emptyDb();
  const tool = addTool(db, { tag: 'GD-0005', name: 'Hedge trimmer', category: 'garden' }, TODAY);
  assert.equal(tool.id, '1');
  assert.equal(tool.category, 'GD');
  assert.equal(tool.retired, false);
  assert.equal(getTool(db, 'GD-0005'), tool);
});

test('the tag letters must match the category', () => {
  assert.throws(
    () => addTool(emptyDb(), { tag: 'PT-0005', name: 'Hedge trimmer', category: 'GD' }, TODAY),
    /does not match category GD/,
  );
});

test('two tools cannot share a tag', () => {
  const db = catalog();
  assert.throws(
    () => addTool(db, { tag: 'PT-0001', name: 'Another drill', category: 'PT' }, TODAY),
    /PT-0001 is already in use/,
  );
});

test('updates condition and notes', () => {
  const db = catalog();
  updateTool(db, 'PT-0011', { condition: 'hose cracked', notes: 'needs an outdoor socket' });
  const tool = getTool(db, 'PT-0011');
  assert.equal(tool.condition, 'hose cracked');
  assert.equal(tool.notes, 'needs an outdoor socket');
});

test('a tool cannot move to another category', () => {
  assert.throws(() => updateTool(catalog(), 'LD-0003', { category: 'GD' }), /retag it instead/);
});

test('searches by words in the name, tag or notes', () => {
  const db = catalog();
  assert.deepEqual(searchTools(db, { q: 'drill' }).map((t) => t.tag), ['PT-0001']);
  assert.deepEqual(searchTools(db, { q: 'MANUAL lid' }).map((t) => t.tag), ['SW-0001']);
  assert.deepEqual(searchTools(db, { q: 'ld-0003' }).map((t) => t.tag), ['LD-0003']);
});

test('filters by category and sorts by tag', () => {
  const db = catalog();
  assert.deepEqual(searchTools(db, { category: 'Power tools' }).map((t) => t.tag), [
    'PT-0001',
    'PT-0011',
  ]);
  assert.equal(searchTools(db).length, 4);
});

test('retired tools drop out of the search', () => {
  const db = catalog();
  retireTool(db, 'PT-0011');
  assert.deepEqual(searchTools(db, { q: 'washer' }), []);
  assert.equal(searchTools(db, { q: 'washer', includeRetired: true }).length, 1);
});
