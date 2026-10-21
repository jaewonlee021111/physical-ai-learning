def report(sensor_id, value):
    return f"{sensor_id} {value}"
print(report("S01", 22.5))
print(report("S03", 0.0))
try:
    report("S01")
except TypeError as error:
    print(type(error).__name__)
