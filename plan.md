# Aroma Delight Coffee Shop Dashboard — Implementation Plan

## Product direction

Build a secure internal operations dashboard for Aroma Delight Coffee Shop in Limuru, Kenya. The first release supports authenticated staff workflows for products, orders, manual payments, inventory, customers and sales reporting. It does not claim to implement live payment gateways, delivery logistics or a mobile application.

## Implementation approach

- **Backend:** Python 3.12, Django 5.2, Django ORM, Django templates and Django authentication.
- **Persistence:** SQLite for local development and automated tests; `DATABASE_URL` support for the managed MySQL environment.
- **Security:** custom staff user roles, deny-by-default role decorators, CSRF-protected forms, server-side validation, secure password hashing, safe ORM queries, audit logging, protected environment configuration, defensive security headers and no sensitive values in logs.
- **Analytics:** ORM aggregations rendered as dashboard metrics and lightweight chart visualisations using CSS/SVG and Chart.js-free progressive enhancement, keeping the first release dependency-light.
- **Delivery:** a Dockerfile, health endpoint, deterministic migrations, seed command, pytest/Django tests, GitHub Actions CI and a CircleCI-compatible configuration for the Part 2 DevOps demonstration.
- **Preview:** Django development server on the managed project port, with `/manus-routes.json` as a route manifest and `/health/` as an unauthenticated readiness endpoint.

## Project structure

- `config/`: Django settings, URL routing, ASGI/WSGI and environment configuration.
- `dashboard/`: domain models, forms, role checks, views, reporting queries, audit helpers, admin and tests.
- `dashboard/templates/`: accessible base layout and workflow screens.
- `static/`: coffee-inspired CSS, small SVG brand assets and route metadata.
- `dashboard/management/commands/seed_demo.py`: repeatable demo data for development only.
- `requirements.txt`, `Dockerfile`, `entrypoint.sh`: reproducible runtime and deployment contract.
- `.github/workflows/ci.yml`, `.circleci/config.yml`: test and security-check automation.

## Design system

### Considered directions

1. **Editorial coffeehouse ledger** — 0.06 probability. Warm, tactile, calm, operationally focused.
2. **Neon cyber café** — 0.03 probability. High contrast, energetic, but too loud for a hospitality management tool.
3. **Monochrome enterprise console** — 0.08 probability. Efficient, but not distinctive enough for Aroma Delight.

### Selected style: Editorial coffeehouse ledger

- **Design movement:** contemporary editorial hospitality UI with the quiet confidence of a premium coffee roaster’s tasting room.
- **Core principles:** operational clarity, warm restraint, meaningful hierarchy and trustworthy detail.
- **Color philosophy:** dark roast ink anchors navigation and security-sensitive actions; crema surfaces reduce visual fatigue; espresso brown marks brand ownership; a restrained sage accent signals healthy stock and successful operations; amber is reserved for attention states.
- **Layout paradigm:** a narrow, persistent rail for orientation paired with an asymmetric content canvas; the dashboard opens with a “today at a glance” story before drilling into operational tables.
- **Signature elements:** a vertical roast-meter accent, soft crema cards with fine hairline borders, and pill-shaped status tokens that read like café order tickets.
- **Interaction philosophy:** every action should state what changed, preserve context and avoid surprise. Destructive or privileged actions require explicit intent and role permission.
- **Animation:** restrained 160–220ms fades and 4px lifts for cards; no continuous motion; charts reveal once on load and respect reduced-motion preferences.
- **Typography system:** `Fraunces` for display moments and section titles; `DM Sans` for body, controls and tabular data; strong numeric figures use tabular numerals.
- **Brand essence:** the calm command centre behind a better cup — precise, warm and quietly ambitious.
- **Brand voice:** concise, human and observant. Example lines: “A good day starts with a clear counter.” “Low stock, early enough to act.”
- **Wordmark/logo:** an abstract aroma swirl forming an “A” above a small coffee-bean notch, paired with the Aroma Delight wordmark.
- **Signature brand color:** roast brown `#6B3F2A`.

## Implementation boundaries

Part 2 requires architecture/design justification and a test plan with two unit-test cases using Jenkins or CircleCI. This implementation prepares the evidence by including focused tests and CI configuration, but the final Part 2 report will document the rationale and test results after the group reviews the running product.
