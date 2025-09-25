#!/bin/bash
DATASET_DIR=data/processed

pushd "$DATASET_DIR" > /dev/null
    # merges the split zip files into one file
    zip -FF dataset.zip --out dataset-merged.zip
    unzip dataset-merged.zip
    rm dataset-merged.zip
popd > /dev/null

test -f "$DATASET_DIR/dataset.parquet" || (
    echo "Could not extract dataset.parquet"
    exit 1
)
