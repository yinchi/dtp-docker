FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install third-party packages only
# Note we need to mount ALL pyproject.toml files in the workspace and {README.md, __init__.py} of
# dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=infra/auth/pyproject.toml,target=infra/auth/pyproject.toml \
    --mount=type=bind,source=infra/api/pyproject.toml,target=infra/api/pyproject.toml \
    uv sync --package dtp-docker-api --locked --no-install-project --no-dev

# Copy in the lockfile, main pyproject.toml, and the current project
# Also copy all dependencies
COPY ./uv.lock ./pyproject.toml /app/
COPY ./infra/api/ /app/infra/api/

# Sync a second time with the actual code loaded
# Mount all pyproject.toml files in the workspace, except the ones we copied
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=infra/auth/pyproject.toml,target=infra/auth/pyproject.toml \
    uv sync --package dtp-docker-api --locked --no-dev


# Then, use a final image without uv
FROM python:3.14-slim-trixie

RUN apt-get update && apt-get install -y wget libpq-dev && rm -rf /var/lib/apt/lists/*

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
 && useradd --system --gid 999 --uid 999 --create-home nonroot

COPY --from=builder --chown=nonroot:nonroot /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER nonroot
WORKDIR /app

EXPOSE 8000

# Run the FastAPI application by default
CMD ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000", "-e", "dtp.api:app"]
