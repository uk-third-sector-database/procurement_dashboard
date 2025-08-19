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
