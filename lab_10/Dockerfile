FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir pymongo

COPY lab10.1/bank_transfer.py /app/bank_transfer.py
COPY lab10.2/inventory_reservation.py /app/inventory_reservation.py
COPY lab10.2/lab10_2_results.csv /app/lab10_2_results.csv

CMD ["python", "bank_transfer.py"]