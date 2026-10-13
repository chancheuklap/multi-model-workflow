// tests/e2e/notes/helpers/design.ts
const pages = {
	'/notes': {
		unpinned: '/design/notes/notes-unpinned.html',
		pinned: '/design/notes/notes-pinned.html',
	},
};

type NotesPage = {
	route: keyof typeof pages;
	state: keyof (typeof pages)['/notes'];
};

export function designPage({ route, state }: NotesPage): string {
	return pages[route][state];
}
