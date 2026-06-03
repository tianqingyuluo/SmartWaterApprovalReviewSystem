FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_LINK_MODE=copy \
    SOFFICE_PATH=/usr/bin/soffice

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        fonts-noto-cjk \
        libreoffice-core \
        libreoffice-writer \
        libreoffice-java-common \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY python-services/smart-water-approval-review-system-py/pyproject.toml \
     python-services/smart-water-approval-review-system-py/uv.lock \
     python-services/smart-water-approval-review-system-py/README.md ./
RUN uv sync --frozen --no-dev

COPY python-services/smart-water-approval-review-system-py/main.py ./
COPY python-services/smart-water-approval-review-system-py/src src
COPY python-services/smart-water-approval-review-system-py/knowledge_pack knowledge_pack

RUN mkdir -p /app/data/chroma /app/knowledge_source \
    && useradd --system --create-home --home-dir /home/smartwater smartwater \
    && chown -R smartwater:smartwater /app /home/smartwater

USER smartwater
EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
