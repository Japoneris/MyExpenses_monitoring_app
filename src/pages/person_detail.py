import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_data, get_persons, get_years, get_categories, fill_missing_months
from i18n import t, get_month_names


st.title(t("person.title"))

df = load_data()

if df.empty:
    st.error(t("errors.no_data"))
    st.stop()

# Discover persons dynamically
persons = get_persons(df)

if not persons:
    st.error(t("errors.no_persons"))
    st.stop()

# Sidebar filters
st.sidebar.header(t("common.filters"))

selected_person = st.sidebar.selectbox(t("common.select_person"), persons)

years = get_years(df)
selected_year = st.sidebar.selectbox(t("common.select_year"), years, index=len(years) - 1)

categories = [t("common.all")] + get_categories(df)
selected_category = st.sidebar.selectbox(t("common.select_category"), categories)

# Filter data
person_data = df[(df["Tiers"] == selected_person) & (df["Year"] == selected_year)]
if selected_category != t("common.all"):
    person_data = person_data[person_data["Catégorie"] == selected_category]

# Year overview for this person
st.header(t("person.expenses_year", person=selected_person, year=selected_year))

col1, col2, col3 = st.columns(3)

total_expenses = person_data["Dépense"].sum()
col1.metric(t("common.total_expenses"), f"{total_expenses:,.2f} €")

num_transactions = len(person_data)
col2.metric(t("person.num_transactions"), num_transactions)

if num_transactions > 0:
    avg_expense = total_expenses / num_transactions
    col3.metric(t("person.avg_per_transaction"), f"{avg_expense:,.2f} €")

# Compare with others
st.header(t("person.comparison"))

year_data = df[df["Year"] == selected_year]
person_totals = year_data.groupby("Tiers")["Dépense"].sum().reset_index()
person_totals.columns = ["Person", "Total"]

fig_comparison = px.bar(
    person_totals,
    x="Person",
    y="Total",
    title=t("person.total_by_person", year=selected_year),
    labels={"Total": t("common.expenses_euro"), "Person": t("common.person")},
    color="Person"
)
# Highlight selected person
colors = ["lightgray" if p != selected_person else "#636EFA" for p in person_totals["Person"]]
fig_comparison.update_traces(marker_color=colors)
st.plotly_chart(fig_comparison, width="stretch")

# Monthly breakdown
st.header(t("person.monthly_breakdown"))

monthly_expenses = (
    person_data.groupby("YearMonth")["Dépense"]
    .sum()
    .reset_index()
)
monthly_expenses["YearMonth"] = monthly_expenses["YearMonth"].astype(str)
monthly_expenses = fill_missing_months(monthly_expenses, selected_year)

fig_monthly = px.bar(
    monthly_expenses,
    x="YearMonth",
    y="Dépense",
    title=t("person.monthly_expenses", person=selected_person),
    labels={"YearMonth": t("common.month"), "Dépense": t("common.expenses_euro")}
)
st.plotly_chart(fig_monthly, width="stretch")

# Category breakdown
st.header(t("person.expenses_by_category"))

category_expenses = (
    person_data.groupby("Catégorie")["Dépense"]
    .sum()
    .reset_index()
    .sort_values("Dépense", ascending=False)
)

col1, col2 = st.columns(2)

with col1:
    fig_pie = px.pie(
        category_expenses,
        values="Dépense",
        names="Catégorie",
        title=t("person.category_distribution")
    )
    st.plotly_chart(fig_pie, width="stretch")

with col2:
    fig_bar = px.bar(
        category_expenses,
        x="Catégorie",
        y="Dépense",
        title=t("person.expenses_by_category"),
        labels={"Catégorie": t("common.category"), "Dépense": t("common.amount")}
    )
    fig_bar.update_xaxes(tickangle=45)
    st.plotly_chart(fig_bar, width="stretch")

# Category evolution over months
st.header(t("person.category_evolution"))

monthly_category = (
    person_data.groupby(["YearMonth", "Catégorie"])["Dépense"]
    .sum()
    .reset_index()
)
monthly_category["YearMonth"] = monthly_category["YearMonth"].astype(str)
monthly_category = fill_missing_months(monthly_category, selected_year, group_columns=["Catégorie"])

fig_evolution = px.bar(
    monthly_category,
    x="YearMonth",
    y="Dépense",
    color="Catégorie",
    title=t("person.expenses_by_category_time", person=selected_person),
    labels={"YearMonth": t("common.month"), "Dépense": t("common.expenses_euro"), "Catégorie": t("common.category")}
)
st.plotly_chart(fig_evolution, width="stretch")

# Top expenses
st.header(t("person.top_expenses"))

top_expenses = person_data.nlargest(10, "Dépense")[["Date", "Dépense", "Catégorie", "Notes"]]
top_expenses["Date"] = top_expenses["Date"].dt.strftime("%d/%m/%Y")

st.dataframe(
    top_expenses,
    width="stretch",
    hide_index=True,
    column_config={
        "Date": t("common.date"),
        "Dépense": st.column_config.NumberColumn(t("common.amount"), format="%.2f"),
        "Catégorie": t("common.category"),
        "Notes": t("common.notes")
    }
)

# Full transaction list
st.header(t("person.all_transactions"))

display_data = person_data[["Date", "Dépense", "Catégorie", "Notes"]].copy()
display_data["Date"] = display_data["Date"].dt.strftime("%d/%m/%Y")
display_data = display_data.sort_values("Date", ascending=False)

st.dataframe(
    display_data,
    width="stretch",
    hide_index=True,
    column_config={
        "Date": t("common.date"),
        "Dépense": st.column_config.NumberColumn(t("common.amount"), format="%.2f"),
        "Catégorie": t("common.category"),
        "Notes": t("common.notes")
    }
)
