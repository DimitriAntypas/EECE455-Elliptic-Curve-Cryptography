"""Exact, dependency-free elliptic-curve arithmetic for educational prime fields.

A finite point is an immutable (x, y) tuple. None represents the identity O.
The GUI is deliberately absent from this module. All arithmetic uses integers.
"""
from dataclasses import dataclass
from math import isqrt
from typing import Optional, Tuple

Point = Optional[Tuple[int, int]]
INFINITY: Point = None
MAX_PRIME = 2_147_483_647  # exact trial division remains bounded
ENUMERATION_LIMIT = 997


def _integer(value, name):
    if type(value) is not int:  # bool is an int subclass, but is not an input here
        raise ValueError(f"{name} must be an integer.")


def is_prime(n: int) -> bool:
    """Deterministic trial division, O(sqrt(n)); no probabilistic decisions."""
    _integer(n, "p")
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    return all(n % d for d in range(3, isqrt(n) + 1, 2))


def inverse_mod(value: int, modulus: int) -> int:
    """Multiplicative inverse from the extended Euclidean algorithm.

    During the loop, t tracks the coefficient of value in a Bezout identity.
    A gcd other than 1 means the inverse does not exist.
    """
    _integer(value, "value")
    _integer(modulus, "modulus")
    if modulus <= 1:
        raise ValueError("Modulus must be greater than 1.")
    old_r, r = modulus, value % modulus
    old_t, t = 0, 1
    while r:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_t, t = t, old_t - quotient * t
    if old_r != 1:
        raise ValueError(f"{value} has no inverse modulo {modulus}.")
    return old_t % modulus


def format_point(point: Point) -> str:
    return "O" if point is None else f"({point[0]}, {point[1]})"


def parse_integer(text: str, name: str, max_digits: int = 100) -> int:
    """Accept signed decimal integers only; bound text before conversion."""
    stripped = text.strip()
    digits = stripped.lstrip("+-")
    if (not digits or len(digits) > max_digits or not digits.isascii()
            or not digits.isdecimal() or stripped.count("+") + stripped.count("-") > 1
            or ("+" in stripped[1:] or "-" in stripped[1:])):
        raise ValueError(f"{name}: enter a decimal integer (at most {max_digits} digits).")
    return int(stripped)


def parse_point(text: str) -> Point:
    """Parse O/infinity/∞ or x,y / (x,y). Validation belongs to Curve."""
    value = text.strip()
    if value.lower() in ("o", "infinity", "∞"):
        return None
    if value.startswith("(") and value.endswith(")"):
        value = value[1:-1]
    pieces = value.split(",")
    if len(pieces) != 2:
        raise ValueError("Enter a point as (x, y), or O for the point at infinity.")
    return (parse_integer(pieces[0], "x"), parse_integer(pieces[1], "y"))


@dataclass(frozen=True)
class Addition:
    result: Point
    slope: Optional[int]
    case: str
    steps: Tuple[str, ...]


@dataclass(frozen=True)
class ScalarStep:
    index: int
    bit: int
    accumulator_before: Point
    addend: Point
    accumulator_after: Point
    next_addend: Point
    addition: Optional[Addition]
    doubling: Addition


@dataclass(frozen=True)
class Multiplication:
    scalar: int
    original_point: Point
    working_point: Point
    result: Point
    steps: Tuple[ScalarStep, ...]
    explanation: str

    def as_text(self) -> str:
        lines = [f"{self.scalar} × {format_point(self.original_point)} = {format_point(self.result)}",
                 self.explanation]
        if self.scalar < 0:
            lines.append(f"Working point −P = {format_point(self.working_point)}")
        lines.append("Read binary digits from right to left (least significant first).")
        for s in self.steps:
            lines.extend(["", f"Bit {s.index} = {s.bit}; A = {format_point(s.addend)}; "
                          f"R before = {format_point(s.accumulator_before)}"])
            if s.addition:
                lines.append("ADD into accumulator:")
                lines.extend("  " + line for line in s.addition.steps)
            else:
                lines.append("SKIP addition: this binary digit is 0.")
            lines.append(f"R after = {format_point(s.accumulator_after)}")
            lines.append("DOUBLE addend (including the final iteration):")
            lines.extend("  " + line for line in s.doubling.steps)
        return "\n".join(lines)


@dataclass(frozen=True)
class Curve:
    p: int
    a: int
    b: int

    def __post_init__(self):
        for value, name in ((self.p, "p"), (self.a, "a"), (self.b, "b")):
            _integer(value, name)
        if not 3 < self.p <= MAX_PRIME:
            raise ValueError(f"Choose a prime p with 3 < p ≤ {MAX_PRIME}.")
        if not is_prime(self.p):
            raise ValueError(f"p = {self.p} is composite. Choose a prime number.")
        object.__setattr__(self, "a", self.a % self.p)
        object.__setattr__(self, "b", self.b % self.p)
        if self.discriminant == 0:
            raise ValueError("Singular curve: (4a³ + 27b²) mod p = 0. Change a or b.")

    @property
    def discriminant(self) -> int:
        """The nonsingularity expression, not the full discriminant −16(...)."""
        return (4 * self.a ** 3 + 27 * self.b ** 2) % self.p

    @property
    def equation(self) -> str:
        return f"y² ≡ x³ + {self.a}x + {self.b}  (mod {self.p})"

    def contains(self, point: Point) -> bool:
        if point is None:
            return True
        if (not isinstance(point, tuple) or len(point) != 2
                or any(type(c) is not int for c in point)):
            return False
        x, y = point
        return (0 <= x < self.p and 0 <= y < self.p
                and (y * y - x ** 3 - self.a * x - self.b) % self.p == 0)

    def validate_point(self, point: Point) -> None:
        if not self.contains(point):
            raise ValueError(f"Invalid point {point!r}. Use coordinates in 0…{self.p - 1} "
                             "that satisfy the active curve, or O.")

    def enumerate_points(self) -> Tuple[Point, ...]:
        """O first, then finite points in lexicographic order; O(p + N) work.

        The residue map stores all y values, preserving both roots and y=0.
        O(p + N) memory; N is the number of finite curve points.
        """
        if self.p > ENUMERATION_LIMIT:
            raise ValueError(f"Enumeration/plotting is limited to p ≤ {ENUMERATION_LIMIT}.")
        residues = {}
        for y in range(self.p):
            residues.setdefault(y * y % self.p, []).append(y)
        points = [None]
        for x in range(self.p):
            rhs = (x ** 3 + self.a * x + self.b) % self.p
            points.extend((x, y) for y in residues.get(rhs, ()))
        return tuple(points)

    def negate(self, point: Point) -> Point:
        self.validate_point(point)
        return None if point is None else (point[0], -point[1] % self.p)

    def add(self, left: Point, right: Point) -> Point:
        return self.explain_add(left, right).result

    def explain_add(self, left: Point, right: Point) -> Addition:
        self.validate_point(left)
        self.validate_point(right)
        heading = f"P = {format_point(left)}, Q = {format_point(right)}"
        if left is None or right is None:
            result = right if left is None else left
            return Addition(result, None, "identity", (heading,
                "O is the group identity: O + P = P and P + O = P.",
                f"Result = {format_point(result)}"))
        x1, y1 = left
        x2, y2 = right
        # Covers distinct inverse pairs AND doubling a point with y = 0.
        if x1 == x2 and (y1 + y2) % self.p == 0:
            case = "vertical tangent" if left == right else "inverse pair"
            reason = ("Here y = 0, so P = −P; doubling gives O."
                      if left == right else "Same x and opposite y: P + (−P) = O.")
            return Addition(None, None, case, (heading, reason, "Result = O"))
        if left == right:
            numerator = (3 * x1 * x1 + self.a) % self.p
            denominator = 2 * y1 % self.p
            rule, case = "λ = (3x₁² + a) · (2y₁)⁻¹ mod p", "doubling"
        else:
            numerator = (y2 - y1) % self.p
            denominator = (x2 - x1) % self.p
            rule, case = "λ = (y₂ − y₁) · (x₂ − x₁)⁻¹ mod p", "addition"
        inverse = inverse_mod(denominator, self.p)
        slope = numerator * inverse % self.p
        x3 = (slope * slope - x1 - x2) % self.p
        y3 = (slope * (x1 - x3) - y1) % self.p
        steps = (heading, rule,
                 f"Numerator ≡ {numerator}; denominator ≡ {denominator} (mod {self.p}).",
                 f"Extended Euclid: {denominator}⁻¹ ≡ {inverse}; "
                 f"{denominator} · {inverse} mod {self.p} = 1.",
                 f"λ = {numerator} · {inverse} mod {self.p} = {slope}",
                 f"x₃ = ({slope}² − {x1} − {x2}) mod {self.p} = {x3}",
                 f"y₃ = ({slope} · ({x1} − {x3}) − {y1}) mod {self.p} = {y3}",
                 f"Result = ({x3}, {y3})")
        return Addition((x3, y3), slope, case, steps)

    def multiply(self, scalar: int, point: Point) -> Point:
        return self.explain_multiply(scalar, point).result

    def explain_multiply(self, scalar: int, point: Point) -> Multiplication:
        _integer(scalar, "k")
        self.validate_point(point)
        working = self.negate(point) if scalar < 0 else point
        remaining, accumulator, addend = abs(scalar), None, working
        trace = []
        if remaining == 0 or point is None:
            explanation = "0P = O." if remaining == 0 else "Every integer multiple of O is O."
            return Multiplication(scalar, point, working, None, (), explanation)
        while remaining:
            bit = remaining & 1
            before = accumulator
            addition = self.explain_add(accumulator, addend) if bit else None
            if addition is not None:
                accumulator = addition.result
            doubling = self.explain_add(addend, addend)
            trace.append(ScalarStep(len(trace), bit, before, addend, accumulator,
                                    doubling.result, addition, doubling))
            addend = doubling.result
            remaining >>= 1
        explanation = (f"|k| = {abs(scalar)} = {abs(scalar):b}₂. Start R = O, A = "
                       + ("−P." if scalar < 0 else "P."))
        return Multiplication(scalar, point, working, accumulator, tuple(trace), explanation)
