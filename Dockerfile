FROM python:3.11-slim

WORKDIR /app

# Install build essentials if needed for packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY freegpt/ ./freegpt/

RUN pip install --no-cache-dir .

EXPOSE 8080

ENTRYPOINT ["freegpt"]
CMD ["--host", "0.0.0.0", "--port", "8080"]
