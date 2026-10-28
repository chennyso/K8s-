ARG BASE_IMAGE=python:3.13-slim-bookworm
FROM ${BASE_IMAGE}
ARG APP_VERSION
LABEL org.opencontainers.image.revision=${APP_VERSION}
ENV APP_VERSION=${APP_VERSION} PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN test -n "$APP_VERSION" && pip install --no-cache-dir --disable-pip-version-check -r requirements.txt && mkdir /app/test-results && chown 1000:1000 /app/test-results
COPY app.py index.html ./
COPY ci/ ./ci/
USER 1000:1000
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
