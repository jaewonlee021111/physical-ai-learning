for raw in ["뜨거움", "24.0"]:
    try:
        print(float(raw))
    except ValueError:
        print(f"확인 필요: 원문={raw!r}")
