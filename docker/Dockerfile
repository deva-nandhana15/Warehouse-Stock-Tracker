# Build from repo root:  docker build -f docker/Dockerfile -t warehouse-stock-tracker:dev .
# Official Docker registry manifest digest verified 2026-10-26.
FROM python:3.12-slim@sha256:a0f57064cbdcd6285fa45f51237ab0b35ea8ebaed06a1f5973e89e19dfb86704

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dedicated unprivileged user (fixed UID so Azure/Kubernetes can verify non-root).
RUN groupadd --system --gid 10001 app \
 && useradd  --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

# Dependencies first for better layer caching.
COPY app/requirements.txt .
RUN pip install -r requirements.txt

COPY app/app.py .
COPY app/inventory_store.py .
COPY app/templates ./templates
COPY app/static ./static

USER 10001:10001

# Overridable at run time. Never put secrets in ENV/ARG.
ENV PORT=5000 \
    APP_VERSION=dev

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import os,urllib.request as u; u.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT','5000'), timeout=3)"]

# ONE worker + threads: inventory is in-memory, so multiple worker processes
# would each hold different data. Logs go to stdout/stderr for Docker/Jenkins.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --access-logfile - --error-logfile - 'app:create_app()'"]
