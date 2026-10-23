import type { AppRouter } from '../app.ts';
import { field, json, parseBody } from '../http.ts';
import { requireStaff } from '../auth.ts';
import { addTool, getTool, retireTool, searchTools, updateTool } from '../tools.ts';

export function toolRoutes(router: AppRouter): void {
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

  router.post('/api/tools/:tag/retire', (ctx) => {
    requireStaff(ctx.user);
    return json(200, retireTool(ctx.db, ctx.params.tag));
  });
}
