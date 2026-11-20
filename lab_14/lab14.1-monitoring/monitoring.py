import os
import time
import json
import argparse
from datetime import datetime, timezone
from getpass import getpass

import requests
from pymongo import MongoClient
from pymongo.errors import PyMongoError


INTERVAL = 30
CACHE_THRESHOLD = 0.80
LAG_THRESHOLD = 10


def send_webhook(url, message):
    if not url:
        return

    # Slack and Discord both accept a content-like
    # notification, but use different field names.
    payload = (
        {"content": message}
        if "discord.com" in url
        else {"text": message}
    )

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("Webhook notification sent.")
    except requests.RequestException as error:
        print(f"Webhook delivery failed: {error}")


def monitor(client, logfile, webhook_url):
    previous_reads = None
    previous_operations = None

    while True:
        try:
            status = client.admin.command("serverStatus")
            replica = client.admin.command("replSetGetStatus")

            connections = status.get("connections", {})
            counters = status.get("opcounters", {})
            cache = status.get("wiredTiger", {}).get("cache", {})

            used = cache.get("bytes currently in the cache", 0)
            maximum = cache.get("maximum bytes configured", 0)
            cache_usage = (
                used / maximum * 100 if maximum else 0
            )

            # Page reads are not the same as cache misses.
            # Report them separately rather than claiming
            # an exact cache hit ratio.
            page_reads = cache.get("pages read into cache", 0)
            pages_requested = cache.get("pages requested from the cache", 0)

            cache_hit_ratio = (
                (pages_requested - page_reads) / pages_requested
                if pages_requested > 0 else None
            )

            members = replica.get("members", [])
            primary = next(
                (m for m in members if m.get("stateStr") == "PRIMARY"),
                None
            )

            lags = {}
            if primary:
                primary_time = primary.get("optimeDate")
                for member in members:
                    if member.get("stateStr") == "SECONDARY":
                        secondary_time = member.get("optimeDate")
                        if primary_time and secondary_time:
                            lag = max(
                                0,
                                (primary_time - secondary_time).total_seconds()
                            )
                            lags[member["name"]] = lag

            timestamp = datetime.now(timezone.utc).isoformat()

            rows = [
                ("Timestamp", timestamp),
                ("Connections", connections.get("current", 0)),
                ("Active connections", connections.get("active", 0)),
                ("Inserts", counters.get("insert", 0)),
                ("Queries", counters.get("query", 0)),
                ("Updates", counters.get("update", 0)),
                ("Deletes", counters.get("delete", 0)),
                ("Commands", counters.get("command", 0)),
                ("Cache usage (%)", f"{cache_usage:.2f}"),
                ("Pages read into cache", page_reads),
                ("Pages requested from cache", pages_requested),
                ("Cache hit ratio (%)",
                    f"{cache_hit_ratio * 100:.2f}"
                    if cache_hit_ratio is not None else "Unavailable"),
                ("Replica members", len(members)),
            ]

            for name, lag in lags.items():
                rows.append((f"Lag {name} (s)", lag))

            output = "\n".join(
                f"{str(key):<30} | {value}"
                for key, value in rows
            )

            alerts = []

            for name, lag in lags.items():
                if lag > LAG_THRESHOLD:
                    alerts.append(
                        f"WARNING: Replication lag on {name} "
                        f"is {lag:.1f}s (>10s)"
                    )

            # Cache hit ratio requires a valid hit/miss
            # measurement. It is not inferred from
            # cache occupancy or cumulative page reads.

            if cache_hit_ratio is not None and cache_hit_ratio < CACHE_THRESHOLD:
                alerts.append(
                    f"WARNING: Cache hit ratio is "
                    f"{cache_hit_ratio * 100:.2f}% (below 80%)"
                )

            if cache_hit_ratio is None:
                alerts.append(
                    "WARNING: Cache hit ratio unavailable; page counters are zero"
                )

            if not maximum:
                alerts.append(
                    "WARNING: WiredTiger cache capacity unavailable"
                )

            if alerts:
                output += "\n" + "\n".join(alerts)
                for alert in alerts:
                    send_webhook(webhook_url, alert)

            print("\n" + output + "\n", flush=True)

            with open(logfile, "a", encoding="utf-8") as file:
                file.write(output + "\n" + "-" * 55 + "\n")

        except PyMongoError as error:
            print(f"MongoDB monitoring error: {error}", flush=True)

        time.sleep(INTERVAL)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log", default="metrics.log"
    )
    args = parser.parse_args()

    username = os.getenv("MONGODB_MONITOR_USER", "ctiAdmin")
    password = os.getenv("MONGODB_MONITOR_PASSWORD")

    if not password:
        password = getpass("Enter MongoDB monitoring password: ")

    webhook = os.getenv("MONITOR_WEBHOOK_URL", "")

    client = MongoClient(
        "mongodb://localhost:27130/",
        username=username,
        password=password,
        authSource="admin",
        
        directConnection=True,
        serverSelectionTimeoutMS=10000
    )

    try:
        client.admin.command("ping")
        print("Connected to MongoDB replica set.")
        monitor(client, args.log, webhook)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    finally:
        client.close()


if __name__ == "__main__":
    main()

