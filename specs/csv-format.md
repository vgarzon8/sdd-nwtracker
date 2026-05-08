# CSV Format

This document defines the CSV files used by `GET /export` and `POST /import`.

## File inventory

| File | Table(s) |
|------|----------|
| `currencies.csv` | `currency` |
| `tags.csv` | `tag` |
| `institutions.csv` | `institution` |
| `accounts.csv` | `account` + `account_tag` |
| `balances.csv` | `balance` |
| `exchange_rates.csv` | `exchange_rate` |

All files are UTF-8 encoded with a header row. The column delimiter is a comma. Fields containing commas, newlines, or double-quotes are double-quote-quoted per RFC 4180 (handled automatically by Python's `csv` module).

## Natural keys

Exported CSVs do **not** include synthetic integer IDs. All cross-file references use natural keys:

- `accounts.csv` references institutions by `institution_name` and currencies by `currency_code`.
- `balances.csv` references accounts by `account_name`.
- `exchange_rates.csv` references currencies by `currency_code`.

This makes the CSV portable: importing into a fresh DB does not require IDs to match.

## Column definitions

### currencies.csv

| Column | Type | Description |
|--------|------|-------------|
| `code` | string | ISO 4217 currency code (e.g., `USD`, `CNY`); natural primary key |
| `name` | string | Human-readable name (e.g., `US Dollar`) |

### tags.csv

| Column | Type | Description |
|--------|------|-------------|
| `name` | string | Tag name; must be unique; must not contain a semicolon |

### institutions.csv

| Column | Type | Description |
|--------|------|-------------|
| `name` | string | Institution name; must be unique |

### accounts.csv

| Column | Type | Description |
|--------|------|-------------|
| `name` | string | Account name; must be unique |
| `institution_name` | string | Institution name; must match a row in `institutions.csv` |
| `currency_code` | string | Currency code; must match a row in `currencies.csv` |
| `side` | string | `asset` or `liability` |
| `status` | string | `active` or `closed` |
| `tags` | string | Semicolon-separated tag names (e.g., `retirement;long-term`); empty string if no tags |

### balances.csv

| Column | Type | Description |
|--------|------|-------------|
| `account_name` | string | Account name; must match a row in `accounts.csv` |
| `month` | string | `YYYY-MM` format |
| `amount` | integer | Balance in whole currency units |

### exchange_rates.csv

| Column | Type | Description |
|--------|------|-------------|
| `currency_code` | string | Currency code; must match a row in `currencies.csv` |
| `month` | string | `YYYY-MM` format |
| `rate` | decimal | Units of this currency per 1 USD; up to 4 decimal places (e.g., `7.1000`) |

## Import processing order

Files are always imported in this order to satisfy foreign key constraints:

1. `currencies.csv`
2. `tags.csv`
3. `institutions.csv`
4. `accounts.csv`
5. `balances.csv`
6. `exchange_rates.csv`

## Example

A minimal valid set of files for a portfolio with one USD checking account and one CNY savings account:

**currencies.csv**
```
code,name
USD,US Dollar
CNY,Chinese Yuan
```

**tags.csv**
```
name
checking
savings
```

**institutions.csv**
```
name
Chase
ICBC
```

**accounts.csv**
```
name,institution_name,currency_code,side,status,tags
Chase Checking,Chase,USD,asset,active,checking
ICBC Savings,ICBC,CNY,asset,active,savings
```

**balances.csv**
```
account_name,month,amount
Chase Checking,2024-01,15000
ICBC Savings,2024-01,50000
```

**exchange_rates.csv**
```
currency_code,month,rate
CNY,2024-01,7.1000
```
