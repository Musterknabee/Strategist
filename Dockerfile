FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY strategy_validator ./strategy_validator

RUN pip install --upgrade pip && pip install .[production]

EXPOSE 8000

CMD ["strategy-validator-api", "--host", "0.0.0.0", "--port", "8000"]
