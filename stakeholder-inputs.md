# Stakehoder inputs

## Goals

- **nwtracker** is an application that helps users track their personal net worth.
- The user records financial account balances (assets and liabilities) on a monthly basis.
- The application also produces helpful summaries and reports, like assets, liabilities, and net worth over time.
- All data is stored locally in the user's environment.
- The user interacts with the data through graphical user interface, e.g., a web application.
- The application supports multiple currencies, with exchange rates stored for historical reference.
- Accounts have tags for gropuing and reporting purposes.
- Legacy data from a prior system can be imported via CSV files.
- The application should support exporting all data to CSV for backup or migration purposes.

## Non-Goals

- No multi-user support
- No network connectivity or cloud sync
- No real-time market data or automatic exchange rate fetching
- No sub-monthly granularity (months are the atomic time unit)
- No budgeting, forecasting, or transaction-level tracking

## Data Model

### Currencies

- Accounts have an associated currency.
- The system supports multiple currencies.
- Balances are stored in their original currency.
- Exchange rates are stored separately for reference.
- See "Exchange Rates" below.


| Field       | Type   | Constraints          |
|-------------|--------|----------------------|
| code         | string | Three-character Currency code, primary key, unique, e.g., "USD"   |
| description | string | Human-readable label |


### Tags

- Tags are free-form labels that can be associated with accounts for grouping and reporting purposes.
- Accounts can have zero or more tags, and tags can be shared across accounts.
- The application provides functionality to parse and manage tags as needed.


| Field | Type   | Constraints                    |
|-------|--------|--------------------------------|
| id  | int | Primary key, unique            |
| name  | string | Short label, unique |
| description  | string   | Optional free-text description |


### Institutions

Financial institutions where accounts are held.


| Field | Type   | Constraints                    |
|-------|--------|--------------------------------|
| id  | int | Primary key, unique            |
| name  | string | Short label, unique |
| description  | string   | Optional free-text description |


### Accounts

- Accounts represent individual financial accounts, categorized as either assets or liabilities.
- Each account is associated with a financial institution and a currency.
- Accounts have a status (active/inactive) that affects their visibility and inclusion in balance updates.
- Accounts have one or more "tags" for grouping and reporting purposes.


| Field         | Type   | Constraints                            |
|---------------|--------|----------------------------------------|
| id            | int    | Primary key                            |
| institution_id | int    | FK → institutions.id                  |
| name          | string | Short descriptive name, e.g., "checking"  |
| tags   | - | collection of tag ids |
| currency_code | string | FK → currencies.code, default "USD"    |
| side          | enum   | `"asset"` or `"liability"`, required    |
| status        | enum   | `"active"` or `"inactive"`, default "active" |


### Balances

- Account balance records for specific months.
- Each record represents the balance of a single account at the end of a given month.
- Balances are stored as integers in currency units (e.g., USD).
- Months are represented as "YYYY-MM" strings


| Field      | Type  | Constraints                                |
|------------|-------|--------------------------------------------|
| id         | int   | Primary key, auto-generated                |
| account_id | int   | FK → accounts.id                           |
| month      | string | Stored as "YYYY-MM" string                 |
| amount     | int   | Balance in i |


Composite unique constraint: `(account_id, month)`. A given account has at most one balance record per month.

### Exchange Rates


| Field         | Type  | Constraints                       |
|---------------|-------|-----------------------------------|
| id            | int   | Primary key, auto-generated       |
| currency_code | string | FK → currencies.code             |
| month         | string | Stored as "YYYY-MM" string        |
| rate          | float | Rate relative to base currency    |


Composite unique constraint: `(currency_code, month)`.

## Business Rules

### Amounts as Integers

- All balance amounts are stored as integers in the smallest unit of the currency (e g. whole USD).
- No floating-point arithmetic is used for balance values.

### Asset vs. Liability Accounting

Net worth is computed as:

```
net_worth = sum(balances for ASSET accounts) − sum(balances for LIABILITY accounts)
```

Liability balances are stored as positive integers; the account's side determines whether they subtract from or add to net worth.

### Account Status

- **active**: Included in balance update workflows and default list views.
- **inactive**: Hidden from default list views; excluded from interactive month-to-month balance update loops. Still visible when `--active-only` is disabled.

### Duplicate Prevention

- Account names are unique. Creating an account with a duplicate name is rejected.
- `(account_id, month)` is unique in balances. Roll-forward operations use insert-or-ignore to avoid duplicates.
- `(currency_code, month)` is unique in exchange rates.`

## Features

### Institution Management

- create, update, list, and delete financial institutions
- cascade delete accounts associated with an institution, with confirmation
- institutions can be associated with accounts during account creation or update

### Account Management

Basic CRUD operations for accounts, with interactive workflows for creation and updates.

- create account with metadata and initial balance, including tags
- list accounts with optional filtering by status and tags
- update account metadata (name, description, tags, currency, status)
- delete accounts and associated data -- requires confirmation
- cascade delete balances associated with an account, with confirmation

### Balance Management

Basic CRUD operations for balances, with interactive workflows for updates, roll-forward, deletion, and transfers.

- create or update balance for a specific account and month
- list balances for a specific month, with account details and category summaries
- roll forward balances from one month to the next for all active accounts
- delete a specific balance record for an account and month
- transfer an amount between two accounts for a specific month, applying correct accounting logic

### Manage Tags

- create and list tags
- associate tags with accounts during account creation or update
- use tags for filtering accounts in list views and reports

### Reports

#### Networth snapshot by month

Assets, liabilities, and net worth for a selected month

### Data Import / Export

#### Initialize Database from CSV

- Populate an empty database from a set of CSV files. Used for initial setup or migration.
- Import is idempotent and can be safely re-run on an existing database without creating duplicates.
- CSV files must be in a specific format and named according to the table they populate 
- The import process validates data integrity

#### Export Tables to CSV

Export all database tables to CSV files in a target directory.

## Configuration

- User environment variables to configure application's behavior, such as database file location and logging settings.
- Support `.env` files for local development configuration.

## Logging

- Log user actions and system events for debugging and audit purposes.
- Logs are stored in a local file with rotation and retention policies.

