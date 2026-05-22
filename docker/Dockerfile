FROM python:3.12-slim

WORKDIR /app

# Install system deps (gh CLI, git)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update && apt-get install -y --no-install-recommends gh && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ /app/src/
COPY config/ /app/config/
COPY ui/ /app/ui/
COPY bin/ /app/bin/

ENV PYTHONPATH=/app/src
ENV AXENG_HOME=/app

EXPOSE 3457

# Start the API server
CMD ["uvicorn", "ui.nextjs.api_server:app", "--host", "0.0.0.0", "--port", "3457"]
