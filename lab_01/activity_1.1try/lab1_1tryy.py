from rich.console import Console
from rich.panel import Panel

console = Console()


def main():

    console.print(
        Panel.fit(
            "Lab 1.1 - Try Yourself",
            title="NoSQL Database Classification"
        )
    )

    # Database selected for research
    database = "InfluxDB"

    # Answer to Question 1: Classification
    family = "Wide-Column / Time-Series"
    classification = "Specialized Time-Series Database"

    reason = (
        "InfluxDB is designed specifically for storing and querying "
        "time-series data. It is optimized for high-speed writes and "
        "queries based on time."
    )

    # Answer to Question 2: Does it fit neatly into one family?
    family_fit = "No"
    
    explanation = (
        "InfluxDB does not fit neatly into one of the four traditional "
        "NoSQL families. It is a specialized time-series database, "
        "although its data model and use cases are closest to the "
        "Wide-Column / Time-Series family."
    )

    console.print("\n--- Question 1: Classify the Database Product ---")
    console.print(f"Database Product : {database}")
    console.print(f"NoSQL Family     : {family}")
    console.print(f"Classification   : {classification}")
    console.print(f"Reason           : {reason}")

    console.print("\n--- Question 2: Does it fit neatly into one family? ---")
    console.print(f"Answer           : {family_fit}")
    console.print(f"Explanation      : {explanation}")

    console.print("\n" + "=" * 65)
    console.print("Lab 1.1 Try Yourself Complete")
    console.print("=" * 65)


if __name__ == "__main__":
    main()