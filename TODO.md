# Aroma Delight Dashboard — Delivery TODO

## 1. Secure foundation and project runtime

- [ ] Django project starts on the configured port and exposes `/health/` with an unauthenticated success response.
- [ ] Runtime reads `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS` and security flags from environment configuration; no credential is committed.
- [ ] The project contains deterministic migrations, a repeatable demo-data command, a Dockerfile and a production entrypoint.
- [ ] `/manus-routes.json` lists every user-facing route and excludes APIs, assets and health endpoints.

## 2. Staff identity, roles and accountability

- [ ] Staff users authenticate through Django’s secure session flow; passwords are hashed and there is no public self-registration.
- [ ] Manager, cashier, barista and system-administrator roles are represented and enforced server-side.
- [ ] Permission-aware navigation is complemented by permission checks on every protected view and mutation.
- [ ] Sensitive actions create audit records without passwords, payment secrets or unnecessary personal data.

## 3. Menu and inventory operations

- [ ] Authorised roles can create, edit, activate/deactivate and price menu products.
- [ ] Inventory records support quantity on hand, reorder level, stock adjustments and visible low-stock states.
- [ ] Invalid quantities, negative prices and unauthorised mutations are rejected server-side with safe feedback.

## 4. Order and payment operations

- [ ] Cashiers can create an order containing one or more available products with positive quantities.
- [ ] Totals are calculated from server-side current prices; client-submitted totals are never trusted.
- [ ] Orders expose clear pending/preparing/ready/completed/cancelled statuses and permitted staff can update them.
- [ ] Manual payment records capture method, amount, status and a safe reference without implementing a live gateway.
- [ ] A receipt view exposes the order, items, totals, payment summary and timestamp for viewing or printing.

## 5. Customers and reporting

- [ ] Staff can search and maintain privacy-conscious customer records within their role permissions.
- [ ] The dashboard shows revenue, order volume, average ticket, payment mix, best sellers, recent activity and low-stock items for a selected period.
- [ ] Charts and metrics are derived from persisted records and handle an empty dataset without errors.

## 6. Quality and DevOps evidence

- [ ] Automated tests cover at least order-total integrity and role-protected inventory mutation as explicit unit-test cases.
- [ ] CI runs migrations/checks/tests and a dependency/security scan on every push or pull request.
- [ ] The implementation is documented clearly enough for the Part 2 architecture/design report and Jenkins or CircleCI demonstration.
- [ ] The finished code is committed to `mesmeric-bee05/Grp-II-Software-Engineering-2` on `main` without secrets or generated databases.
