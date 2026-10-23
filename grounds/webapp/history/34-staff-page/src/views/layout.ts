import { escapeHtml } from './escape.ts';
import type { User } from '../auth.ts';

const STYLE = `
body { font-family: system-ui, sans-serif; margin: 0; color: #222; }
header { background: #2f4f3a; color: #fff; padding: 0.6rem 1rem; display: flex; gap: 1rem; }
header a { color: #fff; }
main { max-width: 60rem; margin: 0 auto; padding: 1rem; }
table { border-collapse: collapse; width: 100%; }
th, td { text-align: left; padding: 0.3rem 0.5rem; border-bottom: 1px solid #ddd; }
.overdue { color: #a00; font-weight: bold; }
.muted { color: #777; }
`;

function nav(user: User | null): string {
  if (!user) return '<a href="/login">Log in</a>';
  const links = ['<a href="/catalog">Catalog</a>'];
  if (user.role === 'staff') links.push('<a href="/staff/today">Today</a>');
  if (user.memberNo) links.push(`<a href="/members/${escapeHtml(user.memberNo)}">My loans</a>`);
  links.push(`<span class="muted">${escapeHtml(user.username)}</span>`);
  return links.join(' ');
}

export function layout(title: string, body: string, user: User | null = null): string {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escapeHtml(title)} - Tallowmere Tool Library</title>
<style>${STYLE}</style>
</head>
<body>
<header><strong>Tallowmere Tool Library</strong> ${nav(user)}</header>
<main>
<h1>${escapeHtml(title)}</h1>
${body}
</main>
</body>
</html>
`;
}

export function errorPage(status: number, message: string, user: User | null = null): string {
  const title = status === 404 ? 'Not found' : 'Something went wrong';
  const back = user?.role === 'staff' ? '<p><a href="/staff/today">Back to today</a></p>' : '';
  return layout(title, `<p>${escapeHtml(message)}</p>${back}`, user);
}

export function loginPage(error?: string): string {
  const message = error ? `<p class="overdue">${escapeHtml(error)}</p>` : '';
  return layout(
    'Log in',
    `${message}<form method="post" action="/login">
<label>Username <input name="username" autocomplete="username"></label>
<label>Password <input name="password" type="password" autocomplete="current-password"></label>
<button>Log in</button>
</form>`,
  );
}
