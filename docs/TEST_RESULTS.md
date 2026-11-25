# Verification results

## Executed environments

| Check | Environment | Result |
|---|---|---|
| Complete desktop suite | Linux desktop, Python 3.13.5, Tcl/Tk 8.6 | **23/23 test methods passed; no skips** |
| Mathematical suite | Linux, Python 3.12.14 | **13/13 test methods passed** |
| GUI integration suite | Linux desktop, Python 3.13.5, Tcl/Tk 8.6 | **10/10 test methods passed** |
| Required-example demonstration | Python 3.12.14 | All expected outputs and rejection examples passed |
| Python compilation | `app.py`, `ecc.py`, `demo.py`, both test modules | Passed |
| POSIX launcher syntax | `sh -n run.sh Start_macOS.command` | Passed |

The final combined desktop run completed in 1.244 seconds in this environment. Timings are incidental, not a performance guarantee. Captured evidence is in `all-tests-desktop-log.txt`, `math-test-log.txt`, `gui-test-log.txt`, `test-environment.txt` and `demo-output.txt`.

## Meaningful mathematical coverage

- Exact enumeration compared with an independent nested-loop implementation on **328 nonsingular curves**: every coefficient combination for p=5,7,11,13 excluding singular cases.
- Every point pair checked against a separate geometric addition reference on **172 nonsingular curves** over p=5,7,11. That reference uses Python's independent inverse and the cubic-root-product relation where applicable; some remaining cases use the standard root-sum formula.
- Identity, inverse, closure, commutativity and every associativity triple checked on E₅(1,0), E₇(2,1), E₁₁(1,6) and E₁₇(2,2).
- Primality checked against a sieve for 0…1999 and for the documented largest API prime.
- Euclidean inversion checked exhaustively for values from −m to m−1 at each modulus m=2…69, including expected failures when gcd is not 1.
- Multiplication compared with repeated addition for k=0…60, and corresponding negative scalars, for every point on three small curves.
- Deterministically seeded scalar identities, a 256-bit scalar, binary trace transitions and the supplied verification examples checked.
- Hasse bounds and multiplication by the enumerated group order checked on selected curves.

## Interface/integration coverage

The real-Tk tests check default point counts; identity in menus; malformed/off-curve inputs; composite/singular rejection; preserving the active curve after a rejected edit; normalization; example changes and clearing prior calculations; addition shortcuts; zero tangent; zero, negative and infinity multiples; the 256-bit input boundary; full trace navigation; table selection; complete CSV output; calculation TXT exports; and p=997 enumeration/plotting.

The layout test verifies that top-level operation controls fit at 1080×740 and 1280×840, and that sidebar controls remain mapped. Trace scrollbars are explicitly checked. Programmatic export tests substitute only the filename dialog selection, then execute the application's actual file-writing code. A scalar trace export is checked while viewing its first bit to ensure the entire trace is exported.

Manual desktop checks additionally verified the displayed coordinate list and discrete plot; P+Q=(10,6); 7P=(0,6); a selected binary walkthrough state; visible scrollbars and export controls; and a real native save-dialog operation. The manually saved UTF-8 export was opened from the filesystem and its curve equation and complete trace were confirmed.

## Reproduce

From the extracted project folder on a desktop with Python and Tk:

```sh
python demo.py
python -m unittest discover -s tests -v
```

Use `python3` if that is the Python command on your system. Without Tk or a desktop display, 10 GUI tests deliberately skip; skipped tests do not count as passed GUI verification.

## Verification limits

Live GUI behavior was tested on Linux only. Windows/macOS launchers and instructions are included, but those operating systems were not executed here. Font substitution, high-DPI scaling and native file dialogs may affect platform-specific appearance. The layout checks do not test every possible font/OS scaling combination or every field value. This project has no security audit or constant-time guarantee and is intended for educational use.
