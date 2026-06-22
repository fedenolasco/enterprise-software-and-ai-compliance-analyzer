FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy the backend project
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Copy agent-brain and mock-pricing-api source for imports
COPY ../../agent-brain/src/ /app/agent-brain/src/
COPY ../../agent-brain/pyproject.toml /app/agent-brain/
COPY ../../mock-pricing-api/src/ /app/mock-pricing-api/src/
COPY ../../mock-pricing-api/pyproject.toml /app/mock-pricing-api/

# Install the UI API
RUN pip install --no-cache-dir -e ".[dev]"

# Install agent-brain as a path dependency
RUN pip install --no-cache-dir -e /app/agent-brain

EXPOSE 3001

CMD ["python", "-m", "ui_api.main"]
