FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y curl supervisor && \
    apt-get upgrade -y && \
    apt-get clean

ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-install-project

COPY ./app /app/app
COPY ./scripts /app/scripts
COPY ./alembic.ini /app/
COPY ./alembic /app/alembic
COPY pytest.ini /app/

RUN uv sync

COPY ./scripts/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["bash", "-c", "/app/scripts/wait-for-service.sh elasticsearch 9200 && /app/scripts/wait-for-kafka.sh kafka 9092 && /app/scripts/initialize.sh && supervisord -c /etc/supervisor/conf.d/supervisord.conf"]


