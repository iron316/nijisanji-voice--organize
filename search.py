def main():
    with open("log.txt") as f:
        logs = f.read().split("\n")
        logs = sorted(logs)
    while True:
        query = input("QUERY >>> ")
        if query == "":
            break
        for log in logs:
            if query in log:
                print(log)


if __name__ == "__main__":
    main()
