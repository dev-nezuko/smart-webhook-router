FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/opt/venv/bin:/root/.local/bin:$PATH"

COPY pyproject.toml README.md /app/
RUN uv sync --no-dev --no-install-project

COPY . /app

RUN chmod +x /app/scripts/start-web.sh /app/scripts/start-worker.sh

EXPOSE 8000

CMD ["/app/scripts/start-web.sh"]
