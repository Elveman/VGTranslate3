FROM python:3.11-slim AS base

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        libtesseract-dev \
        libleptonica-dev \
        gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./src ./src
COPY ./config_example ./config_example
COPY ./README.md .
RUN pip install --no-cache-dir .

# -------- запуск -------------------------------------------------------------
ENV PYTHONUNBUFFERED=1 \
    VGTRANSLATE3_PORT=4404

EXPOSE 4404

ENTRYPOINT ["python", "-m", "vgtranslate3.serve"]
