import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseCsv } from '../src/csv.ts';

test('splits rows and fields', () => {
  assert.deepEqual(parseCsv('a,b,c\n1,2,3'), [
    ['a', 'b', 'c'],
    ['1', '2', '3'],
  ]);
});

test('a trailing newline does not add an empty row', () => {
  assert.deepEqual(parseCsv('a,b\n1,2\n'), [
    ['a', 'b'],
    ['1', '2'],
  ]);
});

test('handles CRLF line endings', () => {
  assert.deepEqual(parseCsv('a,b\r\n1,2\r\n'), [
    ['a', 'b'],
    ['1', '2'],
  ]);
});

test('keeps commas inside quoted fields', () => {
  assert.deepEqual(parseCsv('"Ladder, step",LD\n'), [['Ladder, step', 'LD']]);
});

test('two quotes inside a quoted field are one quote', () => {
  assert.deepEqual(parseCsv('"10"" tile saw",ok\n'), [['10" tile saw', 'ok']]);
  assert.deepEqual(parseCsv('""\n'), [['']]);
});

test('keeps line breaks inside quoted fields', () => {
  const rows = parseCsv('"blade worn\r\nreplace soon",x');
  assert.deepEqual(rows, [['blade worn\r\nreplace soon', 'x']]);
});

test('keeps empty fields', () => {
  assert.deepEqual(parseCsv(',a,,\n'), [['', 'a', '', '']]);
});

test('a blank line is a row with one empty field', () => {
  assert.deepEqual(parseCsv('a\n\nb\n'), [['a'], [''], ['b']]);
});

test('ignores a byte order mark', () => {
  assert.deepEqual(parseCsv('﻿Tag,Name\n'), [['Tag', 'Name']]);
});

test('empty input has no rows', () => {
  assert.deepEqual(parseCsv(''), []);
});

test('reports an unclosed quote with its line', () => {
  assert.throws(() => parseCsv('a,b\n"open,c\nd\n'), /unclosed quote starting on line 2/);
});
