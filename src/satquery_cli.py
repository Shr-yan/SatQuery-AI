from query_engine import process_query


def main():

    print(
        "\nSatQuery AI"
        "\n-----------"
    )

    print(
        "Enter a satellite-analysis query."
    )

    print(
        "Type 'exit' to quit.\n"
    )

    while True:

        try:

            query = input(
                "SatQuery > "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError,
        ):

            print("\nGoodbye.")
            break

        if not query:
            continue

        if query.lower() in [
            "exit",
            "quit",
            "q",
        ]:

            print("Goodbye.")
            break

        print(
            "\nProcessing...\n"
        )

        _, response = process_query(
            query
        )

        print(response)
        print()


if __name__ == "__main__":
    main()