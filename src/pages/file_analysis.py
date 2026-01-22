import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import (
    load_single_file,
    get_available_files,
    get_persons,
    get_categories,
)
from i18n import t, get_month_names


st.title(t("file.title"))

# Get available files
files = get_available_files()

if not files:
    st.error(t("errors.no_files"))
    st.stop()

# File selection
st.sidebar.header(t("file.file_selection"))
selected_file = st.sidebar.selectbox(t("file.select_file"), files)

# Load selected file
df = load_single_file(selected_file)

if df.empty:
    st.error(t("errors.could_not_load", filename=selected_file))
    st.stop()

# File info
st.header(t("file.analysis", filename=selected_file))

# Date range
date_min = df["Date"].min()
date_max = df["Date"].max()
st.info(t("file.date_range", start=date_min.strftime('%d/%m/%Y'), end=date_max.strftime('%d/%m/%Y')))

# Discover persons dynamically
persons = get_persons(df)

# Summary metrics
st.subheader(t("file.summary"))

cols = st.columns(len(persons) + 2)

total_expenses = df["Dépense"].sum()
cols[0].metric(t("common.total_expenses"), f"{total_expenses:,.2f} €")

num_transactions = len(df)
cols[1].metric(t("common.transactions"), num_transactions)

person_totals = {}
for i, person in enumerate(persons):
    person_total = df[df["Tiers"] == person]["Dépense"].sum()
    person_totals[person] = person_total
    cols[i + 2].metric(person, f"{person_total:,.2f} €")

# Balance calculation (only if exactly 2 persons)
if len(persons) == 2:
    difference = person_totals[persons[0]] - person_totals[persons[1]]
    if difference > 0:
        balance_text = t("file.owes", debtor=persons[1], creditor=persons[0], amount=f"{abs(difference/2):,.2f}")
    elif difference < 0:
        balance_text = t("file.owes", debtor=persons[0], creditor=persons[1], amount=f"{abs(difference/2):,.2f}")
    else:
        balance_text = t("file.balanced")
    st.info(t("file.balance", text=balance_text))

# Expenses per person
st.header(t("file.expenses_per_person"))

person_df = pd.DataFrame({
    "Person": persons,
    "Total": [person_totals[p] for p in persons]
})

fig_person = px.bar(
    person_df,
    x="Person",
    y="Total",
    title=t("file.total_by_person"),
    labels={"Total": t("common.expenses_euro"), "Person": t("common.person")},
    color="Person"
)
st.plotly_chart(fig_person, width="stretch")

# Expenses by category
st.header(t("file.expenses_by_category"))

category_total = (
    df.groupby("Catégorie")["Dépense"]
    .sum()
    .reset_index()
    .sort_values("Dépense", ascending=False)
)

col1, col2 = st.columns(2)

with col1:
    fig_pie = px.pie(
        category_total,
        values="Dépense",
        names="Catégorie",
        title=t("file.category_distribution")
    )
    st.plotly_chart(fig_pie, width="stretch")

with col2:
    fig_bar = px.bar(
        category_total,
        x="Catégorie",
        y="Dépense",
        title=t("file.expenses_by_category"),
        labels={"Catégorie": t("common.category"), "Dépense": t("common.amount")}
    )
    fig_bar.update_xaxes(tickangle=45)
    st.plotly_chart(fig_bar, width="stretch")

# Category breakdown per person
st.header(t("file.category_per_person"))

category_person = (
    df.groupby(["Catégorie", "Tiers"])["Dépense"]
    .sum()
    .reset_index()
)

fig_cat_person = px.bar(
    category_person,
    x="Catégorie",
    y="Dépense",
    color="Tiers",
    barmode="group",
    title=t("file.expenses_by_cat_person"),
    labels={"Catégorie": t("common.category"), "Dépense": t("common.expenses_euro"), "Tiers": t("common.person")}
)
fig_cat_person.update_xaxes(tickangle=45)
st.plotly_chart(fig_cat_person, width="stretch")

# Timeline if data spans multiple days
if (date_max - date_min).days > 1:
    st.header(t("file.expenses_over_time"))

    daily_expenses = (
        df.groupby(["Date", "Tiers"])["Dépense"]
        .sum()
        .reset_index()
    )

    fig_timeline = px.bar(
        daily_expenses,
        x="Date",
        y="Dépense",
        color="Tiers",
        title=t("file.daily_expenses"),
        labels={"Date": t("common.date"), "Dépense": t("common.expenses_euro"), "Tiers": t("common.person")}
    )
    st.plotly_chart(fig_timeline, width="stretch")

    # Cumulative expenses
    st.subheader(t("file.cumulative_expenses"))

    daily_total = df.groupby(["Date", "Tiers"])["Dépense"].sum().unstack(fill_value=0)

    fig_cumulative = go.Figure()
    for person in persons:
        if person in daily_total.columns:
            cumulative = daily_total[person].cumsum()
            fig_cumulative.add_trace(go.Scatter(
                x=cumulative.index,
                y=cumulative.values,
                name=person,
                mode="lines+markers"
            ))

    fig_cumulative.update_layout(
        title=t("file.cumulative_per_person"),
        xaxis_title=t("common.date"),
        yaxis_title=t("common.cumulative_expenses_euro")
    )
    st.plotly_chart(fig_cumulative, width="stretch")

# Top expenses
st.header(t("file.top_expenses"))

top_n = st.slider(t("file.top_expenses_slider"), min_value=5, max_value=20, value=10)

top_expenses = df.nlargest(top_n, "Dépense")[["Date", "Tiers", "Dépense", "Catégorie", "Notes"]]
top_expenses["Date"] = top_expenses["Date"].dt.strftime("%d/%m/%Y")

st.dataframe(
    top_expenses,
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

# Full transaction list
st.header(t("file.all_transactions"))

# Filters for the table
col1, col2 = st.columns(2)
with col1:
    filter_person = st.selectbox(t("file.filter_by_person"), [t("common.all")] + persons, key="file_person_filter")
with col2:
    filter_category = st.selectbox(t("file.filter_by_category"), [t("common.all")] + get_categories(df), key="file_cat_filter")

display_data = df[["Date", "Tiers", "Dépense", "Catégorie", "Notes"]].copy()

if filter_person != t("common.all"):
    display_data = display_data[display_data["Tiers"] == filter_person]
if filter_category != t("common.all"):
    display_data = display_data[display_data["Catégorie"] == filter_category]

display_data["Date"] = display_data["Date"].dt.strftime("%d/%m/%Y")
display_data = display_data.sort_values("Date")

st.dataframe(
    display_data,
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

# Summary statistics
st.header(t("file.statistics"))

col1, col2 = st.columns(2)

with col1:
    st.subheader(t("file.by_person"))
    stats_person = df.groupby("Tiers")["Dépense"].agg(["sum", "mean", "count", "max"])
    stats_person.columns = [t("common.total"), t("common.average"), t("common.count"), t("common.max")]
    st.dataframe(stats_person, width="stretch")

with col2:
    st.subheader(t("file.by_category"))
    stats_cat = df.groupby("Catégorie")["Dépense"].agg(["sum", "mean", "count"])
    stats_cat.columns = [t("common.total"), t("common.average"), t("common.count")]
    stats_cat = stats_cat.sort_values(t("common.total"), ascending=False)
    st.dataframe(stats_cat, width="stretch")
