import type { AppRouter } from '../app.ts';
import { HttpError, field, html, json, parseBody, redirect } from '../http.ts';
import { requireStaff } from '../auth.ts';
import { addTool, getTool, retireTool, searchTools, updateTool } from '../tools.ts';
import { toolStatus } from '../loans.ts';
import { catalogPage } from '../views/catalog.ts';
import { importInventory } from '../import.ts';

export function toolRoutes(router: AppRouter): void {
  router.get('/', () => redirect('/catalog'));

  router.get('/catalog', (ctx) => {
    const { q, category } = ctx.req.query;
    const tools = searchTools(ctx.db, { q, category: category || undefined });
    const rows = tools.map((tool) => ({ tool, status: toolStatus(ctx.db, tool) }));
    return html(200, catalogPage(rows, { q, category }, ctx.user));
  });

  router.get('/api/tools', (ctx) => {
    const { q, category } = ctx.req.query;
    return json(200, searchTools(ctx.db, { q, category }));
  });

  router.get('/api/tools/:tag', (ctx) => json(200, getTool(ctx.db, ctx.params.tag)));

  router.post('/api/tools', (ctx) => {
    requireStaff(ctx.user);
    const body = parseBody(ctx.req);
    const tool = addTool(
      ctx.db,
      {
        tag: field(body, 'tag') ?? '',
        name: field(body, 'name') ?? '',
        category: field(body, 'category') ?? '',
        condition: field(body, 'condition'),
        notes: field(body, 'notes'),
      },
      ctx.today,
    );
    return json(201, tool);
  });

  router.post('/api/tools/:tag', (ctx) => {
    requireStaff(ctx.user);
    const body = parseBody(ctx.req);
    const tool = updateTool(ctx.db, ctx.params.tag, {
      name: field(body, 'name'),
      category: field(body, 'category'),
      condition: field(body, 'condition'),
      notes: field(body, 'notes'),
    });
    return json(200, tool);
  });

  // Body is the inventory sheet itself, saved as CSV.
  router.post('/api/import/inventory', (ctx) => {
    requireStaff(ctx.user);
    if (!(ctx.req.headers['content-type'] ?? '').startsWith('text/csv')) {
      throw new HttpError(415, 'send the sheet as text/csv');
    }
    return json(200, importInventory(ctx.db, ctx.req.body, ctx.today));
  });

  router.post('/api/tools/:tag/retire', (ctx) => {
    requireStaff(ctx.user);
    return json(200, retireTool(ctx.db, ctx.params.tag));
  });
}
