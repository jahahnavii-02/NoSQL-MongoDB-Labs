import os
import time
from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.errors import PyMongoError


# MongoDB connection
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017/?directConnection=true"
)

DATABASE_NAME = "banking"
MAX_RETRIES = 5
BASE_DELAY = 0.1

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000
)

db = client[DATABASE_NAME]
accounts = db["accounts"]
history = db["transaction_history"]


class InsufficientFundsError(Exception):
    """Raised when the source account lacks sufficient funds."""
    pass


class AccountNotFoundError(Exception):
    """Raised when an account does not exist."""
    pass


def initialize_accounts():
    """Create two test accounts and clear previous lab history."""
    accounts.delete_many({})
    history.delete_many({})

    accounts.insert_many([
        {
            "account_id": "ACC-001",
            "balance": 500.0,
            "version": 0
        },
        {
            "account_id": "ACC-002",
            "balance": 200.0,
            "version": 0
        }
    ])

    print("\nAccounts initialized successfully.")
    show_accounts()


def show_accounts():
    """Display current account balances."""
    for account in accounts.find({}, {"_id": 0}).sort("account_id", 1):
        print(account)


def transfer_money(source, destination, amount):
    """
    Transfer money atomically using a MongoDB transaction.

    Retry transactions labelled TransientTransactionError
    using exponential backoff.
    """
    if amount <= 0:
        raise ValueError("Transfer amount must be positive.")

    if source == destination:
        raise ValueError("Source and destination must differ.")

    for attempt in range(MAX_RETRIES):
        try:
            with client.start_session() as session:
                with session.start_transaction():

                    # Debit only if the source has enough money.
                    debit = accounts.update_one(
                        {
                            "account_id": source,
                            "balance": {"$gte": amount}
                        },
                        {
                            "$inc": {
                                "balance": -amount,
                                "version": 1
                            }
                        },
                        session=session
                    )

                    if debit.matched_count != 1:
                        source_account = accounts.find_one(
                            {"account_id": source},
                            session=session
                        )

                        if source_account is None:
                            raise AccountNotFoundError(
                                f"Source account {source} not found."
                            )

                        raise InsufficientFundsError(
                            f"Insufficient funds in {source}. "
                            f"Available: {source_account['balance']}, "
                            f"requested: {amount}."
                        )

                    # Credit the destination in the same transaction.
                    credit = accounts.update_one(
                        {"account_id": destination},
                        {
                            "$inc": {
                                "balance": amount,
                                "version": 1
                            }
                        },
                        session=session
                    )

                    if credit.matched_count != 1:
                        raise AccountNotFoundError(
                            f"Destination account {destination} not found."
                        )

                    # Record history in the same transaction.
                    history.insert_one(
                        {
                            "from": source,
                            "to": destination,
                            "amount": amount,
                            "timestamp": datetime.now(timezone.utc),
                            "status": "completed"
                        },
                        session=session
                    )

                # The transaction commits when the context exits normally.

            print(
                f"\nSUCCESS: Transferred {amount:.2f} "
                f"from {source} to {destination}."
            )
            return True

        except InsufficientFundsError as exc:
            # The transaction context aborts before this exception is caught.
            print(f"\nTRANSFER REJECTED: {exc}")
            return False

        except AccountNotFoundError as exc:
            print(f"\nTRANSFER REJECTED: {exc}")
            return False

        except PyMongoError as exc:
            if (
                exc.has_error_label("TransientTransactionError")
                and attempt < MAX_RETRIES - 1
            ):
                delay = BASE_DELAY * (2 ** attempt)
                print(
                    f"\nTransient transaction error. "
                    f"Retry {attempt + 1}/{MAX_RETRIES - 1} "
                    f"in {delay:.2f} seconds."
                )
                time.sleep(delay)
                continue

            print(f"\nMongoDB transaction failed: {exc}")
            raise

    return False


def get_balances():
    """Return account balances as a dictionary."""
    return {
        account["account_id"]: account["balance"]
        for account in accounts.find(
            {},
            {"_id": 0, "account_id": 1, "balance": 1}
        )
    }


def show_history():
    """Display transaction history."""
    print("\nTransaction history:")
    for record in history.find({}, {"_id": 0}):
        print(record)

    print("Total history records:", history.count_documents({}))


def main():
    try:
        # Verify connectivity before running the experiment.
        client.admin.command("ping")
        print("MongoDB connection successful.")

        # Prepare the initial state.
        initialize_accounts()
        initial_balances = get_balances()

        print("\nInitial balances:", initial_balances)

        # Test 1: Successful transfer.
        transfer_money("ACC-001", "ACC-002", 100.0)

        successful_balances = get_balances()
        print("\nBalances after successful transfer:")
        print(successful_balances)

        expected_balances = {
            "ACC-001": 400.0,
            "ACC-002": 300.0
        }

        print(
            "Successful transfer verified:",
            successful_balances == expected_balances
        )

        # Save the state before the insufficient-funds test.
        before_failed_transfer = get_balances()
        history_before = history.count_documents({})

        # Test 2: Attempt to transfer more than the available balance.
        transfer_money("ACC-001", "ACC-002", 10000.0)

        after_failed_transfer = get_balances()
        history_after = history.count_documents({})

        print("\nBalances before rejected transfer:")
        print(before_failed_transfer)

        print("Balances after rejected transfer:")
        print(after_failed_transfer)

        print(
            "Insufficient-funds rollback verified:",
            before_failed_transfer == after_failed_transfer
        )

        print(
            "Rejected transfer created no history record:",
            history_before == history_after
        )

        print("\nFinal account state:")
        show_accounts()
        show_history()

    except PyMongoError as exc:
        print("\nCould not complete the lab.")
        print("Check the MongoDB connection and replica-set primary.")
        print("Error:", exc)

    finally:
        client.close()


if __name__ == "__main__":
    main()