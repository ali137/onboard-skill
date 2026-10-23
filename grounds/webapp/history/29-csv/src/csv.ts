import { HttpError } from './http.ts';

// RFC 4180-style CSV: fields may be quoted, "" is a quote inside a quoted
// field, and lines end in CRLF or LF. A trailing newline does not add a row.
export function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = '';
  let quoted = false;
  let line = 1;
  let quoteLine = 0;
  let i = text.charCodeAt(0) === 0xfeff ? 1 : 0;

  const endField = () => {
    row.push(field);
    field = '';
  };
  const endRow = () => {
    endField();
    rows.push(row);
    row = [];
    line += 1;
  };

  while (i < text.length) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') {
        field += '"';
        i += 2;
        continue;
      }
      if (ch === '"') {
        quoted = false;
      } else {
        if (ch === '\n') line += 1;
        field += ch;
      }
      i += 1;
      continue;
    }
    if (ch === '"' && field === '') {
      quoted = true;
      quoteLine = line;
    } else if (ch === ',') {
      endField();
    } else if (ch === '\r' && text[i + 1] === '\n') {
      endRow();
      i += 1;
    } else if (ch === '\n' || ch === '\r') {
      endRow();
    } else {
      field += ch;
    }
    i += 1;
  }

  if (quoted) throw new HttpError(400, `unclosed quote starting on line ${quoteLine}`);
  if (field !== '' || row.length > 0) endRow();
  return rows;
}
