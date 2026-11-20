"""
NoSQL Lab 11.1: Evaluate Shard Key Choices
Objective:
Evaluate shard keys for an e-commerce order management system
and research MongoDB 5.0+ online resharding.

Run:
    python lab11/lab_01_shard_key_eval.py
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def display_decision_matrix():
    """Compare all four shard-key candidates required by the lab."""

    table = Table(
        title="Lab 11.1 — Shard Key Decision Matrix",
        show_lines=True,
        header_style="bold cyan"
    )

    table.add_column("Candidate Shard Key", style="bold", width=22)
    table.add_column("Cardinality", width=18)
    table.add_column("Distribution", width=25)
    table.add_column("Query Targeting", width=30)
    table.add_column("Hotspot Risk", width=16)
    table.add_column("Verdict", width=30)

    table.add_row(
        "order_id",
        "High, if unique",
        "Generally even for well-distributed IDs",
        "Efficient for order-ID lookups; customer queries may scatter",
        "Low with random IDs",
        "Suitable when order-ID lookups dominate"
    )

    table.add_row(
        "customer_id",
        "Depends on customer population",
        "Can be skewed by customer activity",
        "Good for customer-specific queries",
        "Possible skew / hot customers",
        "Useful when customer queries dominate"
    )

    table.add_row(
        "order_date",
        "High over time",
        "Monotonically increasing values can concentrate new writes",
        "Good for date-range queries when ranges are appropriately distributed",
        "High for ongoing inserts",
        "Avoid for insert-heavy workloads without mitigation"
    )

    table.add_row(
        "customer_id (hashed)",
        "High if many distinct customers",
        "Hashing generally spreads customer keys more evenly",
        "Good for equality queries on customer_id; range queries are not efficient",
        "Generally lower for sequential-key hotspots",
        "Recommended for this workload if customer-scoped queries dominate"
    )

    console.print(table)


def display_recommendation():
    console.print(
        Panel(
            "[bold green]Recommendation: hashed customer_id[/bold green]\n\n"
            "Hashing generally distributes customer key values more evenly "
            "across the shard-key space and reduces the sequential-write "
            "hotspot risk associated with a monotonically increasing key.\n\n"
            "Queries that specify customer_id can target the relevant shard "
            "using the hashed shard key. However, queries by order_id alone "
            "may scatter across shards, and hashed keys do not efficiently "
            "support range queries on the hashed field.\n\n"
            "This recommendation assumes that customer-scoped lookups and "
            "balanced distribution are priorities. The final choice should "
            "be validated against the application's real query workload.",
            title="Shard Key Recommendation",
            border_style="green"
        )
    )


def display_resharding_activity():
    """Present the research activity required by Lab 11.1."""

    console.print(
        Panel(
            "[bold]What is resharding?[/bold]\n"
            "Resharding changes the shard key of an existing sharded "
            "collection so its data can be redistributed for a revised "
            "workload. MongoDB supports online resharding beginning "
            "with MongoDB 5.0.\n\n"
            "[bold]General procedure[/bold]\n"
            "1. Confirm the MongoDB version, cluster health, permissions, "
            "and resharding prerequisites.\n"
            "2. Review the existing shard key, indexes, query patterns, "
            "data volume, and available disk capacity.\n"
            "3. Select a new shard key that matches the workload.\n"
            "4. On a supported MongoDB deployment, issue "
            "sh.reshardCollection() with the collection namespace and "
            "new shard key.\n"
            "5. Monitor the operation and cluster resource usage.\n"
            "6. Verify completion, the resulting shard key, data "
            "availability, and query performance.\n"
            "7. Validate application behavior and monitor the cluster "
            "after the change.\n\n"
            "[bold]Example command — illustrative only[/bold]\n"
            'sh.reshardCollection("shop.orders", '
            '{ customer_id: "hashed" })\n\n'
            "[bold]Limitations and considerations[/bold]\n"
            "• Resharding consumes additional CPU, network, and disk I/O.\n"
            "• Sufficient free disk space is required while data is "
            "copied and redistributed.\n"
            "• The operation can affect performance; writes may be "
            "temporarily blocked during a critical transition.\n"
            "• Unique indexes must satisfy MongoDB's shard-key "
            "compatibility requirements.\n"
            "• Only one collection can be resharded at a time per cluster.\n"
            "• Supported options and restrictions depend on the MongoDB "
            "version and deployment configuration.\n"
            "• The new key must be suitable for the workload; resharding "
            "does not automatically fix poor query design.",
            title="Try It Yourself — MongoDB 5.0+ Resharding",
            border_style="blue"
        )
    )


def main():
    console.print(
        Panel(
            "E-commerce Order Management System",
            title="NoSQL Lab 11.1",
            border_style="cyan"
        )
    )

    display_decision_matrix()
    display_recommendation()
    display_resharding_activity()

    console.print(
        "\n[bold green]Lab 11.1 analysis displayed.[/bold green]"
    )


if __name__ == "__main__":
    main()