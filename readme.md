# Expense Analyzer

Collect data from [`MyExpenses` app](https://www.myexpenses.mobi/fr/) (do `export_to_csv`).

This app help you to analyze budget, month after month.



# Usage 

## Local Development

- English (default): `streamlit run src/app.py`
- French: `APP_LANGUAGE=fr streamlit run src/app.py`

## Docker Compose

1. Copy the environment file: `cp .env.example .env`
2. Edit `.env` to set your preferences:
   - `APP_LANGUAGE`: Set to `en` (English) or `fr` (French)
   - `DATA_DIR`: Path to your data directory (default: `./data`)
3. Build and start the container: `docker-compose up -d`
4. Access the app at: http://localhost:8501
5. Stop the container: `docker-compose down`

Example with custom data directory:
```bash
DATA_DIR=/path/to/your/data APP_LANGUAGE=fr docker-compose up -d
```

# Data 

## Location

`.csv` files are stored in `data/`

## Format

Here are the columns you will find in any files.


# Dashboard

The dashboard is made with streamlit.

It should help to visualizer:

- total expenses month per month
- expensive per person month per month
- get access to the detailed sheat of a given month
- A total per year should be done.

# Notes

Some expense pages have duplicated entries (with same date, same amount).
You need to remove them, as this is just an export issue.
