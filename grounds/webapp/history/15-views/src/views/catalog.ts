import { escapeHtml } from './escape.ts';
import { layout } from './layout.ts';
import type { User } from '../auth.ts';
import type { Tool } from '../store.ts';
import { CATEGORIES } from '../tools.ts';

export interface CatalogRow {
  tool: Tool;
  status: string;
}

function categoryOptions(selected: string | undefined): string {
  const options = [`<option value="">All categories</option>`];
  for (const [code, name] of Object.entries(CATEGORIES)) {
    const attr = code === selected ? ' selected' : '';
    options.push(`<option value="${code}"${attr}>${escapeHtml(name)}</option>`);
  }
  return options.join('');
}

export function catalogPage(
  rows: CatalogRow[],
  query: { q?: string; category?: string },
  user: User | null,
): string {
  const form = `<form method="get" action="/catalog">
<input type="search" name="q" value="${escapeHtml(query.q ?? '')}" placeholder="drill, ladder...">
<select name="category">${categoryOptions(query.category)}</select>
<button>Search</button>
</form>`;
  if (rows.length === 0) return layout('Catalog', `${form}<p>No tools match.</p>`, user);
  const body = rows
    .map(
      ({ tool, status }) => `<tr>
<td>${escapeHtml(tool.tag)}</td>
<td>${escapeHtml(tool.name)}</td>
<td>${escapeHtml(CATEGORIES[tool.category] ?? tool.category)}</td>
<td>${escapeHtml(tool.condition)}</td>
<td>${escapeHtml(status)}</td>
</tr>`,
    )
    .join('\n');
  const table = `<table>
<thead><tr><th>Tag</th><th>Tool</th><th>Category</th><th>Condition</th><th>Status</th></tr></thead>
<tbody>
${body}
</tbody>
</table>`;
  return layout('Catalog', `${form}\n${table}`, user);
}
