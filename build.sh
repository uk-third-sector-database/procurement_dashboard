#!/bin/sh
set -eou pipefail
./extract_dataset.sh
docker build -t uk-third-sector-procurement-dashboard .
