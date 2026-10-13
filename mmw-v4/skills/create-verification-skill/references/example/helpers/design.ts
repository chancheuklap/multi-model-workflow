// tests/e2e/notes/helpers/design.ts
const pages = {
	'/notes': {
		unpinned: '/notes/notes-unpinned.html',
		pinned: '/notes/notes-pinned.html',
	},
};

export function designPage<Route extends keyof typeof pages>(
	{ route, state }: { route: Route; state: keyof (typeof pages)[Route] },
) {
	return pages[route][state];
}
