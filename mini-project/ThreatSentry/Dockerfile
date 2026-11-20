# Python base image avoids installing Python through Ubuntu apt repositories
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV SCANNER_MODE=local

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY backend ./backend
COPY ingestion ./ingestion

EXPOSE 8000

# Health check using Python instead of curl
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health', timeout=5)" || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]