import { HttpError } from './http.ts';
import { allTools, findToolByTag, insertTool, openLoanForTool } from './store.ts';
import type { Db, Tool } from './store.ts';

export const CATEGORIES: Record<string, string> = {
  PT: 'Power tools',
  LD: 'Ladders',
  GD: 'Garden',
  SW: 'Sewing',
  HT: 'Hand tools',
};

export interface ToolInput {
  tag: string;
  name: string;
  category: string;
  condition?: string;
  notes?: string;
}

const ASSET_TAG = /^[A-Z]{2}-\d{4}$/;

export function checkTag(tag: string): string {
  if (!ASSET_TAG.test(tag)) throw new HttpError(400, `asset tag "${tag}" must look like AB-1234`);
  return tag;
}

// Accepts the code ("PT") or the name ("Power tools"), any case.
export function categoryCode(value: string): string {
  const wanted = value.trim().toLowerCase();
  for (const [code, name] of Object.entries(CATEGORIES)) {
    if (code.toLowerCase() === wanted || name.toLowerCase() === wanted) return code;
  }
  throw new HttpError(400, `unknown category "${value.trim()}"`);
}

export function addTool(db: Db, input: ToolInput, today: string): Tool {
  const tag = checkTag(input.tag);
  const category = categoryCode(input.category ?? '');
  const name = (input.name ?? '').trim();
  if (name === '') throw new HttpError(400, 'name is required');
  if (tag.slice(0, 2) !== category) {
    throw new HttpError(400, `asset tag ${tag} does not match category ${category}`);
  }
  if (findToolByTag(db, tag)) throw new HttpError(409, `asset tag ${tag} is already in use`);
  return insertTool(db, {
    tag,
    name,
    category,
    condition: (input.condition ?? '').trim(),
    notes: (input.notes ?? '').trim(),
    retired: false,
    addedOn: today,
  });
}

export function getTool(db: Db, tag: string): Tool {
  const tool = findToolByTag(db, tag);
  if (!tool) throw new HttpError(404, `no tool with asset tag ${tag}`);
  return tool;
}

export function updateTool(db: Db, tag: string, changes: Partial<ToolInput>): Tool {
  const tool = getTool(db, tag);
  if (changes.name !== undefined) {
    if (changes.name.trim() === '') throw new HttpError(400, 'name is required');
    tool.name = changes.name.trim();
  }
  if (changes.category !== undefined && categoryCode(changes.category) !== tool.category) {
    throw new HttpError(400, `${tag} cannot change category; retag it instead`);
  }
  if (changes.condition !== undefined) tool.condition = changes.condition.trim();
  if (changes.notes !== undefined) tool.notes = changes.notes.trim();
  return tool;
}

export function retireTool(db: Db, tag: string): Tool {
  const tool = getTool(db, tag);
  tool.retired = true;
  return tool;
}

export interface ToolSearch {
  q?: string;
  category?: string;
  includeRetired?: boolean;
}

export function searchTools(db: Db, search: ToolSearch = {}): Tool[] {
  const words = (search.q ?? '').toLowerCase().split(/\s+/).filter(Boolean);
  const category = search.category ? categoryCode(search.category) : undefined;
  return allTools(db)
    .filter((tool) => search.includeRetired || !tool.retired)
    .filter((tool) => !category || tool.category === category)
    .filter((tool) => {
      const haystack = `${tool.tag} ${tool.name} ${tool.notes}`.toLowerCase();
      return words.every((word) => haystack.includes(word));
    })
    .sort((a, b) => a.tag.localeCompare(b.tag));
}

export function toolStatus(db: Db, tool: Tool): string {
  if (tool.retired) return 'retired';
  const loan = openLoanForTool(db, tool.id);
  if (loan) return `on loan, due ${loan.due}`;
  return 'available';
}
