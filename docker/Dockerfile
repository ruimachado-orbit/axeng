FROM python:3.12-slim

WORKDIR /app

# ── System deps ────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gh \
    git \
    && rm -rf /var/lib/apt/lists/*

# ── Python deps ────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Streamlit for the web UI
RUN pip install --no-cache-dir streamlit

# ── Axeng source ───────────────────────────────────────────────
COPY src/ ./src/
COPY config/ ./config/
COPY ui/ ./ui/
COPY bin/ ./bin/

# ── Set up Hermes directory for Google API ────────────────────
RUN mkdir -p /root/.hermes/skills/productivity/google-workspace/scripts && \
    mkdir -p /root/.hermes/secrets

# Copy Google API script to Hermes directory
COPY src/tools/google_api.py /root/.hermes/skills/productivity/google-workspace/scripts/google_api.py
RUN chmod +x /root/.hermes/skills/productivity/google-workspace/scripts/google_api.py

# ── Entry point ───────────────────────────────────────────────
ENV PYTHONPATH=/app/src
ENV PATH="/app:${PATH}"

CMD ["streamlit", "run", "ui/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]