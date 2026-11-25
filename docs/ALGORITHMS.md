# Understanding and explaining the implementation

## 1. The mathematical objects

We work in the finite field F_p, where p is prime and p > 3. The curve consists of pairs satisfying

**y² ≡ x³ + ax + b (mod p)**

and a separate identity element **O**, called the point at infinity. A finite point is a Python tuple `(x, y)`; O is `None`. `format_point` displays `None` as `O`. Using a separate object prevents confusion between infinity and the valid finite point `(0, 0)` on some curves.

`Curve` is an immutable dataclass. Construction checks integer types, the supported p range, primality, and nonsingularity. It normalizes a and b modulo p. The expression `(4a³ + 27b²) mod p` must be nonzero. The actual Weierstrass discriminant is −16 times this expression; since p > 3, the nonzero checks are equivalent. The `discriminant` property is explicitly documented as the simplified nonsingularity expression.

`contains` accepts O or a canonical finite point. It checks both coordinate bounds and the equation. Public group operations validate their inputs even for shortcuts such as `0P`, so malformed points cannot pass silently.

## 2. Exact inversion by extended Euclid

Ordinary division is inappropriate in a finite field. Dividing by d means multiplying by the unique integer d⁻¹ satisfying `d*d⁻¹ ≡ 1 mod p`, for nonzero d.

`inverse_mod` runs extended Euclid on p and `d mod p`. It maintains remainders and their coefficients of d. At termination, if the gcd is 1, the final coefficient modulo p is the inverse. Otherwise it raises an error.

Example: `2⁻¹ mod 17 = 9`, because `2*9 = 18 ≡ 1 mod 17`. No operation in `ecc.py` uses floating-point arithmetic. Integer `//` is used only to compute Euclidean quotients.

## 3. Enumerating all points

A naive reference method tries p² coordinate pairs. The application instead:

1. For each y in `0…p−1`, append y to `residues[y*y % p]`.
2. For each x in `0…p−1`, compute `rhs = (x³ + ax + b) % p`.
3. Emit `(x, y)` for **every** y stored under that rhs.
4. Include O separately, first in the returned tuple.

Every valid pair is found because every field x and every field y is represented in these loops. Non-solutions are excluded by equality of the residues. A residue may have two roots, one root y=0, or no roots. We store all roots and never count y=0 twice. The loop order makes finite points lexicographically sorted without a separate sort.

This takes O(p + N) elementary field operations and O(p + N) storage including the output, where N is the number of finite points. The GUI bounds p at 997. The exact count is obtained by enumeration, not estimated by a formula.

For E₁₇(2,2), the finite points are:

```
(0,6)   (0,11)  (3,1)   (3,16)  (5,1)   (5,16)
(6,3)   (6,14)  (7,6)   (7,11)  (9,1)   (9,16)
(10,6)  (10,11) (13,7)  (13,10) (16,4)  (16,13)
```

There are 18 finite points, and **19 group elements** after adding O.

## 4. Addition: decide the case before inverting

`explain_add(P,Q)` returns an immutable `Addition` object containing the result, slope (if defined), case name, and readable steps. `add` returns just its result. They share the same arithmetic, avoiding inconsistent educational explanations.

Decision order matters:

1. If either operand is O, return the other. This includes O + O = O.
2. If x₁ = x₂ and `(y₁+y₂) mod p = 0`, return O. This covers both inverse pairs and doubling a point with y=0; no inverse of zero is attempted.
3. If P=Q with nonzero y, use the doubling slope.
4. Otherwise use the ordinary addition slope. For valid points with equal x, the previous cases already cover all possibilities.

For distinct x coordinates:

**λ ≡ (y₂−y₁)(x₂−x₁)⁻¹ mod p**

For doubling:

**λ ≡ (3x₁²+a)(2y₁)⁻¹ mod p**

In both cases:

**x₃ ≡ λ²−x₁−x₂ mod p**

**y₃ ≡ λ(x₁−x₃)−y₁ mod p**

All intermediate residues and outputs use `% p`. A modular inverse is computed only after zero-denominator cases have been excluded.

### Worked example: double P=(5,1) on E₁₇(2,2)

- Numerator: `(3*5²+2) mod 17 = 77 mod 17 = 9`.
- Denominator: `2*1 mod 17 = 2`; its inverse is 9.
- Slope: `9*9 mod 17 = 13`.
- x₃: `(13²−5−5) mod 17 = 159 mod 17 = 6`.
- y₃: `(13*(5−6)−1) mod 17 = −14 mod 17 = 3`.
- Therefore **2P=(6,3)**.

For `P+(6,3)`, λ = 2, giving x₃=10 and y₃=6. The inverse of P is `(5,16)`, and adding that inverse gives O. On E₅(1,0), `(0,0)` is a finite point whose double is O.

## 5. Multiplication: binary double-and-add

`explain_multiply(k,P)` returns a `Multiplication` object and a tuple of `ScalarStep` records. Each record captures the bit index/value, accumulator before and after, current addend, next addend, and the complete addition/doubling explanations. `multiply` returns the final point.

For negative k, replace P by −P and process |k|. For k=0 or P=O, return O immediately.

```
R = O
A = working point
n = |k|
while n > 0:
    if n & 1:
        R = R + A
    A = A + A
    n = n >> 1
return R
```

At bit i, A represents `2^i * working_point`; R contains the contributions from all previously processed 1 bits. If the next bit is 1, add that contribution. Doubling prepares A for the next bit. Equivalently, the invariant is `R + nA = |k| * working_point` at each iteration boundary. Shifting n halves its remaining binary representation. When n=0, the invariant gives the required result.

For k≠0 and finite P, the code performs `bit_length(|k|)` doublings and `popcount(|k|)` accumulator additions. It deliberately doubles once on the final iteration to match the supplied pseudocode; that last doubled addend is not used afterward. There is no scalar reduction by group order and no precomputed-answer lookup.

### Worked example: 7P

`7 = 111₂`. Bits are processed from **right to left**.

| Bit index | Bit | Current A | R before | R after | Doubled A |
|---|---|---|---|---|---|
| 0 | 1 | (5,1) | O | (5,1) | (6,3) |
| 1 | 1 | (6,3) | (5,1) | (10,6) | (3,1) |
| 2 | 1 | (3,1) | (10,6) | (0,6) | (13,7) |

Thus **7P=(0,6)**. The final doubled A=(13,7) is 8P; it is not the answer.

Arithmetic work is O(log |k|) group operations for nonzero k. One group operation requires an extended-Euclid inverse, with O(log p) Euclidean iterations; integer bit costs grow with operand size. The educational trace stores O(log |k|) records. This is a variable-time teaching implementation, not a constant-time cryptographic library.

## 6. How the application is organized

| Component | Responsibility |
|---|---|
| `Curve`, `inverse_mod`, parsers | Exact validated arithmetic; no GUI imports |
| `Addition`, `Multiplication`, `ScalarStep` | Structured mathematical results and explanations |
| `FieldLab._layout` and tab builders | Widgets, layout and styling |
| `apply_curve` | Validate proposed parameters, enumerate, then replace active state atomically |
| `calculate_add` / `calculate_scalar` | Parse inputs, call mathematical core, render result and errors |
| `draw_plot` | Convert discrete coordinates to Canvas pixels and overlay P/Q/R/A |
| `change_step` / `show_scalar_final` | Navigate recorded calculations without recomputing a different algorithm |
| `write_points` / `export_trace` | Save complete active-curve data in portable formats |

The GUI's `curve` and `points` are committed together after successful validation. Rejected curve drafts do not partially update the application. Switching curves clears old operation results, menus and highlights. Plot points come from enumeration, not from visual interpolation or a continuous real curve.

## 7. Why the tests provide useful evidence

- The residue-map enumerator is checked against a separate O(p²) nested-loop oracle on **all nonsingular curves** for p=5,7,11,13.
- Addition is checked for every pair on all nonsingular curves for p=5,7,11 using a geometric reference. The reference uses Python's independent modular inverse and a cubic-root-product identity when possible; remaining geometric cases share standard formulas. This is strong cross-checking, not a fully independent formal proof.
- The actual implementation's operation tables are checked for identity, inverse, closure, commutativity and every associativity triple on four small curves.
- Scalars are checked against repeated addition, negative-point symmetry, scalar distributivity, trace consistency, and a 256-bit example.
- GUI tests use real Tk widgets to check active-state preservation, exports, special cases, example changes, trace navigation and control visibility at two window sizes.

These checks supplement the mathematical reasoning above. They cannot establish production security or exhaustively verify every possible parameter.
