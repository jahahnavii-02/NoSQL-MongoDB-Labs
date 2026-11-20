from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time


# ==========================================
# MongoDB connection
# ==========================================

client = MongoClient(
    "mongodb://localhost:27017/",
    serverSelectionTimeoutMS=5000
)

db = client["cti_platform"]

threats = db["threats"]


# ==========================================
# Configuration
# ==========================================

CHECK_INTERVAL = 10
RUNS = 6

CTI_URL = "https://ctidigest.com/"


# ==========================================
# Get latest threat stored in MongoDB
# ==========================================

def get_latest_db_threat():

    return threats.find_one(
        {},
        sort=[
            ("publishedDate", -1)
        ]
    )


# ==========================================
# Check CTI Digest for newer reports
# ==========================================

def check_new_reports():

    try:

        response = requests.get(
            CTI_URL,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        links = []

        for link in soup.find_all("a", href=True):

            title = link.get_text(
                " ",
                strip=True
            )

            url = link["href"]

            if title:
                links.append(
                    (title, url)
                )

        return links[:10]

    except Exception as e:

        print(
            "Web check failed:",
            str(e)
        )

        return []


# ==========================================
# WiredTiger cache statistics
# ==========================================

def get_cache_stats():

    status = db.command(
        "serverStatus"
    )

    cache = status[
        "wiredTiger"
    ][
        "cache"
    ]

    maximum = cache[
        "maximum bytes configured"
    ]

    current = cache[
        "bytes currently in the cache"
    ]

    utilization = (
        current / maximum
    ) * 100

    return {
        "maximum": maximum,
        "current": current,
        "utilization": utilization,
        "pages_read": cache[
            "pages read into cache"
        ],
        "pages_written": cache[
            "pages written from cache"
        ]
    }


# ==========================================
# Display monitoring information
# ==========================================

def display_status(run_number):

    print("\n")
    print("=" * 60)
    print(
        f"MONITORING CHECK {run_number}/{RUNS}"
    )
    print(
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )
    print("=" * 60)


    # --------------------------------------
    # Latest database threat
    # --------------------------------------

    latest = get_latest_db_threat()

    print("\nDATABASE STATUS")

    if latest:

        print(
            "Latest threat:",
            latest.get(
                "title",
                "Unknown"
            )
        )

        print(
            "Published:",
            latest.get(
                "publishedDate",
                "Unknown"
            )
        )

    else:

        print(
            "No threats found."
        )


    # --------------------------------------
    # Web check
    # --------------------------------------

    print("\nCTI DIGEST CHECK")

    reports = check_new_reports()

    if reports:

        print(
            f"Reports/pages discovered: "
            f"{len(reports)}"
        )

        for title, url in reports[:5]:

            print(
                "-",
                title
            )

    else:

        print(
            "No new reports detected "
            "or website could not be read."
        )


    # --------------------------------------
    # Cache
    # --------------------------------------

    cache = get_cache_stats()

    print("\nWIREDTIGER CACHE")

    print(
        "Maximum cache:",
        f"{cache['maximum']:,}",
        "bytes"
    )

    print(
        "Current cache:",
        f"{cache['current']:,}",
        "bytes"
    )

    print(
        "Cache utilization:",
        f"{cache['utilization']:.2f}%"
    )

    print(
        "Pages read:",
        f"{cache['pages_read']:,}"
    )

    print(
        "Pages written:",
        f"{cache['pages_written']:,}"
    )


# ==========================================
# Main monitoring loop
# ==========================================

print("=" * 60)
print("LAB 7.2 MONITOR")
print("=" * 60)

print(
    f"Monitoring interval: "
    f"{CHECK_INTERVAL} seconds"
)

print(
    f"Number of checks: {RUNS}"
)

print(
    "Press Ctrl+C to stop early."
)


for run in range(1, RUNS + 1):

    display_status(run)

    if run < RUNS:

        print(
            f"\nWaiting {CHECK_INTERVAL} seconds..."
        )

        time.sleep(
            CHECK_INTERVAL
        )


print("\n")
print("=" * 60)
print("MONITORING COMPLETED")
print("=" * 60)