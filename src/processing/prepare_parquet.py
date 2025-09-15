#!/usr/bin/env python3
"""
Converts the original CSV or Parquet file into a cleaned Parquet file for the streamlit app.

Usage:
    pdm run prepare_parquet.py input.csv output.parquet
    pdm run prepare_parquet.py input.parquet output.parquet
"""

import sys
from pathlib import Path

import pandas as pd

PARQUET_COMPRESSION = "zstd"
ENGINE = "pyarrow"
DAY_FIRST = True

REPLACE_NEWLINE_WITH_SPACE = True

MIN_YEAR = 2010
MAX_YEAR = 2025

MIN_YEAR_SEEN = 2000
MAX_YEAR_SEEN = 2026

COLUMN_NAMES = {
    "index": "Index",
    "data_source": "Source",
    "dept": "Department",
    "amount": "Amount",
    "date_payment": "Payment date",
    "year_payment": "Payment year",
    "supplier": "Supplier",
    "normalized_supplier": "Supplier (norm)",
    "contractsfinder_awardedtovcse": "CF -> VCSE",
    "contractsfinder_region": "CF region",
    "daterange_org_seen": "Date range (org seen)",
    "daterange_org_seen_min_date": "Org seen - min date",
    "daterange_org_seen_max_date": "Org seen - max date",
    "total_value_payments_to_org": "Total value payment (supplier)",
    "total_number_payments_to_org": "Total payments (org)",
    "orgflag": "Verification flag",
    "verifcode": "Verification code",
    "verifnote": "Verification note",
    "verifmatch": "Match type",
    "manual_match_to_spine": "Matched to spine?",
    "other_exact_match": "Supplier (norm) match?",
    "isspine_manual": "Is spine manual?",
    "isspine": "Is spine?",
    "longmatch": "Long match",
    "uid": "Spine uid",
    "organisationname": "Organisation",
    "fulladdress": "Address",
    "postcode": "Postcode",
    "city": "City",
    "registerdate": "Registration date",
    "removeddate": "Removal date",
    "latitude": "Latitude",
    "longitude": "Longitude",
    "geometry": "Geometry",
    "nuts_id_0": "NUTS ID 0",
    "nuts_name_0": "NUTS Name 0",
    "nuts_id_1": "NUTS ID 1",
    "nuts_name_1": "NUTS Name 1",
    "nuts_id_2": "NUTS ID 2",
    "nuts_name_2": "NUTS Name 2",
    "nuts_id_3": "NUTS ID 3",
    "nuts_name_3": "NUTS Name 3",
}


def prepare_parquet(in_fpath: Path, out_fpath: Path):
    """Load data from CSV or Parquet, processes it and outputs processed Parquet.

    Args:
        in_fpath (Path): Path to the input CSV or Parquet file.
        out_fpath (Path): Path to the output Parquet file for the processed data.
    """

    ext = in_fpath.suffix.lower()
    print(f"Reading {ext.upper()} file: {in_fpath}")

    if ext == ".csv":
        dset = pd.read_csv(in_fpath, parse_dates=True, low_memory=False)

        #  output the raw data as Parquet file
        fpath = in_fpath.with_suffix(".parquet")
        print(f"Writing Parquet (auto-named): {fpath}")
        dset.to_parquet(
            fpath,
            compression=PARQUET_COMPRESSION,
            engine=ENGINE,
        )
    elif ext == ".parquet":
        dset = pd.read_parquet(in_fpath)
    else:
        raise ValueError(f"Unsupported input extension: {ext} (use .csv or .parquet)")

    print(f"- records: {dset.shape[0]}, columns: {dset.shape[1]}")

    # process each column in turn
    # ----------------------------
    for column_name in dset.columns:
        print(f"Processing {column_name} ({dset[column_name].dtype})")
        match column_name:
            case "Unnamed: 0":
                dset = dset.drop(columns=[column_name])
                print("- column dropped")
            case "data_source":
                dset[column_name] = process_data_source(dset[column_name])
            case "dept":
                dset[column_name] = process_dept(dset[column_name])
            case "amount":
                dset[column_name] = process_amount(dset[column_name])
            case "supplier":
                dset[column_name] = process_supplier(dset[column_name])
            case "normalized_supplier":
                dset[column_name] = process_normalized_supplier(dset[column_name])
            case "date_payment":
                dset[column_name] = process_date_payment(dset[column_name])
            case "contractsfinder_awardedtovcse":
                dset[column_name] = process_contractsfinder_awardedtovcse(dset[column_name])
            case "contractsfinder_region":
                dset[column_name] = process_contractsfinder_region(dset[column_name])
            case "daterange_org_seen":
                dset[column_name] = process_daterange_org_seen(dset[column_name])
                dset = split_daterange_org_seen(dset)
            case "total_value_payments_to_org":
                dset[column_name] = process_total_value_payments_to_org(dset[column_name])
            case "total_number_payments_to_org":
                dset[column_name] = process_total_number_payments_to_org(dset[column_name])
            case "orgflag":
                dset[column_name] = process_orgflag(dset[column_name])
            case "verifmatch":
                dset[column_name] = process_verifmatch(dset[column_name])
            case "verifcode":
                dset[column_name] = process_verifcode(dset[column_name])
            case "verifnote":
                dset[column_name] = process_verifcode(dset[column_name])
            case "manual_match_to_spine":
                dset[column_name] = process_manual_match_to_spine(dset[column_name])
            case "other_exact_match":
                dset[column_name] = process_other_exact_math(dset[column_name])
            case "isspine_manual":
                dset[column_name] = process_is_spine_manual(dset[column_name])
            case "isspine":
                dset[column_name] = process_is_spine(dset[column_name])
            case "longmatch":
                dset[column_name] = process_longmatch(dset[column_name])
            case "uid":
                dset[column_name] = process_uid(dset[column_name])
            case "organisationname":
                dset[column_name] = process_organisationname(dset[column_name])
            case "fulladdress":
                dset[column_name] = process_fulladdress(dset[column_name])
            case "city":
                dset[column_name] = process_city(dset[column_name])
            case "postcode":
                dset[column_name] = process_postcode(dset[column_name])
            case "registerdate":
                dset[column_name] = process_registerdate(dset[column_name])
            case "removeddate":
                dset[column_name] = process_removeddate(dset[column_name])
            case "latitude":
                dset[column_name] = process_latitude(dset[column_name])
            case "longitude":
                dset[column_name] = process_longitude(dset[column_name])
            case "geometry":
                dset = dset.drop(columns=[column_name])
                print("- column dropped")
            case "nuts_id_1":
                dset[column_name] = process_nuts_id(dset[column_name])
            case "nuts_name_1":
                dset[column_name] = process_nuts_name(dset[column_name])
            case "nuts_id_2":
                dset[column_name] = process_nuts_id(dset[column_name])
            case "nuts_name_2":
                dset[column_name] = process_nuts_name(dset[column_name])
            case "nuts_id_3":
                dset[column_name] = process_nuts_id(dset[column_name])
            case "nuts_name_3":
                dset[column_name] = process_nuts_name(dset[column_name])
            case _:
                print("- processing not implemented - skipping")

    # filter out date outliers outside MIN_YEAR to MAX_YEAR
    # -----------------------------------------------------
    column_name = "date_payment"
    column_year = "year_payment"

    print(f"Filtering out {column_name} outside {MIN_YEAR}-{MAX_YEAR}")
    dset[column_year] = dset[column_name].dt.year

    # get and filter outliers
    mask_outliers = ~dset[column_year].between(MIN_YEAR, MAX_YEAR)
    dset_outliers = dset.loc[mask_outliers]
    print(
        f"- outliers records with {column_name} outside {MIN_YEAR}-{MAX_YEAR}: "
        f"{dset_outliers.shape[0]}"
    )

    fpath = Path(out_fpath).with_name(Path(out_fpath).stem + "_outliers.csv")
    dset_outliers.to_csv(fpath, index=False)
    print(f"- outliers written to: {fpath}")

    # filter data
    dset = dset.loc[dset[column_year].between(MIN_YEAR, MAX_YEAR)]
    print(f"- records with {column_name} between {MIN_YEAR} and {MAX_YEAR}: {dset.shape[0]}")

    # rename columns
    dset = dset.rename(COLUMN_NAMES)

    # write the processed data
    print(f"Writing processed data to: {out_fpath}")
    if ext == ".parquet":
        dset.to_parquet(out_fpath, compression=PARQUET_COMPRESSION, engine=ENGINE)
    elif ext == ".csv":
        dset.to_csv(out_fpath)
    else:
        raise ValueError(f"Unsupported output extension: {ext}. Use .parquet or .csv")


def replace_newline_with_space(
    s: pd.Series, do_replace: bool = REPLACE_NEWLINE_WITH_SPACE
) -> pd.Series:
    """Replace newline characters with spaces in a pandas Series.
    Args:
        s (pd.Series): Input pandas Series.
    Returns:
        pd.Series: Series with newline characters replaced by spaces.
    """
    if do_replace:
        print("- replaced newline characters with spaces")
        return s.str.replace("\n", " ", regex=False)
    return s


def process_data_source(s: pd.Series) -> pd.Series:
    """Process the 'data_source' column: clean text and convert to categorical.
    Args:
        s (pd.Series): Input pandas Series for the 'data_source' column.
    Returns:
        pd.Series: Series with processed 'data_source' column.
    """

    print(f"- null values: {s.isna().sum()}")

    # ensure dtype is string
    s = s.astype("string")

    s = replace_newline_with_space(s, REPLACE_NEWLINE_WITH_SPACE)

    # specific replacement
    to_replace = ["NHSSpend", "NHS Spend"]
    s = s.str.replace(to_replace[0], to_replace[1], regex=False)
    print(f"- replaced {to_replace[0]} with {to_replace[1]}")

    # cast to categorical
    s = s.astype("category")
    cats = s.cat.categories.tolist()
    print(f"- cast to Categorical with {len(cats)} unique values: {cats}")
    print(f"- processed dtype: {s.dtype}")

    return s


def process_dept(s: pd.Series) -> pd.Series:
    """Process the 'dept' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'dept' column.
    Returns:
        pd.Series: Series with processed 'dept' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    # ensure dtype is string
    s = s.astype("string")

    s = replace_newline_with_space(s, REPLACE_NEWLINE_WITH_SPACE)
    print(f"- processed dtype: {s.dtype}")

    return s


def process_amount(s: pd.Series) -> pd.Series:
    """Process the 'amount' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'amount' column.
    Returns:
        pd.Series: Series with processed 'amount' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_supplier(s: pd.Series) -> pd.Series:
    """Process the 'supplier' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'supplier' column.
    Returns:
        pd.Series: Series with processed 'amount' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    # ensure dtype is string
    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_normalized_supplier(s: pd.Series) -> pd.Series:
    """Process the 'normalized_supplier' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'normalized_supplier' column.
    Returns:
        pd.Series: Series with processed 'normalized_supplier' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    # ensure dtype is string
    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_date_payment(s: pd.Series) -> pd.Series:
    """Process the 'date_payment' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'date_payment' column.
    Returns:
        pd.Series: Series with processed 'date_payment' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = pd.to_datetime(s, errors="coerce", dayfirst=True)

    print(f"- processed dtype: {s.dtype}")

    return s


def process_contractsfinder_awardedtovcse(s: pd.Series) -> pd.Series:
    """Process the 'contractsfinder_awardedtovcse' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'contractsfinder_awardedtovcse' column.
    Returns:
        pd.Series: Series with processed 'contractsfinder_awardedtovcse' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("boolean")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_contractsfinder_region(s: pd.Series) -> pd.Series:
    """Process the 'contractsfinder_region' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'contractsfinder_region' column.
    Returns:
        pd.Series: Series with processed 'contractsfinder_region' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_daterange_org_seen(s: pd.Series) -> pd.Series:
    """Process the 'daterange_org_seen' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'daterange_org_seen' column.
    Returns:
        pd.Series: Series with processed 'daterange_org_seen' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


def split_daterange_org_seen(dset: pd.DataFrame) -> pd.DataFrame:
    """Split the 'daterange_org_seen' column into min and max date columns, and extract years.
    Args:
        dset (pd.DataFrame): Input pandas DataFrame containing the 'daterange_org_seen' column.
    Returns:
        pd.DataFrame: DataFrame with additional columns for min and max dates and years.
    """

    column_name = "daterange_org_seen"

    column_min = f"{column_name}_min_date"
    column_max = f"{column_name}_max_date"
    column_min_year = f"{column_name}_min_year"
    column_max_year = f"{column_name}_max_year"

    df = dset.copy()

    # normalise dashes and split
    s = df[column_name].astype("string").str.replace(r"[–—]", "-", regex=True)
    parts = s.str.split("-", n=1, expand=True)

    # parse dates (coerce invalids to NaT, like strict=False)
    df[column_min] = pd.to_datetime(parts[0].str.strip(), dayfirst=DAY_FIRST, errors="coerce")
    df[column_max] = pd.to_datetime(
        parts[1].str.strip() if parts.shape[1] > 1 else pd.Series(pd.NA, index=df.index),
        dayfirst=DAY_FIRST,
        errors="coerce",
    )

    # year columns
    df[column_min_year] = df[column_min].dt.year
    df[column_max_year] = df[column_max].dt.year

    return df


def process_total_value_payments_to_org(s: pd.Series) -> pd.Series:
    """Process the 'total_value_payments_to_org' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'total_value_payments_to_org' column.
    Returns:
        pd.Series: Series with processed 'total_value_payments_to_org' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_total_number_payments_to_org(s: pd.Series) -> pd.Series:
    """Process the 'total_number_payments_to_org' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'total_number_payments_to_org' column.
    Returns:
        pd.Series: Series with processed 'total_number_payments_to_org' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_orgflag(s: pd.Series) -> pd.Series:
    """Process the 'orgflag' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'orgflag' column.
    Returns:
        pd.Series: Series with processed 'orgflag' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_verifmatch(s: pd.Series) -> pd.Series:
    """Process the 'verifmatch' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'verifmatch' column.
    Returns:
        pd.Series: Series with processed 'verifmatch' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_verifcode(s: pd.Series) -> pd.Series:
    """Process the 'verifcode' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'verifcode' column.
    Returns:
        pd.Series: Series with processed 'verifcode' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_verifnote(s: pd.Series) -> pd.Series:
    """Process the 'verifnote' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'verifnote' column.
    Returns:
        pd.Series: Series with processed 'verifnote' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_manual_match_to_spine(s: pd.Series) -> pd.Series:
    """Process the 'manual_match_to_spine' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'manual_match_to_spine' column.
    Returns:
        pd.Series: Series with processed 'manual_match_to_spine' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("boolean")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_other_exact_math(s: pd.Series) -> pd.Series:
    """Process the 'other_exact_math' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'other_exact_math' column.
    Returns:
        pd.Series: Series with processed 'other_exact_math' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("boolean")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_is_spine_manual(s: pd.Series) -> pd.Series:
    """Process the 'is_spine_manual' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'is_spine_manual' column.
    Returns:
        pd.Series: Series with processed 'is_spine_manual' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_is_spine(s: pd.Series) -> pd.Series:
    """Process the 'is_spine' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'is_spine' column.
    Returns:
        pd.Series: Series with processed 'is_spine' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("boolean")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_longmatch(s: pd.Series) -> pd.Series:
    """Process the 'longmatch' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'longmatch' column.
    Returns:
        pd.Series: Series with processed 'longmatch' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_uid(s: pd.Series) -> pd.Series:
    """Process the 'uid' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'uid' column.
    Returns:
        pd.Series: Series with processed 'uid' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_organisationname(s: pd.Series) -> pd.Series:
    """Process the 'organisationname' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'organisationname' column.
    Returns:
        pd.Series: Series with processed 'organisationname' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_fulladdress(s: pd.Series) -> pd.Series:
    """Process the 'fulladdress' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'fulladdress' column.
    Returns:
        pd.Series: Series with processed 'fulladdress' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_city(s: pd.Series) -> pd.Series:
    """Process the 'city' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'city' column.
    Returns:
        pd.Series: Series with processed 'city' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_postcode(s: pd.Series) -> pd.Series:
    """Process the 'postcode' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'postcode' column.
    Returns:
        pd.Series: Series with processed 'postcode' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_registerdate(s: pd.Series) -> pd.Series:
    """Process the 'registerdate' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'registerdate' column.
    Returns:
        pd.Series: Series with processed 'registerdate' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = pd.to_datetime(s, errors="coerce", dayfirst=True)

    print(f"- processed dtype: {s.dtype}")

    return s


def process_removeddate(s: pd.Series) -> pd.Series:
    """Process the 'removeddate' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'removeddate' column.
    Returns:
        pd.Series: Series with processed 'removeddate' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = pd.to_datetime(s, errors="coerce", dayfirst=True)

    print(f"- processed dtype: {s.dtype}")

    return s


def process_latitude(s: pd.Series) -> pd.Series:
    """Process the 'latitude' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'latitude' column.
    Returns:
        pd.Series: Series with processed 'latitude' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_longitude(s: pd.Series) -> pd.Series:
    """Process the 'longitude' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'longitude' column.
    Returns:
        pd.Series: Series with processed 'longitude' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_nuts_id(s: pd.Series) -> pd.Series:
    """Process the 'nuts_id' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'nuts_id' column.
    Returns:
        pd.Series: Series with processed 'nuts_id' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


def process_nuts_name(s: pd.Series) -> pd.Series:
    """Process the 'nuts_name' column: replace newline characters with spaces.
    Args:
        s (pd.Series): Input pandas Series for the 'nuts_name' column.
    Returns:
        pd.Series: Series with processed 'nuts_name' column.
    """
    null_count = s.isna().sum()
    print(f"- null values: {null_count}")

    s = s.astype("string")

    print(f"- processed dtype: {s.dtype}")

    return s


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python prepare_parquet.py <input.csv|input.parquet> <output.parquet>")
        sys.exit(1)

    input_fpath = Path(sys.argv[1])
    output_fpath = Path(sys.argv[2])

    # Sanity checks
    # -------------
    # - input file exists
    if not input_fpath.exists():
        print(f"Error: Input file does not exist: {input_fpath}")
        sys.exit(1)

    # - input file has a valid extension
    if input_fpath.suffix.lower() not in {".csv", ".parquet"}:
        print(f"Error: Unsupported input extension '{input_fpath.suffix}'. Use .csv or .parquet.")
        sys.exit(1)

    # - output file has a .parquet extension
    if output_fpath.suffix.lower() != ".parquet":
        print(f"Error: Output file must have .parquet extension: {output_fpath}")
        sys.exit(1)

    # - input and output files are not the same
    if input_fpath.resolve() == output_fpath.resolve():
        print("Error: Input and output files must be different.")
        sys.exit(1)

    try:
        prepare_parquet(input_fpath, output_fpath)
    except Exception as e:
        print(f"Error while processing: {e}")
        sys.exit(1)
