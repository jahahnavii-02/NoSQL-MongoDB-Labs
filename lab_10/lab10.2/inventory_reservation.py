import os
import time
import csv
import threading
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

from pymongo import MongoClient, ReturnDocument
from pymongo.errors import PyMongoError

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://mongo-primary:27017,"
    "mongo-secondary1:27017,"
    "mongo-secondary2:27017/?replicaSet=rs0"
)

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
db = client["ecommerce"]
inventory = db["inventory"]
orders = db["orders"]

MAX_RETRIES = 5
BASE_DELAY = 0.05
PRODUCT_ID = "PROD-001"


def initialize_inventory(stock):
    """Reset the test product and order collection."""
    inventory.delete_many({})
    orders.delete_many({})

    inventory.insert_one({
        "product_id": PRODUCT_ID,
        "name": "Test Product",
        "stock": stock,
        "version": 0,
        "price": 100.0
    })


def reserve_inventory(order_id, customer_id, qty=1):
    """Reserve stock and create the order atomically."""
    for attempt in range(MAX_RETRIES):
        try:
            with client.start_session() as session:
                with session.start_transaction():
                    product = inventory.find_one(
                        {"product_id": PRODUCT_ID},
                        session=session
                    )

                    if product is None:
                        return False

                    if product["stock"] < qty:
                        return False

                    result = inventory.update_one(
                        {
                            "product_id": PRODUCT_ID,
                            "stock": {"$gte": qty},
                            "version": product["version"]
                        },
                        {
                            "$inc": {
                                "stock": -qty,
                                "version": 1
                            }
                        },
                        session=session
                    )

                    if result.modified_count != 1:
                        raise RuntimeError(
                            "Inventory changed during reservation."
                        )

                    orders.insert_one({
                        "order_id": order_id,
                        "customer_id": customer_id,
                        "items": [{
                            "product_id": PRODUCT_ID,
                            "qty": qty,
                            "price": product["price"]
                        }],
                        "status": "pending",
                        "total": qty * product["price"],
                        "created_at": datetime.now(timezone.utc)
                    }, session=session)

            return True

        except PyMongoError as exc:
            if (
                exc.has_error_label("TransientTransactionError")
                and attempt < MAX_RETRIES - 1
            ):
                delay = BASE_DELAY * (2 ** attempt)
                time.sleep(delay)
                continue

            print(f"Reservation {order_id} failed: {exc}")
            return False

        except RuntimeError:
            if attempt < MAX_RETRIES - 1:
                time.sleep(BASE_DELAY * (2 ** attempt))
                continue
            return False

    return False


def run_contention_test():
    """Eight requests compete for five available units."""
    print("\n--- CONTENTION TEST: 8 requests, stock = 5 ---")
    initialize_inventory(5)

    successes = 0
    failures = 0

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(
                reserve_inventory,
                f"CONT-{i:03d}",
                f"CUST-{i:03d}",
                1
            )
            for i in range(8)
        ]

        for future in as_completed(futures):
            if future.result():
                successes += 1
            else:
                failures += 1

    remaining = inventory.find_one(
        {"product_id": PRODUCT_ID}
    )["stock"]

    order_count = orders.count_documents({})

    print("Successful reservations:", successes)
    print("Rejected reservations:", failures)
    print("Remaining stock:", remaining)
    print("Orders created:", order_count)

    assert successes == 5, "Expected exactly five successful reservations."
    assert remaining == 0, "Expected inventory stock to reach zero."
    assert order_count == 5, "Expected exactly five orders."

    print("Contention test passed.")


def run_throughput_test(workers, transactional=True):
    """Measure reservations per second under different concurrency levels."""
    print(
        f"\nTesting workers={workers}, "
        f"transactional={transactional}"
    )

    # Use ample stock so inventory exhaustion does not dominate the test.
    initialize_inventory(1000)
    total_requests = 200
    successes = 0

    def non_transactional_reservation(order_id, customer_id):
        """
        Demonstration baseline: stock decrement and order insert
        are separate operations, so failures can leave inconsistencies.
        """
        product = inventory.find_one_and_update(
            {
                "product_id": PRODUCT_ID,
                "stock": {"$gte": 1}
            },
            {
                "$inc": {"stock": -1, "version": 1}
            },
            return_document=ReturnDocument.BEFORE
        )

        if product is None:
            return False

        orders.insert_one({
            "order_id": order_id,
            "customer_id": customer_id,
            "items": [{
                "product_id": PRODUCT_ID,
                "qty": 1,
                "price": product["price"]
            }],
            "status": "pending",
            "total": product["price"],
            "created_at": datetime.now(timezone.utc)
        })

        return True

    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []

        for i in range(total_requests):
            order_id = f"{'TX' if transactional else 'NT'}-{workers}-{i}"
            customer_id = f"CUST-{i}"

            if transactional:
                future = executor.submit(
                    reserve_inventory,
                    order_id,
                    customer_id,
                    1
                )
            else:
                future = executor.submit(
                    non_transactional_reservation,
                    order_id,
                    customer_id
                )

            futures.append(future)

        for future in as_completed(futures):
            if future.result():
                successes += 1

    elapsed = time.perf_counter() - start
    throughput = successes / elapsed if elapsed else 0.0

    result = {
        "mode": "transactional" if transactional else "non_transactional",
        "workers": workers,
        "requests": total_requests,
        "successes": successes,
        "elapsed_seconds": round(elapsed, 4),
        "throughput_per_second": round(throughput, 2)
    }

    print(result)
    return result


def main():
    try:
        client.admin.command("ping")
        print("MongoDB connection successful.")

        # First verify correctness under contention.
        run_contention_test()

        # Then benchmark throughput using sufficient inventory.
        results = []

        for workers in (1, 4, 8, 16):
            results.append(
                run_throughput_test(workers, transactional=True)
            )

        for workers in (1, 4, 8, 16):
            results.append(
                run_throughput_test(workers, transactional=False)
            )

        with open(
            "lab10_2_results.csv",
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "mode",
                    "workers",
                    "requests",
                    "successes",
                    "elapsed_seconds",
                    "throughput_per_second"
                ]
            )
            writer.writeheader()
            writer.writerows(results)

        print("\n--- FINAL SUMMARY ---")
        print("Benchmark rows:", len(results))
        print("CSV saved as lab10_2_results.csv")
        print(
            "Contention and throughput measurements completed. "
            "Use the measured output for your report."
        )

    finally:
        client.close()


if __name__ == "__main__":
    main()