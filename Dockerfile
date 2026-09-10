# Multi-stage Dockerfile for EraLang 2.1
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies (build-essential for C transpiler gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    make \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project specification
COPY pyproject.toml setup.py README.md LICENSE ./
COPY eralang ./eralang
COPY examples ./examples
COPY benchmarks ./benchmarks
COPY tests ./tests
COPY web ./web
COPY era.py ./

# Install EraLang toolchain in editable mode
RUN pip install --no-cache-dir -e .

EXPOSE 8000

# Default entrypoint runs era CLI
ENTRYPOINT ["era"]
CMD ["info"]
