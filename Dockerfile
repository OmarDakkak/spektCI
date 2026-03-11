FROM python:3.11-alpine AS builder

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir build && \
    python -m build --wheel && \
    pip install --no-cache-dir dist/*.whl

# ── Runtime ──────────────────────────────────────────────────────
FROM python:3.11-alpine

RUN adduser -D spektci
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/spektci /usr/local/bin/spektci

USER spektci
ENTRYPOINT ["spektci"]
CMD ["--help"]
