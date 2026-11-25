"""Independent enumeration, a geometric addition oracle, and group-law checks."""
import math
import random
import unittest
from ecc import (Curve, ENUMERATION_LIMIT, MAX_PRIME, format_point,
                 inverse_mod, is_prime, parse_integer, parse_point)


def brute_points(curve):
    """Deliberately simple O(p²) oracle; does not use the residue-map algorithm."""
    return (None,) + tuple((x, y) for x in range(curve.p) for y in range(curve.p)
                          if y*y % curve.p == (x*x*x + curve.a*x + curve.b) % curve.p)


def geometric_add(curve, left, right, points):
    """Independent line-intersection oracle for small fields.

    Intersect y = mx+c with the curve. For distinct points, the third root of
    the substituted cubic is found from its product (Vieta) when x1*x2 != 0,
    otherwise from the root sum; tangent case uses root sum with multiplicity.
    This is augmented by a direct geometric on-line membership check.
    Python's built-in pow computes the reference inverse (not our Euclid code).
    """
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and (y1+y2) % curve.p == 0:
        return None
    numerator, denominator = ((3*x1*x1+curve.a, 2*y1) if left == right
                              else (y2-y1, x2-x1))
    m = numerator * pow(denominator, -1, curve.p) % curve.p
    intercept = (y1-m*x1) % curve.p
    if left != right and (x1*x2) % curve.p:
        # x³ − m²x² + (a−2mc)x + (b−c²) = 0
        x3 = (intercept*intercept-curve.b) * pow(x1*x2, -1, curve.p) % curve.p
    else:
        x3 = (m*m-x1-x2) % curve.p
    third = (x3, (m*x3+intercept) % curve.p)
    if third not in points:
        raise AssertionError("Reference line intersection is not on the curve")
    return (third[0], -third[1] % curve.p)


class FieldTests(unittest.TestCase):
    def test_primality_matches_sieve(self):
        sieve = [True]*2000
        sieve[:2] = [False, False]
        for i in range(2, math.isqrt(1999)+1):
            if sieve[i]:
                for multiple in range(i*i, 2000, i):
                    sieve[multiple] = False
        for value, expected in enumerate(sieve):
            self.assertEqual(is_prime(value), expected, value)
        self.assertTrue(is_prime(MAX_PRIME))
        self.assertFalse(is_prime(-7))

    def test_inverse_exhaustive(self):
        for modulus in range(2, 70):
            for value in range(-modulus, modulus):
                if math.gcd(value, modulus) == 1:
                    self.assertEqual(value*inverse_mod(value, modulus) % modulus, 1)
                    self.assertEqual(inverse_mod(value, modulus), pow(value, -1, modulus))
                else:
                    with self.assertRaises(ValueError):
                        inverse_mod(value, modulus)

    def test_invalid_modulus_and_types(self):
        for modulus in (0, 1, -9, True, 2.5):
            with self.assertRaises(ValueError):
                inverse_mod(1, modulus)
        for p in (-1, 0, 2, 3, 15, 21, MAX_PRIME+1, True, 17.0):
            with self.assertRaises(ValueError):
                Curve(p, 2, 2)
        for a, b in ((True, 2), (2, 2.1), ("2", 2)):
            with self.assertRaises(ValueError):
                Curve(17, a, b)

    def test_input_parsing(self):
        for value in ("O", "o", " infinity ", "∞"):
            self.assertIsNone(parse_point(value))
        self.assertEqual(parse_point(" (5, 1) "), (5, 1))
        self.assertEqual(parse_point("5,1"), (5, 1))
        self.assertEqual(parse_point("-1, +2"), (-1, 2))
        for value in ("", "5", "(5,1", "5,1)", "1,2,3", "1.2,4", "None", "1e2,3"):
            with self.assertRaises(ValueError, msg=value):
                parse_point(value)
        for value in ("", "++2", "+-2", "2-1", "1.5", "2e4", "1_000", "１２", "1"*101):
            with self.assertRaises(ValueError, msg=value):
                parse_integer(value, "value")
        self.assertEqual(parse_integer(" -19 ", "k"), -19)
        self.assertEqual(format_point(None), "O")


class CurveTests(unittest.TestCase):
    def setUp(self):
        self.curve = Curve(17, 2, 2)
        self.P = (5, 1)

    def test_required_examples(self):
        c, p = self.curve, self.P
        self.assertEqual(len(c.enumerate_points()), 19)
        self.assertEqual(sum(pt is not None for pt in c.enumerate_points()), 18)
        self.assertEqual(c.add(p, p), (6, 3))
        self.assertEqual(c.add(p, (6, 3)), (10, 6))
        self.assertEqual(c.multiply(7, p), (0, 6))
        self.assertIsNone(c.add(p, (5, 16)))
        self.assertIsNone(c.multiply(0, p))
        self.assertIsNone(c.multiply(19, p))
        self.assertEqual(c.multiply(-1, p), (5, 16))
        self.assertIsNone(Curve(5, 1, 0).add((0, 0), (0, 0)))

    def test_validation_and_normalization(self):
        self.assertEqual(Curve(17, -15, 36), self.curve)
        with self.assertRaises(ValueError):
            Curve(17, 0, 0)
        for point in ((1, 1), (22, 1), (5, -16), [5, 1], (5,), (True, 1), "O", (5, 1.0)):
            self.assertFalse(self.curve.contains(point))
            for operation in (lambda: self.curve.add(point, None),
                              lambda: self.curve.add(None, point),
                              lambda: self.curve.multiply(0, point),
                              lambda: self.curve.negate(point)):
                with self.assertRaises(ValueError):
                    operation()
        for scalar in (True, 1.5, "2"):
            with self.assertRaises(ValueError):
                self.curve.multiply(scalar, self.P)

    def test_enumeration_matches_brute_force(self):
        # Every nonsingular short-Weierstrass curve in these prime fields.
        for p in (5, 7, 11, 13):
            for a in range(p):
                for b in range(p):
                    if (4*a**3+27*b*b) % p == 0:
                        continue
                    curve = Curve(p, a, b)
                    self.assertEqual(curve.enumerate_points(), brute_points(curve))
        self.assertGreater(len(Curve(ENUMERATION_LIMIT, 2, 2).enumerate_points()), 0)
        with self.assertRaises(ValueError):
            Curve(1009, 2, 2).enumerate_points()

    def test_every_addition_against_geometric_oracle(self):
        for p in (5, 7, 11):
            for a in range(p):
                for b in range(p):
                    if (4*a**3+27*b*b) % p == 0:
                        continue
                    curve = Curve(p, a, b)
                    points = brute_points(curve)
                    for left in points:
                        for right in points:
                            self.assertEqual(curve.add(left, right),
                                             geometric_add(curve, left, right, points),
                                             (p, a, b, left, right))

    def test_group_laws_exhaustive(self):
        # Exhaustively check all point triples on four separate small curves.
        for curve in (Curve(5, 1, 0), Curve(7, 2, 1), Curve(11, 1, 6), self.curve):
            points = curve.enumerate_points()
            # Precompute the actual implementation's operation table.
            table = {(p, q): curve.add(p, q) for p in points for q in points}
            for p in points:
                self.assertEqual(table[p, None], p)
                self.assertEqual(table[None, p], p)
                self.assertIsNone(table[p, curve.negate(p)])
                for q in points:
                    self.assertIn(table[p, q], points)  # closure
                    self.assertEqual(table[p, q], table[q, p])
                    for r in points:
                        self.assertEqual(table[table[p, q], r], table[p, table[q, r]])

    def test_scalar_matches_repeated_addition(self):
        for curve in (Curve(5, 1, 0), Curve(7, 2, 1), self.curve):
            for point in curve.enumerate_points():
                result = None
                for k in range(61):
                    self.assertEqual(curve.multiply(k, point), result)
                    self.assertEqual(curve.multiply(-k, point), curve.negate(result))
                    result = curve.add(result, point)

    def test_lagrange_and_hasse_checks(self):
        for p in (5, 7, 11, 17, 97):
            c = Curve(p, 1, 0)
            pts = c.enumerate_points()
            self.assertLessEqual(abs(len(pts)-(p+1)), 2*math.sqrt(p))
            for point in pts:
                self.assertIsNone(c.multiply(len(pts), point))

    def test_large_scalar_and_distributivity(self):
        rng = random.Random(455)
        c, p = self.curve, self.P
        large = 2**255 + 12345
        self.assertEqual(c.multiply(large, p), c.multiply(large % 19, p))
        for _ in range(120):
            k, m = rng.randint(-1000, 1000), rng.randint(-1000, 1000)
            self.assertEqual(c.multiply(k+m, p), c.add(c.multiply(k, p), c.multiply(m, p)))
            q = rng.choice(c.enumerate_points())
            self.assertEqual(c.multiply(k, c.add(p, q)), c.add(c.multiply(k, p), c.multiply(k, q)))

    def test_educational_trace(self):
        c, p = self.curve, self.P
        addition = c.explain_add(p, p)
        self.assertEqual(addition.slope, 13)
        self.assertEqual(addition.case, "doubling")
        self.assertIn("Extended Euclid", "\n".join(addition.steps))
        self.assertEqual(c.explain_add(p, c.negate(p)).case, "inverse pair")
        self.assertEqual(Curve(5, 1, 0).explain_add((0, 0), (0, 0)).case, "vertical tangent")
        for k in (1, 7, 19, -7, 2**255+1):
            trace = c.explain_multiply(k, p)
            self.assertEqual(len(trace.steps), abs(k).bit_length())
            self.assertEqual([s.bit for s in trace.steps], [int(b) for b in bin(abs(k))[2:][::-1]])
            previous = None
            for s in trace.steps:
                self.assertEqual(s.accumulator_before, previous)
                self.assertEqual(s.next_addend, c.add(s.addend, s.addend))
                expected = c.add(previous, s.addend) if s.bit else previous
                self.assertEqual(s.accumulator_after, expected)
                previous = expected
            self.assertEqual(trace.result, previous)
            self.assertIn("DOUBLE", trace.as_text())
        self.assertEqual(c.explain_multiply(0, p).steps, ())
        self.assertEqual(c.explain_multiply(100, None).steps, ())


if __name__ == "__main__":
    unittest.main(verbosity=2)
