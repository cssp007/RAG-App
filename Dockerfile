FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OLLAMA_HOST=0.0.0.0:11434 \
    OLLAMA_MODEL=llama3.2

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        procps \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 5000
EXPOSE 11434

CMD ["sh", "-c", "ollama serve > /tmp/ollama.log 2>&1 & sleep 5 && ollama pull llama3.2 && python app.py"]