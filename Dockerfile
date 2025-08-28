
# Use Debian as a base image
FROM debian:bookworm-slim

# Install system dependencies and mise
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install mise
RUN curl https://mise.run | bash
ENV PATH="/root/.local/share/mise/shims:/root/.local/share/mise/bin:$PATH"

# Set work directory
WORKDIR /app

# Copy tool versions and install tools
COPY .tool-versions /app/.tool-versions
RUN mise install

# Copy project files
COPY bunny.py /app/bunny.py
COPY bunny.html /app/bunny.html
COPY pyproject.toml /app/pyproject.toml

# Install dependencies with uv
RUN uv pip install --system --no-cache-dir .

# Expose port for FastAPI
EXPOSE 8000

# Start the FastAPI server
CMD ["uvicorn", "bunny:app", "--host", "0.0.0.0", "--port", "8000"]
