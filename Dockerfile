FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STRATEGY_VALIDATOR_MODE=PRODUCTION \
    STRATEGY_VALIDATOR_LEDGER_DB_PATH=/var/lib/strategy-validator/ledger.sqlite3 \
    STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR=/var/backups/strategy-validator \
    STRATEGY_VALIDATOR_ARTIFACT_ROOT=/var/lib/strategy-validator/artifacts

WORKDIR /app

RUN addgroup --system strategy-validator \
    && adduser --system --ingroup strategy-validator strategy-validator \
    && mkdir -p /app/docs /var/lib/strategy-validator /var/lib/strategy-validator/artifacts /var/backups/strategy-validator \
    && chown -R strategy-validator:strategy-validator /app /var/lib/strategy-validator /var/backups/strategy-validator

COPY pyproject.toml ./pyproject.toml
COPY strategy_validator ./strategy_validator
COPY docs/ARCHITECTURE_ROADMAP.md ./docs/ARCHITECTURE_ROADMAP.md

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

USER strategy-validator
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3).read()" || exit 1

CMD ["sh", "-c", "strategy-validator-migrate && exec strategy-validator-api --host 0.0.0.0 --port 8000"]
