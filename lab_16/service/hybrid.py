class HybridFraudService:
    def __init__(self, hub):
        self.hub = hub

    def get_transaction(self, txn_id):
        doc = self.hub.run(
            "mongo",
            lambda: self.hub.mongo.transactions.find_one(
                {"transaction_id": txn_id},
                {"_id": 0}
            )
        )
        if not doc:
            return None

        events = self.hub.run(
            "cassandra",
            lambda: list(self.hub.cassandra_session.execute(
                """
                SELECT user_id, event_time, event_type, amount, counterparty_id
                FROM user_events WHERE user_id=%s LIMIT 20
                """,
                (doc.get("user_id", ""),)
            ))
        )

        doc["recent_events"] = [
            {
                "user_id": row.user_id,
                "event_time": row.event_time.isoformat() if row.event_time else None,
                "event_type": row.event_type,
                "amount": row.amount,
                "counterparty_id": row.counterparty_id
            } for row in events
        ]
        return doc

    def get_user_profile(self, user_id):
        profile = self.hub.run(
            "mongo",
            lambda: self.hub.mongo.users.find_one(
                {"user_id": user_id},
                {"_id": 0}
            )
        )

        events = self.hub.run(
            "cassandra",
            lambda: list(self.hub.cassandra_session.execute(
                """
                SELECT event_time, event_type, transaction_id, amount, counterparty_id
                FROM user_events WHERE user_id=%s LIMIT 50
                """,
                (user_id,)
            ))
        )

        graph_data = self.hub.run(
            "neo4j",
            lambda: self._user_graph(user_id)
        )

        return {
            "user_id": user_id,
            "profile": profile,
            "recent_events": [
                {
                    "event_time": row.event_time.isoformat() if row.event_time else None,
                    "event_type": row.event_type,
                    "transaction_id": row.transaction_id,
                    "amount": row.amount,
                    "counterparty_id": row.counterparty_id
                } for row in events
            ],
            "connected_users": graph_data
        }

    def _user_graph(self, user_id):
        query = """
        MATCH (u:User {id:$uid})-[:TRANSFERRED_TO*1..2]-(other:User)
        RETURN DISTINCT other.id AS user_id
        LIMIT 50
        """
        with self.hub.neo4j_driver.session() as session:
            return [r["user_id"] for r in session.run(query, uid=user_id)]

    def detect_fraud_rings(self, user_id, max_hops=3):
        if not 1 <= int(max_hops) <= 5:
            raise ValueError("max_hops must be between 1 and 5")

        query = """
        MATCH path=(u:User {id:$uid})-[:TRANSFERRED_TO*1..%d]-(other:User)
        RETURN DISTINCT other.id AS user_id, length(path) AS hops
        ORDER BY hops
        LIMIT 100
        """ % int(max_hops)

        graph = self.hub.run(
            "neo4j",
            lambda: self._run_graph_query(query, user_id)
        )

        events = self.hub.run(
            "cassandra",
            lambda: list(self.hub.cassandra_session.execute(
                """
                SELECT event_time, event_type, transaction_id, amount, counterparty_id
                FROM user_events WHERE user_id=%s LIMIT 50
                """,
                (user_id,)
            ))
        )

        high_value_events = [
            {
                "transaction_id": row.transaction_id,
                "amount": row.amount,
                "counterparty_id": row.counterparty_id,
                "event_type": row.event_type
            }
            for row in events if row.amount is not None and row.amount >= 10000
        ]

        return {
            "user_id": user_id,
            "max_hops": int(max_hops),
            "connected_users": graph,
            "high_value_events": high_value_events,
            "possible_ring": len(graph) >= 3 or len(high_value_events) >= 3
        }

    def _run_graph_query(self, query, user_id):
        with self.hub.neo4j_driver.session() as session:
            return [
                {"user_id": r["user_id"], "hops": r["hops"]}
                for r in session.run(query, uid=user_id)
            ]
