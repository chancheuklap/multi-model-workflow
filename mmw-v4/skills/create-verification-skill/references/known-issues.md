# Known verification issues

Each entry records the product type it applies to, the symptom, the cause,
where it belongs in `verify-<product>` or the product environment tool, and what
to write there. An entry contains only the details recorded for that issue.

### Password entry prevents screenshots

- Applies to products with sign-in that requires a password in the browser.
- Symptom: e2e prohibits all screenshots after a password is entered, leaving the Spec reviewer without screenshot pairs.
- Guidance: complete sign-in outside the test browser. The test only injects the saved login state.

### Development servers reload on first visit

- Applies to frontends with a development server.
- Cause: the development server reloads the page on first visit, and build output differs from development output.
- Guidance: use a production build and preview server for both targets.

### New permissions are missing from test accounts

- Applies to products with permissions when a new feature adds permissions.
- Write in: the sign-in helper.
- Guidance: use the product's own APIs to satisfy account prerequisites. For example, ERP gives a super administrator only the permissions that exist when the enterprise is activated. Add new permissions through its role-management API.

### The back end is in another repository

- Applies to frontends and backends in separate repositories.
- Write in: the environment tool.
- Guidance: state which checkout of the other repository is in use. If it differs from the last run, say so rather than switching silently.

### Authenticator codes are single-use per window

- Applies to authenticators whose code can be used only once in a time window.
- Guidance: all sign-in scripts share the last-used window.

### A secret is displayed only once

- Applies to secrets that are displayed only once.
- Guidance: read the secret immediately and save it in a file with mode `600`.

### Consecutive pages have identically named fields

- Applies when consecutive pages have inputs with the same name.
- Guidance: wait for the new page's landmark before filling the input.

### Environment-tool locks survive failure

- Applies to environment tools that use locks.
- Guidance: release the lock on failure. Take over when the process holding the lock is gone.

### Back-end tests require an environment variable

- Applies to back-end integration tests enabled by an environment variable.
- Guidance: give back-end tests a dedicated database separate from the e2e database. A run counts only when the skip count is zero.

### Repository lint scans the whole tree

- Applies to repositories whose lint scans the whole tree.
- Guidance: ignore test artifacts and environment directories.

### Database health passes during initialization

- Symptom: a database health check can pass while initialization scripts are still running.

### pnpm rejects packages less than a day old

- Applies to pnpm 11.
- Symptom: it does not install packages published less than a day ago.
- Guidance: install an exact older version. Do not accept an exception.

### Tests share writable state

- Applies when tests in one run share writable configuration or a database.
- Symptom: two tests saving at the same time conflict.
- Guidance: set `workers: 1`.

### Fixed timestamps eventually include a date

- Applies to pages that include the date when a time is not today.
- Cause: a fixed timestamp in test data eventually stops being today.
- Guidance: allow the date in assertions.
