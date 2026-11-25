# Demonstration and group preparation

## Before class

Extract the folder, confirm `python app.py` opens a window, and run `python demo.py`. Check the laptop's display scaling and read the formula walkthrough in `ALGORITHMS.md`. The application needs no Wi-Fi. Keep a terminal open in the project folder so you can run the test suite if asked.

A suggested division of explanation is: curve validation/enumeration; Euclidean inversion/addition; scalar multiplication/traces; GUI/testing. Adapt this to your actual group and contributions. Do not claim work or testing that your group has not personally reviewed.

## A 5–7 minute demonstration

### 1. Introduce the scope (30 seconds)

“Our project implements three operations over a finite prime field: enumerating elliptic-curve points, adding them, and multiplying a point by an integer. The mathematics is separate from the interface in `ecc.py`.”

Start with the classic preset E₁₇(2,2). Explain the equation and why a prime p and a nonsingular curve are needed.

### 2. Show every point (45 seconds)

Open **All points**. Show **18 finite points** and **group order 19**. Point out the O row and explain why it is not plotted. The graph contains isolated finite-field solutions rather than a continuous real curve. Select a table point and use **Use as P**; demonstrate that the point menu is editable too.

### 3. Explain addition and doubling (90 seconds)

Reset to classic. Open **P + Q**. With P=(5,1), Q=(6,3), compute **R=(10,6)**. Read the slope and modular inverse steps.

Select **Q = P** to obtain **(6,3)**. Explain why doubling needs a tangent slope. Use the complete calculation in `ALGORITHMS.md` if asked to derive λ=13.

Select **Q = −P**. Explain **P+(5,16)=O** and why no division by zero occurs. Type O for P to show the identity rule.

### 4. Walk through multiplication (90 seconds)

Reset to classic and select **k × P**. P=(5,1), k=7 gives **(0,6)**. Explain `7=111₂` and read the bits right to left. Press **Next bit** three times. Show R progressing through `(5,1)`, `(10,6)`, `(0,6)` while A doubles.

Clarify that the green card keeps the final answer; the step caption and plot show the selected intermediate state. Select **Final result** to restore the full trace.

Try k=0 → O; k=19 → O; k=−1 → (5,16). Explain that −k is handled by negating P, not by a separate multiplication formula.

### 5. Show safeguards and the other special case (60 seconds)

- Enter p=15 and apply: the modulus is rejected; the active curve is preserved.
- Enter p=17, a=0, b=0: singular curve rejected.
- Reset; type (1,1) as an addition input: point rejected.
- Choose **Zero tangent · E₅(1,0)**. In addition, enter P=Q=(0,0): result O because y=0.

### 6. Close with implementation evidence (45 seconds)

Export a point CSV or full calculation trace. Run `python -m unittest discover -s tests -v` in the project folder. On a desktop with Tk, all 23 test methods should run. Describe the independent enumeration oracle and the exhaustive small-curve group-law tests.

## Questions everyone should be able to answer

| Question | Essential answer |
|---|---|
| Why require a prime modulus? | Every nonzero field element then has a multiplicative inverse. |
| Why p > 3? | This project uses the standard short Weierstrass form and its formulas in characteristic greater than 3. |
| Why reject 4a³+27b²=0 mod p? | The curve is singular, outside the nonsingular elliptic-curve group used by these formulas. |
| Why is O `None` rather than (0,0)? | O has no affine coordinates; (0,0) can itself be a valid finite point. |
| Why do you include O when enumerating? | It is the identity required to complete the group. |
| Can two points share the same x? | Yes; their y values are opposites modulo p, except the single root y=0. |
| Why not use ordinary division? | The slope is a field element: multiply by an integer modular inverse. |
| What prevents inversion of zero? | Identity and inverse-pair/y=0 cases are checked before computing a slope. |
| Why does binary multiplication work? | Each A is a power-of-two multiple; R accumulates precisely the set-bit contributions. |
| Why not multiply x and y by k? | Scalar multiplication is repeated **group addition**, not coordinate-wise multiplication. |
| How are negative k handled? | Work with |k| and −P=(x,−y mod p). |
| Why the p=997 GUI limit? | Enumeration, menus and plotting are kept small enough for an interactive educational demonstration. |
| Is the graph a real elliptic curve? | It is the finite set of solutions in F_p²; real-valued curve geometry is not drawn. |
| Can this encrypt a message? | Encryption is outside this Project 13 scope. The app demonstrates group arithmetic. |
| Are these realistic security parameters? | No; small fields and variable-time traceable algorithms are chosen for learning. |
| What was tested on Windows/macOS? | Launchers and instructions are provided; live execution was tested on Linux only. |

## If something goes wrong

- No window: check `python -m tkinter` and use a desktop session.
- A different Python is selected: use `py -3 app.py` on Windows or `python3 app.py` on macOS/Linux.
- Clipped window at high OS scaling: reduce scaling or use a larger display; minimum is 1080×740 logical pixels.
- Formula output seems inconsistent after editing: recompute the operation. The displayed result/export corresponds to the last successful calculation, not unsubmitted input changes.
- Dense plot: use the point list for precise selection; it always retains all points.
