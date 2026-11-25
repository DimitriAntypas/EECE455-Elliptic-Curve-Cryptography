# Requirement traceability

Authority: the uploaded `Project_13_ECC_ChatGPT_Source.docx`, copied unmodified as `Project_Source.docx`. Section 1 reproduces the assignment wording and GUI guidance. The original project-list PDF itself was not supplied, so this implementation relies on that source brief rather than claiming independent inspection of the original handout.

Exact assignment wording in the supplied brief:

> “Given an Elliptic Curve Eₚ(a, b), write code to find all points on the curve, add two points on the curve and multiply a point by a scalar.”

The brief also states that general project guidance calls for a user-friendly educational GUI. Sections 2–8 are proposed implementation guidance, rather than additional professor mandates.

| Requirement or proposed criterion | Implementation | Verification |
|---|---|---|
| Find all points | `Curve.enumerate_points`; table and scatter plot; O included | Required count; independent brute-force reference for all nonsingular curves over p=5,7,11,13 |
| Add two points | `Curve.add` / `explain_add`; P+Q panel | Supplied examples; inverse, identity, tangent; reference and group-law tests |
| Multiply by a scalar | `Curve.multiply` / `explain_multiply`; k×P panel | Supplied examples; repeated addition; zero, infinity, negatives and large scalar tests |
| User-friendly educational GUI | Python/Tkinter; plotted points; worked traces; binary-step navigation; presets | Manual desktop checks and 10 real-Tk test methods |
| Prime field p>3; normalize a,b | Immutable `Curve` validation | Prime sieve comparison; invalid types/values; normalization tests |
| Reject singular curves | Nonzero `(4a³+27b²) mod p` | Singular example rejected in core and GUI |
| Canonical finite coordinates; O separate | Tuple or `None`; `contains` and parsers | Off-curve, malformed, out-of-range and infinity tests |
| All roots, including y=0 | Quadratic residue dictionary of lists | Independent enumeration and zero-tangent tests |
| Extended Euclidean inverse | `inverse_mod`, integer-only | Exhaustive small-modulus gcd checks and independent inverse comparison |
| Show modular calculations | `Addition.steps` | Trace-content and scalar-step consistency checks; manual visual review |
| Integer multiplication including k≤0 | Binary double-and-add and −P for negatives | Example results and repeated addition over positive/negative scalars |
| Responsive documented small-prime limit | GUI/enumeration p≤997; 256-bit GUI scalar bound | Largest GUI field and input-bound tests |
| Readable validation and reset | Inline messages; atomic curve apply; reset/presets | Error/recovery and example-state tests |
| No internet dependency | Standard-library-only desktop application | No runtime network code or remote assets |
| Runnable complete source, tests, README | Root source, launchers, `tests/`, README and learning documents | Executed code and provided package |

## Scope choices

- Python with Tkinter follows the source's default recommendation. It is not represented as a professor-mandated language.
- Enumeration and plotting are deliberately restricted to prime p≤997; all points are found for every accepted GUI curve. A clear error is shown outside this range.
- The mathematical API supports arithmetic on larger prime fields up to 2,147,483,647, with the same enumeration limit. Trial-division primality is deterministic within that documented bound.
- The GUI accepts arbitrary signed decimal scalars within |k|<2²⁵⁶; the API is not fixed to that scalar bound.
- TXT/CSV exports and binary walkthrough navigation are small educational conveniences.
- No encryption, ECDH, ECDSA, invented grading rubric, formal report or presentation has been added. The Markdown documents are implementation/demo learning notes.
