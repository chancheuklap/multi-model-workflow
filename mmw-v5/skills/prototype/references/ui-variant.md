# UI variant

How one variant of a UI prototype is written, by the session running `UI.md` or by a candidate **arena** sends.

Use the product's existing components and production-style frontend code. Each variant follows the page's purpose, available data, and styling system, with a clear exported component name. Variants differ in layout, information hierarchy, or primary action, rather than just colour or copy.

Use an **API fake** only for interfaces that do not exist yet. Write any API fake your variant needs in your own directory. Existing interfaces use the real local backend. When fake sample data references an existing entity, provide those referenced records through the API fake too, so their IDs agree. Take sample data from the environment tools' product-test seed data rather than inventing it, so tests written from the prototype do not fail on different data in the product. Start from that seed data each launch. Keep fake mutations in `sessionStorage`: refresh retains them, a new tab or restart returns to the seed data.

When the product has accounts, use the real login flow and test accounts against the local account service started by the environment tools, not production or development servers. When new permissions do not exist in the backend yet, demonstrate their different UIs through the prototype's own identity switcher. Give the owner state URLs for states that normal actions cannot reach, such as loading or errors. Tests do not use those URLs.

Give every actionable element a role and an accessible name, so e2e can find it by those names.

A shared `<Header>` is fine; a shared `<Layout>` defeats the point. Each variant should be free to throw out the layout.

As a candidate, put any question whose answer would change the UI in your variant's rationale, not under `## Problems`.

Open your variant on the product page and check it against the Done line below; a candidate uses the URL its brief gives.

Done when your variant runs, exposes every state, and connects each button to a real interface or the API fake.
