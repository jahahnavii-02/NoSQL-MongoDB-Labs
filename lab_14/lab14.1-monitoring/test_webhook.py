import requests

webhook_url = "http://127.0.0.1:8000"

test_alerts = [
    {
        "alert": "LOW CACHE HIT RATIO",
        "cache_hit_ratio": 75,
        "threshold": 80,
        "message": "Cache hit ratio is below 80%"
    },
    {
        "alert": "HIGH REPLICATION LAG",
        "replication_lag_seconds": 11,
        "threshold": 10,
        "message": "Replication lag exceeds 10 seconds"
    }
]

for alert in test_alerts:
    response = requests.post(webhook_url, json=alert, timeout=5)
    print(alert["alert"], "-> HTTP", response.status_code)
