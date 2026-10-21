temperatures = [22.5, 25.0, 26.0]
count = 0
for temperature_c in temperatures:
    if temperature_c > 24.0:
        count = count + 1
print(count)
