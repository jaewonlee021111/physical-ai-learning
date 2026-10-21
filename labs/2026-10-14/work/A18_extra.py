price, count = 1500, 2
total = price * count
print(total, "무료 배송" if total >= 5000 else "배송비 추가")
