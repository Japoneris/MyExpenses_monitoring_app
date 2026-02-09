import os
import logging
import pandas as pd
import streamlit as st
from pathlib import Path
from i18n import get_month_names

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_data_dir() -> Path:
    """Get the data directory path.

    Priority:
    1. DATA_DIR environment variable (for both Docker and local configs)
    2. /app/data if it exists (Docker default)
    3. src/data relative to this file (local development fallback)
    """
    # Check environment variable first
    env_data_dir = os.environ.get("DATA_DIR")
    if env_data_dir:
        return Path(env_data_dir)

    # Docker default path
    docker_path = Path("/app/data")
    if docker_path.exists():
        return docker_path

    # Local development fallback (src/data)
    return Path(__file__).parent / "data"


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
            # No groups found, return empty df with correct columns
            columns = ["YearMonth"] + group_columns + [value_column]
            return pd.DataFrame(columns=columns)

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
    data_dir = get_data_dir()
    all_data = []

    csv_files = list(data_dir.glob("*.csv"))
    logger.info(f"Found {len(csv_files)} CSV file(s) in {data_dir}")

    for csv_file in csv_files:
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

    # Parse dates with error handling
    combined["Date"] = pd.to_datetime(combined["Date"], format="%d/%m/%Y", errors="coerce")

    # Check for and log invalid dates before filtering
    invalid_dates_mask = combined["Date"].isna()
    if invalid_dates_mask.any():
        invalid_rows = combined[invalid_dates_mask]
        for source_file in invalid_rows["source_file"].unique():
            file_invalid_count = (invalid_rows["source_file"] == source_file).sum()
            logger.warning(
                f"File '{source_file}' contains {file_invalid_count} row(s) with invalid/broken dates - these rows will be discarded"
            )
        # Discard rows with invalid dates
        combined = combined[~invalid_dates_mask]
        logger.info(f"Discarded {invalid_dates_mask.sum()} row(s) with invalid dates")

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


def get_available_files() -> list[str]:
    """Get list of available CSV files in data directory."""
    data_dir = get_data_dir()
    return sorted([f.name for f in data_dir.glob("*.csv")])


def check_invalid_dates() -> pd.DataFrame:
    """Check all CSV files for rows with invalid dates.

    Returns a DataFrame with the problematic rows including:
    - source_file: the filename containing the invalid date
    - row_number: the row number in the original CSV file (1-indexed, excluding header)
    - original_date: the raw date value that couldn't be parsed
    - Other columns from the original data for context
    """
    data_dir = get_data_dir()
    all_invalid = []

    csv_files = list(data_dir.glob("*.csv"))

    for csv_file in csv_files:
        try:
            df = pd.read_csv(
                csv_file,
                sep=";",
                decimal=",",
                encoding="utf-8"
            )

            # Skip files without a Date column
            if "Date" not in df.columns:
                logger.warning(f"File '{csv_file.name}' has no 'Date' column, skipping")
                continue

            # Store original date value before parsing
            df["original_date"] = df["Date"].astype(str)
            df["source_file"] = csv_file.name
            df["row_number"] = range(2, len(df) + 2)  # 1-indexed, +1 for header row

            # Try to parse dates
            df["Date_parsed"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")

            # Find invalid dates
            invalid_mask = df["Date_parsed"].isna()
            if invalid_mask.any():
                invalid_rows = df[invalid_mask].copy()
                all_invalid.append(invalid_rows)
        except Exception as e:
            logger.error(f"Error reading file '{csv_file.name}': {e}")
            continue

    if not all_invalid:
        return pd.DataFrame()

    return pd.concat(all_invalid, ignore_index=True)


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

    # Parse dates with error handling
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")

    # Check for and log invalid dates before filtering
    invalid_dates_mask = df["Date"].isna()
    if invalid_dates_mask.any():
        logger.warning(
            f"File '{filename}' contains {invalid_dates_mask.sum()} row(s) with invalid/broken dates - these rows will be discarded"
        )
        # Discard rows with invalid dates
        df = df[~invalid_dates_mask]

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
