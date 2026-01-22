import pandas as pd
import streamlit as st
from pathlib import Path
from i18n import get_month_names


def fill_missing_months(df: pd.DataFrame, year: int, value_column: str = "Dépense", group_columns: list[str] | None = None) -> pd.DataFrame:
    """
    Fill missing months in a dataframe with zero values.

    Args:
        df: DataFrame with a 'YearMonth' column (as string, e.g., '2024-01')
        year: The year to fill months for
        value_column: The column containing values (will be filled with 0)
        group_columns: Optional list of columns to preserve groups for (e.g., ['Tiers'] for person data)

    Returns:
        DataFrame with all 12 months, missing ones filled with 0
    """
    # Create all months for the year
    all_months = [f"{year}-{m:02d}" for m in range(1, 13)]

    if group_columns:
        # Get unique combinations of group columns
        if not df.empty:
            unique_groups = df[group_columns].drop_duplicates().to_dict('records')
        else:
            unique_groups = []

        # Create a complete index with all months for each group
        rows = []
        for month in all_months:
            for group in unique_groups:
                row = {"YearMonth": month, value_column: 0}
                row.update(group)
                rows.append(row)

        if not rows:
            # No groups found, just return empty df with all months
            return pd.DataFrame({"YearMonth": all_months, value_column: [0] * 12})

        full_df = pd.DataFrame(rows)

        # Merge with actual data
        merge_cols = ["YearMonth"] + group_columns
        result = full_df.merge(
            df[merge_cols + [value_column]],
            on=merge_cols,
            how="left",
            suffixes=("_default", "")
        )

        # Use actual values where available, otherwise use 0
        if f"{value_column}_default" in result.columns:
            result[value_column] = result[value_column].fillna(result[f"{value_column}_default"])
            result = result.drop(columns=[f"{value_column}_default"])

        result[value_column] = result[value_column].fillna(0)

        return result.sort_values(["YearMonth"] + group_columns)
    else:
        # Simple case: just fill missing months
        full_df = pd.DataFrame({"YearMonth": all_months, value_column: 0})

        if df.empty:
            return full_df

        result = full_df.merge(
            df[["YearMonth", value_column]],
            on="YearMonth",
            how="left",
            suffixes=("_default", "")
        )

        if f"{value_column}_default" in result.columns:
            result[value_column] = result[value_column].fillna(result[f"{value_column}_default"])
            result = result.drop(columns=[f"{value_column}_default"])

        result[value_column] = result[value_column].fillna(0)

        return result.sort_values("YearMonth")


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load all CSV files from data directory and combine them."""
    data_dir = Path(__file__).parent.parent / "data"
    all_data = []

    for csv_file in data_dir.glob("*.csv"):
        df = pd.read_csv(
            csv_file,
            sep=";",
            decimal=",",
            encoding="utf-8"
        )
        df["source_file"] = csv_file.name
        all_data.append(df)

    if not all_data:
        return pd.DataFrame()

    combined = pd.concat(all_data, ignore_index=True)

    # Parse dates
    combined["Date"] = pd.to_datetime(combined["Date"], format="%d/%m/%Y")

    # Convert amounts to float
    combined["Dépense"] = pd.to_numeric(combined["Dépense"], errors="coerce").fillna(0)
    combined["Revenu"] = pd.to_numeric(combined["Revenu"], errors="coerce").fillna(0)

    # Remove duplicates (same date, same amount, same person, same notes)
    combined = combined.drop_duplicates(
        subset=["Date", "Dépense", "Tiers", "Notes"],
        keep="first"
    )

    # Add year and month columns
    combined["Year"] = combined["Date"].dt.year
    combined["Month"] = combined["Date"].dt.month
    combined["YearMonth"] = combined["Date"].dt.to_period("M")

    return combined


def get_persons(df: pd.DataFrame) -> list[str]:
    """Get list of unique persons from the data."""
    return sorted(df["Tiers"].dropna().unique().tolist())


def get_years(df: pd.DataFrame) -> list[int]:
    """Get list of unique years from the data."""
    return sorted(df["Year"].unique())


def get_categories(df: pd.DataFrame) -> list[str]:
    """Get list of unique categories from the data."""
    return sorted(df["Catégorie"].dropna().unique().tolist())


def get_data_dir() -> Path:
    """Get the data directory path."""
    return Path(__file__).parent.parent / "data"


def get_available_files() -> list[str]:
    """Get list of available CSV files in data directory."""
    data_dir = get_data_dir()
    return sorted([f.name for f in data_dir.glob("*.csv")])


@st.cache_data
def load_single_file(filename: str) -> pd.DataFrame:
    """Load a single CSV file and process it."""
    data_dir = get_data_dir()
    filepath = data_dir / filename

    if not filepath.exists():
        return pd.DataFrame()

    df = pd.read_csv(
        filepath,
        sep=";",
        decimal=",",
        encoding="utf-8"
    )
    df["source_file"] = filename

    # Parse dates
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")

    # Convert amounts to float
    df["Dépense"] = pd.to_numeric(df["Dépense"], errors="coerce").fillna(0)
    df["Revenu"] = pd.to_numeric(df["Revenu"], errors="coerce").fillna(0)

    # Remove duplicates (same date, same amount, same person, same notes)
    df = df.drop_duplicates(
        subset=["Date", "Dépense", "Tiers", "Notes"],
        keep="first"
    )

    # Add year and month columns
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["YearMonth"] = df["Date"].dt.to_period("M")

    return df
