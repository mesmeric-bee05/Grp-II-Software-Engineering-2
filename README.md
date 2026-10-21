# Aroma Delight Coffee Shop Dashboard

A secure Django operations dashboard for the Aroma Delight Coffee Shop project in Limuru Town, Kiambu County, Kenya. The first release gives authorised staff a clear view of menu items, orders, manual payments, inventory, customers, sales rhythm and audit activity.

## Run locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # optional; export values in your shell
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 0.0.0.0:3000
```

Demo users are created only when the explicit `seed_demo` command is run. All seeded users use the development password `AromaDemo!2026`; replace or remove them before any real deployment. The application uses SQLite by default for local work and reads a MySQL-compatible `DATABASE_URL` when provided by the managed environment.

## Product scope

The dashboard supports role-aware operations for manager, cashier, barista and system administrator roles. It does not implement live M-Pesa/card gateway processing, delivery logistics, payroll or a mobile app. Payment records are manual operational records and intentionally do not store card or mobile-money credentials.

## Quality

`pytest` covers order-total integrity and server-side role protection. GitHub Actions and CircleCI configurations run Django checks, migrations, tests and Bandit; the GitHub workflow also runs pip-audit. CI files are prepared for the BCS 3106 Part 2 DevOps demonstration.

## Repository

https://github.com/mesmeric-bee05/Grp-II-Software-Engineering-2
