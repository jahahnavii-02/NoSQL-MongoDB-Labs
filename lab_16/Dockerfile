FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --default-timeout=180 --retries=10 -r requirements.txt

COPY service ./service

EXPOSE 8016

CMD ["uvicorn", "service.api:app", "--host", "0.0.0.0", "--port", "8016"]
