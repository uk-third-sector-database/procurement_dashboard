#!/usr/bin/env python3
"""
Converts the original CSV or Parquet file into a cleaned Parquet file for the streamlit app.

Usage:
    python prepare_parquet.py input.csv output.parquet
    python prepare_parquet.py input.parquet output.parquet
"""

import sys
from pathlib import Path

import polars as pl


def prepare_parquet(in_fpath: Path, out_fpath: Path):
    """Load data from CSV or Parquet, processes it and outputs processed Parquet.

    Args:
        in_fpath (Path): Path to the input CSV or Parquet file.
        out_fpath (Path): Path to the output Parquet file.
    """

    ext = in_fpath.suffix.lower()
    print(f"Reading {ext.upper()} file: {in_fpath}")

    if ext == ".csv":
        dset = pl.read_csv(
            in_fpath,
            try_parse_dates=True,
            infer_schema_length=1000,
            low_memory=True,
            schema_overrides={
                "contractsfinder_awardedtovcse": pl.Boolean
            },
        )
        fpath = in_fpath.with_suffix(".parquet")
        print(f"Writing Parquet (auto-named): {fpath}")
        dset.write_parquet(
            fpath,
            compression="zstd",
            use_pyarrow=True,
        )
    elif ext == ".parquet":
        dset = pl.read_parquet(in_fpath)
    else:
        raise ValueError(f"Unsupported input extension: {ext} (use .csv or .parquet)")

    print(f"Processing data from {in_fpath}...")

    # data source
    # -----------
    column_name = "data_source"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")
        to_replace = ["\n", " "]
        dset = dset.with_columns(pl.col(column_name).str.replace_all(to_replace[0], to_replace[1]))
        print("- replaced newline with space")

        to_replace = ["NHSSpend", "NHS Spend"]
        dset = dset.with_columns(pl.col(column_name).str.replace(to_replace[0], to_replace[1]))
        print(f"- replaced {to_replace[0]} with {to_replace[1]}")
        dset = dset.with_columns(pl.col(column_name).cast(pl.Categorical))
        print(
            f"- cast {column_name} to Categorical with "
            f"{len(dset[column_name].unique())} unique values: "
            f"{dset[column_name].unique().to_list()}"
        )
    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # department
    # ----------
    column_name = "dept"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")
        to_replace = ["\n", " "]
        dset = dset.with_columns(pl.col(column_name).str.replace_all(to_replace[0], to_replace[1]))
        print("- replaced newline with space")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # amount
    # ------
    column_name = "amount"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")
    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # supplier
    # ----------
    column_name = "supplier"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # normalized_supplier
    # -------------------
    column_name = "normalized_supplier"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # date_payment
    # ------------
    column_name = "date_payment"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    column_name = "contractsfinder_awardedtovcse"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # contractsfinder_region
    # ----------------------
    column_name = "contractsfinder_region"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # daterange_org_seen
    # ----------------------
    column_name = "daterange_org_seen"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # total_value_payments_to_org
    # ----------------------
    column_name = "total_value_payments_to_org"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # total_number_payments_to_org
    # ----------------------------
    column_name = "total_number_payments_to_org"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # orgflag
    # -------
    column_name = "orgflag"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # verifmatch
    # ----------
    column_name = "verifmatch"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # verifcode
    # ----------
    column_name = "verifcode"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # verifnote
    # ----------
    column_name = "verifnote"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # manual_match_to_spine
    # ---------------------
    column_name = "manual_match_to_spine"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")
        dset = dset.with_columns(
            pl.col(column_name).cast(pl.Int8).cast(pl.Boolean)
        )
        print("- cast to Boolean")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # other_exact_match
    # -----------------
    column_name = "other_exact_match"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")
        dset = dset.with_columns(
            pl.col(column_name).cast(pl.Int8).cast(pl.Boolean)
        )
        print("- cast to Boolean")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # isspine_manual
    # --------------
    column_name = "isspine_manual"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # isspine
    # -------
    column_name = "isspine"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # longmatch
    # ---------
    column_name = "longmatch"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # uid
    # ---
    column_name = "uid"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # organisationname
    # ----------------
    column_name = "organisationname"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # fulladdress
    # -----------
    column_name = "fulladdress"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # city
    # ----
    column_name = "city"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # postcode
    # --------
    column_name = "postcode"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # registerdate
    # -------------
    column_name = "registerdate"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # latitude
    # ---------
    column_name = "latitude"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # longitude
    # ---------
    column_name = "longitude"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # geometry
    # ---------
    column_name = "geometry"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # nuts_id_0
    # ---------
    column_name = "nuts_id_0"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # nuts_name_0
    # -----------
    column_name = "nuts_name_0"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # nuts_id_1
    # ---------
    column_name = "nuts_id_1"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # nuts_name_1
    # -----------
    column_name = "nuts_name_1"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # nuts_id_2
    # ---------
    column_name = "nuts_id_2"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # nuts_name_2
    # -----------
    column_name = "nuts_name_2"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # nuts_id_3
    # ---------
    column_name = "nuts_id_3"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    # nuts_name_3
    # -----------
    column_name = "nuts_name_3"
    try:
        print(f"Processing {column_name}: {dset[column_name].dtype}")
        null_count = dset[column_name].is_null().sum()
        print(f"- null values in {column_name}: {null_count}")

    except pl.exceptions.ColumnNotFoundError:
        print(f"Warning: '{column_name}' not in the dataset - skipping processing.")

    dset.write_parquet(
        out_fpath,
        compression="zstd",
        use_pyarrow=True,
    )
    print(f"Processed data written to: {out_fpath}")


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
