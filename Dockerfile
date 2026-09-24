FROM python:3.12-slim

# Build/runtime deps: FreeTDS for pymssql, plus exiftool & qpdf for PDF payloads
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc freetds-dev freetds-bin \
        libimage-exiftool-perl qpdf \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/  ./app/
COPY tools/ ./tools/

# Vulnerable/fixed toggle (default: vulnerable)
ENV VULNERABLE=true

EXPOSE 5000

CMD ["python", "app/app.py"]
