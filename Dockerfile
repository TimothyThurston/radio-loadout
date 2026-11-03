# syntax=docker/dockerfile:1
# Supported security-maintained Python; pin the multi-platform base manifest.
ARG PYTHON_IMAGE=python:3.13.15-slim-bookworm@sha256:2325bb286ec344af3e5898cc224b5844e2707ac6e26b1632516fd3edc84a5e26
FROM ${PYTHON_IMAGE} AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 SOURCE_DATE_EPOCH=1704067200
WORKDIR /build
COPY deploy/requirements-build.lock deploy/requirements-runtime.lock /build/
RUN python -m pip install --require-hashes --only-binary=:all: -r requirements-build.lock
COPY pyproject.toml README.md LICENSE COPYRIGHT /build/
COPY src/ /build/src/
RUN python -m build --wheel --no-isolation --outdir /wheels \
    && python -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --require-hashes --only-binary=:all: --no-compile -r requirements-runtime.lock \
    && /opt/venv/bin/python -m pip install --no-deps --no-compile /wheels/radio_loadout-*.whl \
    && /opt/venv/bin/python -m pip check

FROM ${PYTHON_IMAGE} AS runtime
ENV PATH="/opt/venv/bin:$PATH" TMPDIR=/tmp HOST=0.0.0.0 PORT=8000
RUN groupadd --gid 10001 radio && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin radio
COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-I", "-B", "-c", "import os,urllib.request; urllib.request.build_opener(urllib.request.ProxyHandler({})).open('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/healthz',timeout=2).close()"]
CMD ["python", "-I", "-B", "-u", "-m", "radio_loadout.web.serve"]
