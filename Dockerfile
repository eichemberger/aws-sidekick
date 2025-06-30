FROM node:22-alpine AS client-builder

RUN corepack enable pnpm

WORKDIR /app/client

COPY client/package.json client/pnpm-lock.yaml ./

RUN pnpm install --frozen-lockfile

COPY client/ ./

RUN pnpm run build

FROM python:3.12-alpine AS backend

RUN apk add --no-cache \
    curl \
    build-base

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock* ./

RUN uv pip install --system --no-cache-dir .

COPY src/ ./src/
COPY api.py ./
COPY main.py ./
COPY config/ ./config/

COPY --from=client-builder /app/client/dist ./client/dist

RUN mkdir -p ./data

EXPOSE 8000

ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV PYTHONPATH=/app/src
ENV UV_NO_SYNC=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["python", "api.py"] 