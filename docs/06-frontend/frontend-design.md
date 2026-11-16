# Frontend Product and Design Brief

## 1. Frontend responsibility

React provides the browser interface for the product catalogue, product detail view, and dashboard. Nginx serves the built static assets and proxies `/api/` requests to FastAPI. The browser must never connect directly to PostgreSQL or Redis.

## 2. Initial screens

### Product catalogue

- Display a list/grid of products.
- Show product name, price, category, and stock.
- Support category filtering and pagination once the API query contract is finalized.
- Provide clear loading, empty, and error states.

### Product detail

- Display all product fields returned by the API.
- Handle a missing product (404) with a not-found state.
- Avoid assuming a currency symbol until currency is specified.

### Dashboard

- Display total products, total inventory value, average product price, and products grouped by category.
- Format decimal values without converting through JavaScript floating-point arithmetic where that could alter monetary precision; use decimal-safe formatting/strings.
- Make the metric definition clear. Inventory value formula is pending confirmation.

### Product management actions

Create/update/delete endpoints are in scope. Whether the initial UI exposes these actions, and who is authorized to use them, must be decided after the authentication/access-control scope is resolved. Do not imply that a public unauthenticated UI is safe for production writes.

## 3. Design system decisions still open

The supplied project brief does not specify brand identity or visual style. Before detailed UI implementation, agree:

- Product name/logo and visual tone.
- Color palette and contrast requirements.
- Typography and spacing scale.
- Component library or custom component strategy.
- Responsive breakpoints and mobile navigation.
- Table vs. card/list presentation for products.
- Charting approach for category statistics, if charts are desired.

Do not fabricate branding and treat it as approved. A clean, restrained admin/dashboard layout is a reasonable prototype default only after the owner approves it.

## 4. UX quality requirements

- Responsive layout for desktop, tablet, and mobile.
- Keyboard-operable navigation and controls.
- Semantic HTML, visible focus states, labels, and accessible error messages.
- Loading, empty, error, and success feedback for network operations.
- Confirm destructive delete actions.
- Prevent accidental duplicate submissions while a mutation is pending.
- Keep API errors understandable without exposing backend internals.

## 5. Frontend implementation decisions

React is selected, but the following have not been chosen: build tool, router, state/data-fetching library, component system, form library, chart library, and frontend test tooling. Select only what the actual UI requires and record choices in `docs/01-architecture/tech-stack.md`.
