"""Run the uploaded brief's examples without opening a graphical window."""
from ecc import Curve, format_point


def main():
    curve, point = Curve(17, 2, 2), (5, 1)
    points = curve.enumerate_points()
    print(curve.equation)
    print(f"Finite points: {len(points)-1}; total group order: {len(points)}")
    examples = [
        ("P + P", curve.add(point, point), (6, 3)),
        ("P + (6, 3)", curve.add(point, (6, 3)), (10, 6)),
        ("7P", curve.multiply(7, point), (0, 6)),
        ("P + (5, 16)", curve.add(point, (5, 16)), None),
        ("0P", curve.multiply(0, point), None),
        ("19P", curve.multiply(19, point), None),
        ("(-1)P", curve.multiply(-1, point), (5, 16)),
        ("E5(1,0): 2(0,0)", Curve(5, 1, 0).add((0, 0), (0, 0)), None),
    ]
    assert len(points) == 19
    for name, actual, expected in examples:
        assert actual == expected, (name, actual, expected)
        print(f"PASS  {name:20s} = {format_point(actual)}")
    for label, operation in (
        ("off-curve (1,1)", lambda: curve.add((1, 1), point)),
        ("composite p=15", lambda: Curve(15, 2, 2)),
        ("singular E17(0,0)", lambda: Curve(17, 0, 0)),
    ):
        try:
            operation()
        except ValueError:
            print(f"PASS  Reject {label}")
        else:
            raise AssertionError(f"Did not reject {label}")
    print("\n7P trace:\n" + curve.explain_multiply(7, point).as_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
