import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_data, get_persons, get_years, get_categories, fill_missing_months, check_invalid_dates
from i18n import t, get_month_names


st.title(t("overview.title"))

# Check for invalid dates and display warnings
invalid_dates_df = check_invalid_dates()
if not invalid_dates_df.empty:
    with st.expander(f"**Warning: {len(invalid_dates_df)} row(s) with invalid dates found (click to expand)**", expanded=True):
        st.warning("The following rows have invalid/broken dates and will be discarded:")
        display_cols = ["source_file", "row_number", "original_date"]
        # Add other available columns for context
        for col in ["Tiers", "Dépense", "Catégorie", "Notes"]:
            if col in invalid_dates_df.columns:
                display_cols.append(col)
        st.dataframe(
            invalid_dates_df[display_cols],
            hide_index=True,
            column_config={
                "source_file": "File",
                "row_number": "Row #",
                "original_date": "Invalid Date Value",
                "Tiers": "Person",
                "Dépense": "Amount",
                "Catégorie": "Category",
                "Notes": "Notes"
            }
        )

df = load_data()

if df.empty:
    st.error(t("errors.no_data"))
    st.stop()

# Sidebar filters
st.sidebar.header(t("common.filters"))

years = get_years(df)
selected_year = st.sidebar.selectbox(t("common.select_year"), years, index=len(years) - 1)

categories = [t("common.all")] + get_categories(df)
selected_category = st.sidebar.selectbox(t("common.select_category"), categories)

# Filter data
year_data = df[df["Year"] == selected_year]
if selected_category != t("common.all"):
    year_data = year_data[year_data["Catégorie"] == selected_category]

# Discover persons dynamically
persons = get_persons(df)

# Year totals section
st.header(t("overview.year_overview", year=selected_year))

# Create columns dynamically based on number of persons
cols = st.columns(len(persons) + 1)

total_expenses = year_data["Dépense"].sum()
cols[0].metric(t("common.total_expenses"), f"{total_expenses:,.2f} €")

person_totals = {}
for i, person in enumerate(persons):
    person_total = year_data[year_data["Tiers"] == person]["Dépense"].sum()
    person_totals[person] = person_total
    cols[i + 1].metric(f"{person}", f"{person_total:,.2f} €")

# Balance calculation (only if exactly 2 persons)
if len(persons) == 2:
    difference = person_totals[persons[0]] - person_totals[persons[1]]
    if difference > 0:
        balance_text = t("overview.owes", debtor=persons[1], creditor=persons[0], amount=f"{abs(difference/2):,.2f}")
    elif difference < 0:
        balance_text = t("overview.owes", debtor=persons[0], creditor=persons[1], amount=f"{abs(difference/2):,.2f}")
    else:
        balance_text = t("overview.balanced")
    st.info(t("overview.balance", text=balance_text))
elif len(persons) > 2:
    avg_expense = total_expenses / len(persons)
    st.subheader(t("overview.balance_summary"))
    for person in persons:
        diff = person_totals[person] - avg_expense
        if diff > 0:
            st.write(t("overview.spent_more", person=person, amount=f"{diff:,.2f}"))
        elif diff < 0:
            st.write(t("overview.spent_less", person=person, amount=f"{abs(diff):,.2f}"))

# Monthly expenses chart
st.header(t("overview.monthly_expenses"))

monthly_total = (
    year_data.groupby(["YearMonth"])["Dépense"]
    .sum()
    .reset_index()
)
monthly_total["YearMonth"] = monthly_total["YearMonth"].astype(str)
monthly_total = fill_missing_months(monthly_total, selected_year)

fig_monthly = px.bar(
    monthly_total,
    x="YearMonth",
    y="Dépense",
    title=t("overview.total_per_month"),
    labels={"YearMonth": t("common.month"), "Dépense": t("common.expenses_euro")}
)
st.plotly_chart(fig_monthly, width="stretch")

# Expenses per person per month
st.header(t("overview.expenses_per_person_month"))

monthly_person = (
    year_data.groupby(["YearMonth", "Tiers"])["Dépense"]
    .sum()
    .reset_index()
)
monthly_person["YearMonth"] = monthly_person["YearMonth"].astype(str)
monthly_person = fill_missing_months(monthly_person, selected_year, group_columns=["Tiers"])

fig_person = px.bar(
    monthly_person,
    x="YearMonth",
    y="Dépense",
    color="Tiers",
    barmode="group",
    title=t("overview.expenses_per_person_month"),
    labels={"YearMonth": t("common.month"), "Dépense": t("common.expenses_euro"), "Tiers": t("common.person")}
)
st.plotly_chart(fig_person, width="stretch")

# Cumulative expenses over months
st.header(t("overview.cumulative_over_time"))

monthly_balance = (
    year_data.groupby(["YearMonth", "Tiers"])["Dépense"]
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)
monthly_balance["YearMonth"] = monthly_balance["YearMonth"].astype(str)

# Fill missing months for cumulative chart
all_months = [f"{selected_year}-{m:02d}" for m in range(1, 13)]
monthly_balance = monthly_balance.set_index("YearMonth").reindex(all_months, fill_value=0).reset_index()
monthly_balance = monthly_balance.rename(columns={"index": "YearMonth"})

fig_balance = go.Figure()
for person in persons:
    if person in monthly_balance.columns:
        cumulative = monthly_balance[person].cumsum()
        fig_balance.add_trace(go.Scatter(
            x=monthly_balance["YearMonth"],
            y=cumulative,
            name=t("overview.person_cumulative", person=person),
            mode="lines+markers"
        ))

fig_balance.update_layout(
    title=t("overview.cumulative_per_person"),
    xaxis_title=t("common.month"),
    yaxis_title=t("common.cumulative_expenses_euro")
)
st.plotly_chart(fig_balance, width="stretch")

# Expenses by category
st.header(t("overview.expenses_by_category"))

category_total = (
    year_data.groupby("Catégorie")["Dépense"]
    .sum()
    .reset_index()
    .sort_values("Dépense", ascending=False)
)

fig_category = px.pie(
    category_total,
    values="Dépense",
    names="Catégorie",
    title=t("overview.distribution_by_category")
)
st.plotly_chart(fig_category, width="stretch")

# Detailed monthly view
st.header(t("overview.detailed_monthly"))

MONTH_NAMES = get_month_names()
months_in_year = sorted(year_data["Month"].unique())
month_options = [MONTH_NAMES[m] for m in months_in_year]

if month_options:
    selected_month_name = st.selectbox(t("common.select_month"), month_options)
    selected_month = [k for k, v in MONTH_NAMES.items() if v == selected_month_name][0]

    month_data = year_data[year_data["Month"] == selected_month].copy()

    # Month summary - dynamic columns
    cols = st.columns(len(persons) + 1)
    month_total = month_data["Dépense"].sum()
    cols[0].metric(t("overview.month_total", month=selected_month_name), f"{month_total:,.2f} €")

    for i, person in enumerate(persons):
        person_month = month_data[month_data["Tiers"] == person]["Dépense"].sum()
        cols[i + 1].metric(person, f"{person_month:,.2f} €")

    # Detailed table
    st.subheader(t("overview.expense_details"))

    display_columns = ["Date", "Tiers", "Dépense", "Catégorie", "Notes"]
    month_display = month_data[display_columns].copy()
    month_display["Date"] = month_display["Date"].dt.strftime("%d/%m/%Y")
    month_display = month_display.sort_values("Date")

    st.dataframe(
        month_display,
        width="stretch",
        hide_index=True,
        column_config={
            "Date": t("common.date"),
            "Tiers": t("common.person"),
            "Dépense": st.column_config.NumberColumn(t("common.amount"), format="%.2f"),
            "Catégorie": t("common.category"),
            "Notes": t("common.notes")
        }
    )
else:
    st.warning(t("errors.no_data_filters"))
