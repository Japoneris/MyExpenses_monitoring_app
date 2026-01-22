# Expense Analyzer

Dashboard to analyze your Expenses.

Expenses files comes from [`MyExpenses` app](https://www.myexpenses.mobi/fr/) (do `export_to_csv`).

## Data

`.csv` files from `MyExpenses`  should be stored in `data/`

## Features

- Month per month overview
- Detail per product category
- Comparison per user (who pays more / is the budget balanced?)
- Full detail of raw transaction if needed
- Automatic sheat aggregation:
  - Remove duplicates
  - Split by year
  - Group by month

## Screenshots

TODO


---

# Usage 

## Run with Python

Create a virtual env: 

```sh
python3 -m venv venv
```

Activate it:

```sh
source venv/bin/activate
```

Install the libs:

```sh
pip3 install -r requirements.txt
```

Run:

```sh
cd src
streamlit run app.py
```

Access the app at: [http://localhost:8501](http://localhost:8501)



Note: you can configure language (`en` or `fr`) by setting
```sh
APP_LANGUAGE=fr streamlit run src/app.py
```


## Run with Docker Compose

0. Check the docker compose to modify env variables if needed
1. Build and start the container: `docker compose up -d`
2. Access the app at: http://localhost:8501
3. Stop the container: `docker compose down`

