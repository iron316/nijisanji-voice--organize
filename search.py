def main():
    with open("log.txt") as f:
        logs = f.read().split("\n")

    query = input("QUERY >>> ")
    for log in logs:
        if query in log:
            print(log)


if __name__ == "__main__":
    main()
