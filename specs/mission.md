# Mission

## Purpose

`nwtracker` is a personal net worth tracker. It helps a single user monitor their financial health over time by recording account balances monthly and producing clear summaries of assets, liabilities, and net worth.

## Who It Is For

A single user managing their own finances locally — no accounts, no logins, no sharing.

## Core Values

- **Local-first.** All data lives on the user's machine. No cloud, no sync, no network calls.
- **Simple and durable.** SQLite as the database. CSV for import and export. The data must outlast the application.
- **Monthly granularity.** The month is the atomic unit of time. No sub-monthly entries, no daily tracking.
- **Multi-currency.** Accounts are held in their native currency. Exchange rates are recorded manually for historical reference.

## What It Does

- Record financial account balances (assets and liabilities) each month
- Organize accounts by institution, currency, and user-defined tags
- Roll balances forward month-to-month to reduce manual entry
- Report assets, liabilities, and net worth for any given month
- Import legacy data from CSV files
- Export all data to CSV for backup or migration
- Converse with a natural language AI assistant to query data, get insights, and enter balances
- Receive AI-generated monthly narrative summaries and anomaly alerts
- Get AI assistance when mapping and cleaning CSV data during import

## What It Does Not Do

- No multi-user support
- No cloud sync or network connectivity (except outbound AI API calls, which are opt-in and configurable)
- No real-time market data or automatic exchange rate fetching
- No sub-monthly granularity
- No budgeting, forecasting, or transaction-level tracking
