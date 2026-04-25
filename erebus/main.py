from application.runner import run_erebus


def main():
    """
    Console entry point of the EREBUS engine.
    """

    target = input("Enter target domain: ").strip()

    if not target:
        print("Empty target provided")
        return

    run_erebus(target)


if __name__ == "__main__":
    main()