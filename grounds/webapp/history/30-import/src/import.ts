import { HttpError } from './http.ts';
import { parseCsv } from './csv.ts';
import { addTool, updateTool } from './tools.ts';
import { findToolByTag } from './store.ts';
import type { Db } from './db.ts';

// The board's inventory sheet, exported from their spreadsheet.
const COLUMNS = ['Tag', 'Name', 'Category', 'Condition', 'Notes'] as const;

type Column = (typeof COLUMNS)[number];

export interface ImportResult {
  added: number;
  updated: number;
  rejected: { row: number; reason: string }[];
}

function columnIndex(header: string[]): Record<Column, number> {
  const index = {} as Record<Column, number>;
  for (const name of COLUMNS) {
    const at = header.indexOf(name);
    if (at === -1) throw new HttpError(400, `the sheet has no "${name}" column`);
    index[name] = at;
  }
  return index;
}

// Each row updates the tool with that tag, or adds it if the tag is new.
// Rows are numbered as in the spreadsheet, so the first data row is row 2.
export function importInventory(db: Db, csv: string, today: string): ImportResult {
  const [header, ...rows] = parseCsv(csv);
  if (!header) throw new HttpError(400, 'the sheet is empty');
  const index = columnIndex(header);
  const result: ImportResult = { added: 0, updated: 0, rejected: [] };

  rows.forEach((cells, i) => {
    if (cells.every((cell) => cell.trim() === '')) return;
    const cell = (name: Column) => (cells[index[name]] ?? '').trim();
    const tag = cell('Tag');
    const fields = {
      name: cell('Name'),
      category: cell('Category'),
      condition: cell('Condition'),
      notes: cell('Notes'),
    };
    try {
      if (findToolByTag(db, tag)) {
        updateTool(db, tag, fields);
        result.updated += 1;
      } else {
        addTool(db, { tag, ...fields }, today);
        result.added += 1;
      }
    } catch (err) {
      if (!(err instanceof HttpError)) throw err;
      result.rejected.push({ row: i + 2, reason: err.message });
    }
  });
  return result;
}
