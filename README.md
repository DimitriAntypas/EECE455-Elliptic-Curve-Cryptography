# ECC Field Lab

**EECE 455/632 · Project 13 · Elliptic Curve Cryptography**

An offline desktop application for exploring short Weierstrass elliptic curves over finite prime fields. It implements the three operations in the supplied project brief: **find all points, add two points, and multiply a point by an integer**, with an educational graphical interface.

## Start here

1. Extract the entire ZIP to a normal folder. Do not run it from inside the ZIP.
2. Install **Python 3.10 or newer with Tk support** if Python is not already installed. No pip packages are needed.
3. Open a terminal in the extracted `EECE455_ECC_Lab` folder and run:

   ```sh
   python app.py
   ```

   On macOS/Linux the command may be `python3 app.py`.

Windows users can also double-click **Start_Windows.bat**. macOS users can use **Start_macOS.command**; if it is not executable, run `chmod +x Start_macOS.command` once. Linux users can use `sh run.sh`. These launchers run the same source code; this is not a compiled executable.

To check Tk independently, run `python -m tkinter` (or `python3 -m tkinter`). A small demonstration window should open. On Debian/Ubuntu, install the system package `python3-tk` if Tk is missing. On Windows/macOS, use a Python installer that includes Tcl/Tk. A desktop display is required: notebooks, SSH sessions without graphical forwarding, and displayless servers cannot show the GUI.

The default window is 1280 × 840; the minimum supported window is 1080 × 740 logical pixels. At high operating-system display scaling, a larger physical screen may be needed. Fonts and native file dialogs can differ by platform.

## What is included

| File | Purpose |
|---|---|
| `app.py` | Tkinter interface, discrete Canvas plot, input handling, trace navigation, exports |
| `ecc.py` | Exact curve arithmetic, Euclidean inverse, enumeration, addition and double-and-add |
| `tests/test_ecc.py` | Independent mathematical checks and supplied examples |
| `tests/test_gui.py` | Real-Tk interface/controller, layout, error-recovery and CSV tests |
| `demo.py` | Headless verification of the supplied examples |
| `START_HERE.html` | Friendly offline project overview; open in any browser |
| `docs/ALGORITHMS.md` | Formulas, invariants, worked calculations and code walkthrough |
| `docs/DEMO.md` | A demonstration script and questions the group should be able to answer |
| `docs/REQUIREMENTS.md` | Traceability to the uploaded brief and documented scope |
| `docs/TEST_RESULTS.md` | Actual test environment, results and limitations |
| `docs/*-test-log.txt` | Captured successful test output |
| `docs/Project_Source.docx` | Unmodified copy of the supplied project source brief |

## Using the application

**Define the curve.** Enter prime `p`, and integer coefficients `a`, `b`, then select **Apply curve**. Coefficients are reduced modulo `p`. Composite moduli, `p ≤ 3`, singular curves, and fields above the GUI limit are rejected with a readable explanation. Invalid drafts preserve the currently active curve; the active equation remains visible.

**All points.** The coordinate table contains every point, including `O` on its own row. The graph plots only finite points. The finite count and total group order are shown separately. Click a dot or select a row and use **Use as P/Q**. Choosing P also fills the scalar-multiplication point. Select O from the list or type `O`; infinity has no finite plot location.

**P + Q.** Select from the editable point menus, or type `(x, y)` / `x,y` / `O`. Press **Compute P + Q**. **Q = P** computes doubling; **Q = −P** computes the inverse-pair case. The trace gives the slope, modular inverse check and result coordinates, or explains a special case. P, Q and R are highlighted; a combined label indicates coincident points.

**k × P.** Enter a signed decimal scalar and a valid point. Compute to see the full double-and-add trace. **Next bit** walks through the binary digits from least significant to most significant; **Previous** moves back. During a step, blue A is the current addend and green R is the accumulator *after* that bit. The panel separately explains doubling A for the next iteration. **Final result** restores the full trace. The green result card always contains the final result, even during the walkthrough.

**Exports.** Export every group element as CSV or an operation's full trace as UTF-8 text. Infinity is explicitly flagged in CSV with empty x/y fields. Switching curves clears calculation results. Exports describe the last successfully computed operation on the active curve; after editing inputs, compute again to update that operation.

**Keyboard.** Tab/Shift+Tab moves through controls. Enter applies curve fields or computes point/scalar fields. Ctrl+Enter computes the selected operation. Use the draggable divider to adjust the plot and calculation panel widths.

## Verification commands

From the project folder:

```sh
python demo.py
python -m unittest tests.test_ecc -v
python -m unittest discover -s tests -v
```

Use `python3` instead if needed. The full suite contains **23 test methods**. All 23 passed in the tested Linux desktop environment. Without Tk or a display, the 10 GUI tests explicitly skip; the 13 mathematical tests still run. The skip is not a GUI pass. Tests do not require internet access.

## Deliberate bounds

- GUI enumeration/plotting: prime **3 < p ≤ 997**, so the coordinate list and graph remain responsive. Larger fields can create overlapping dots; the complete list and counts remain authoritative.
- The mathematical `Curve` API accepts primes up to **2,147,483,647** using deterministic trial division. Its enumeration method retains the 997 limit. Arithmetic on supplied valid points does not require enumeration.
- GUI scalar inputs: **|k| < 2²⁵⁶**. The core API has no fixed scalar bound; the number of iterations is the bit length of |k|, except the zero/infinity shortcuts. It retains a trace, so memory also grows with bit length.
- Coefficients normalize modulo p. Finite point coordinates must already lie in `0…p−1`; off-curve or out-of-range coordinates are rejected rather than silently changed.
- Educational arithmetic is variable-time and uses deliberately small fields. This is **not production cryptographic software**.

The supplied brief gives no mandatory programming language, submission format, report, presentation, deadline or rubric. The package follows its Python/Tkinter recommendation and includes learning documentation; it does not invent additional submission requirements.
