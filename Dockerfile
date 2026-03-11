FROM python:3.13-slim-bookworm AS builder

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir build && \
    python -m build --wheel && \
    pip install --no-cache-dir dist/*.whl

# ── Runtime ──────────────────────────────────────────────────────
FROM python:3.13-slim-bookworm

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

LABEL org.opencontainers.image.title="spektci" \
      org.opencontainers.image.description="Multi-platform CI/CD compliance scanner" \
      org.opencontainers.image.url="https://github.com/OmarDakkak/spektCI" \
      org.opencontainers.image.source="https://github.com/OmarDakkak/spektCI" \
      org.opencontainers.image.licenses="MIT"

RUN useradd --create-home spektci
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin/spektci /usr/local/bin/spektci

USER spektci
HEALTHCHECK --interval=60s --timeout=3s CMD ["spektci", "--version"]
ENTRYPOINT ["spektci"]
CMD ["--help"]
