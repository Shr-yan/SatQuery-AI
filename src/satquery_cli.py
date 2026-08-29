from query_engine import (
    process_query,
)


def run_cli():

    print(
        "SatQuery AI"
    )

    print(
        "-----------"
    )

    print(
        "Enter a satellite-analysis query."
    )

    print(
        "Type 'exit' to quit."
    )

    while True:

        query = input(
            "\nSatQuery > "
        ).strip()

        if query.lower() in {
            "exit",
            "quit",
            "q",
        }:

            print(
                "Goodbye."
            )

            break

        if not query:

            continue

        print(
            "\nProcessing...\n"
        )

        _, formatted = (
            process_query(
                query
            )
        )

        print(
            formatted
        )


if __name__ == "__main__":

    run_cli()