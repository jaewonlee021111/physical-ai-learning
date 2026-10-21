from log_checker import parse_temperature
for raw in ["0", "50", "51.0"]:
    try:
        print(raw, parse_temperature(raw))
    except ValueError as error:
        print(raw, str(error))
