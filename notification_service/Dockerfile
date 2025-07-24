FROM python:3.12-slim

RUN apt-get update && apt-get clean

ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

COPY ./pyproject.toml ./uv.lock /app/

RUN uv sync --frozen

COPY ./app /app/app
COPY ./scripts /app/scripts

ENTRYPOINT ["/bin/bash", "-c"]
CMD ["/app/scripts/wait-for-kafka.sh kafka 9092 && python -m app.main"]
