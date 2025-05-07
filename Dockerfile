# syntax=docker/dockerfile:1.4
FROM python:3.11-slim AS runtime

# Prevents Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Keeps Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Create a non-privileged user
ARG UID=1000
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/appuser" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# Install system dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
    apt-get -y install --no-install-recommends \
    build-essential \
    python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch to non-privileged user
USER appuser
RUN mkdir -p /home/appuser/.cache
RUN chown -R appuser:appuser /home/appuser
WORKDIR /home/appuser

# Install uv using pip and ensure it's available
RUN pip install uv
ENV PATH="/home/appuser/.local/bin:$PATH"

# Create virtual environment with uv
RUN uv venv
# Ensure the virtual environment is used
ENV PATH="/home/appuser/.venv/bin:$PATH"

# Copy dependency files to leverage Docker cache
COPY --chown=appuser:appuser pyproject.toml ./

# Create an empty uv.lock file if it doesn't exist
COPY --chown=appuser:appuser uv.lock ./uv.lock

# Install dependencies using uv sync
RUN uv sync

# Copy the application code
COPY --chown=appuser:appuser main.py .
COPY --chown=appuser:appuser .env .

# Command to run the application
CMD ["python", "main.py"]
