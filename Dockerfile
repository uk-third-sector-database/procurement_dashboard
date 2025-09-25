# build stage
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PDM_USE_VENV=true \
    PDM_VENV_IN_PROJECT=true

WORKDIR /app

RUN python -m pip install --no-cache-dir pdm
COPY README.md pyproject.toml pdm.lock* /app/
RUN pdm sync --prod --no-editable

COPY . /app


# runtime stage
FROM python:3.12-slim AS runtime

# Same Python quality-of-life flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Put the PDM-created venv on PATH
    PATH="/app/.venv/bin:${PATH}" \
    PYTHONPATH="/app/src"

WORKDIR /app

# Copy app code and the populated .venv from the builder stage
COPY --from=builder /app /app

# Streamlit default port
EXPOSE 8501

# Run the Streamlit app. Change app.py if your entry point is different.
CMD ["streamlit", "run", "src/gui/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
