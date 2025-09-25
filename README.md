# Procurement Dashboard

## Setup

This project uses Python 3.12 or newer and manages dependencies with PDM. If not already done, install PDM following the instructions at [PDM Installation](https://pdm-project.org/en/latest/).

Install project dependencies with `pdm install`. If needed, install the development dependencies with `pdm install -G dev`. Force PDM to resolve and lock the dev dependencies `pdm lock -G dev`. Check the setup is correct with `pdm info`. Get a list of the declared packages `pdm list --graph`

Add a package with `pdm add <package_name>`, remove a package with `pdm remove <package_name>`. Add a package as a development dependency with
`pdm add -G dev <package_name>`.

Run code
```bash
pdm run python <file.py>
```

Run fomatting or linting
```bash
pdm run format
pdm run lint
```

Linting for just one file
```bash
pdm run ruff check <file.py>
```

Run the streamlit app
```bash
pdm run streamlit run src/gui/app.py
```

For a local run the prepared dataset has to be available in `data/processed/dataset.parquet`. If not already done, run the data processing script
```bash
pdm run python src/processing/prepare_parquet.py data/raw/final_procurement_dataset.csv data/processed/dataset.parquet
```

This expects the raw dataset to be available in `data/raw/final_procurement_dataset.csv`. 
