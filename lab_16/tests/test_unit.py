from unittest.mock import Mock
import pytest

from service.breaker import CircuitBreaker, State
from service.hybrid import HybridFraudService


def test_circuit_breaker_opens_after_three_failures():
    breaker = CircuitBreaker(threshold=3, recovery_seconds=30)

    for _ in range(3):
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("failure")))

    assert breaker.state == State.OPEN
    assert breaker.allow_request() is False


def test_circuit_breaker_recovers_after_success():
    breaker = CircuitBreaker()
    breaker.record_failure()
    breaker.record_success()

    assert breaker.state == State.CLOSED
    assert breaker.failures == 0


def test_invalid_hop_count():
    service = HybridFraudService(Mock())

    with pytest.raises(ValueError):
        service.detect_fraud_rings("U001", 0)

    with pytest.raises(ValueError):
        service.detect_fraud_rings("U001", 6)


def test_transaction_not_found():
    hub = Mock()
    hub.run.return_value = None
    service = HybridFraudService(hub)

    assert service.get_transaction("UNKNOWN") is None


def test_transaction_merges_cassandra_events():
    hub = Mock()
    hub.mongo.transactions.find_one.return_value = {
        "transaction_id": "TXN001",
        "user_id": "U001"
    }

    event = Mock()
    event.user_id = "U001"
    event.event_time = None
    event.event_type = "TRANSFER"
    event.amount = 15000.0
    event.counterparty_id = "U002"

    hub.cassandra_session.execute.return_value = [event]
    hub.run.side_effect = lambda backend, fn: fn()

    service = HybridFraudService(hub)
    result = service.get_transaction("TXN001")

    assert result["transaction_id"] == "TXN001"
    assert len(result["recent_events"]) == 1
    assert result["recent_events"][0]["amount"] == 15000.0


def test_fraud_detection_uses_graph_and_events():
    hub = Mock()
    hub.run.side_effect = [
        [{"user_id": "U002", "hops": 1},
         {"user_id": "U003", "hops": 2},
         {"user_id": "U004", "hops": 3}],
        []
    ]

    service = HybridFraudService(hub)
    result = service.detect_fraud_rings("U001", 3)

    assert result["possible_ring"] is True
    assert len(result["connected_users"]) == 3
