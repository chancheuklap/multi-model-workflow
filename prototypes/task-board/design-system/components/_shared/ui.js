// The id a part of a component carries: `<data-ui>.<part>` when the page gave the
// component an id, nothing when it did not.
export const part = (ui, name) => (ui ? `${ui}.${name}` : undefined);
