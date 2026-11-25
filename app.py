"""ECC Field Lab — an offline Tkinter teaching application.

Run: python app.py. Mathematical logic is isolated in ecc.py.
"""
import csv
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from ecc import (Curve, ENUMERATION_LIMIT, format_point, parse_integer,
                 parse_point)

BG = "#eef2f6"
CARD = "#ffffff"
INK = "#18283c"
MUTED = "#62748b"
NAVY = "#13263c"
BLUE = "#2369d8"
TEAL = "#008a79"
ORANGE = "#b96512"
BORDER = "#dce4ee"
POINT = "#96a9bf"


class FieldLab(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ECC Field Lab | EECE 455 · Project 13")
        self.geometry("1280x840")
        self.minsize(1080, 740)
        self.configure(bg=BG)
        self.curve = None
        self.points = ()
        self.highlights = {}
        self.plot_positions = []
        self.scalar_trace = None
        self.step_index = -1
        self.active_mode = "explore"
        self.vars = {name: tk.StringVar(value=value) for name, value in
                     (("p", "17"), ("a", "2"), ("b", "2"),
                      ("P", "(5, 1)"), ("Q", "(6, 3)"),
                      ("scalarP", "(5, 1)"), ("k", "7"))}
        self.pick_target = tk.StringVar(value="P")
        self._style()
        self._layout()
        self.bind("<Control-Return>", self._keyboard_calculate)
        self.apply_curve()

    def _style(self):
        self.option_add("*Font", "{DejaVu Sans} 10")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=CARD)
        style.configure("TLabel", background=CARD, foreground=INK)
        style.configure("TButton", padding=(10, 7), font=("DejaVu Sans", 10))
        style.map("TButton", background=[("active", "#e2ebf9")])
        style.configure("Primary.TButton", background=BLUE, foreground="white",
                        borderwidth=0, padding=(12, 9))
        style.map("Primary.TButton", background=[("active", "#1555b6")],
                  foreground=[("active", "white")])
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(13, 11), background="#e6ecf3")
        style.map("TNotebook.Tab", background=[("selected", CARD)],
                  foreground=[("selected", BLUE)])
        style.configure("Treeview", rowheight=29, background=CARD,
                        fieldbackground=CARD, foreground=INK, borderwidth=0)
        style.configure("Treeview.Heading", background="#edf3f9", foreground=MUTED,
                        font=("DejaVu Sans", 9, "bold"), padding=6)
        style.map("Treeview", background=[("selected", "#dceafa")],
                  foreground=[("selected", INK)])
        style.configure("TCombobox", padding=7)
        style.configure("TEntry", padding=7)
        style.configure("TRadiobutton", background=CARD, foreground=INK)

    @staticmethod
    def label(parent, text, size=10, color=INK, bold=False, bg=CARD, **kwargs):
        return tk.Label(parent, text=text, bg=bg, fg=color,
                        font=("DejaVu Sans", size, "bold" if bold else "normal"), **kwargs)

    def _layout(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        side = tk.Frame(self, bg=NAVY, width=238)
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)
        self.label(side, "◉  ECC FIELD LAB", 15, "#ffffff", True, NAVY,
                   anchor="w").pack(fill="x", padx=22, pady=(21, 5))
        self.label(side, "A finite field. Infinite curiosity.", 9, "#a7bad0", bg=NAVY,
                   anchor="w").pack(fill="x", padx=22)
        self.label(side, "EECE 455 / 632   ·   PROJECT 13", 8, "#8ca5c0", bg=NAVY,
                   anchor="w").pack(fill="x", padx=22, pady=(9, 18))
        self.label(side, "01  DEFINE YOUR CURVE", 9, "#9db7d1", True, NAVY,
                   anchor="w").pack(fill="x", padx=22, pady=(0, 8))
        for key, caption in (("p", "Prime modulus p"), ("a", "Coefficient a"),
                             ("b", "Coefficient b")):
            self.label(side, caption, 10, "#e1eaf5", bg=NAVY, anchor="w").pack(
                fill="x", padx=22, pady=(4, 3))
            entry = ttk.Entry(side, textvariable=self.vars[key])
            entry.pack(fill="x", padx=22)
            entry.bind("<Return>", lambda event: self.apply_curve())
        ttk.Button(side, text="Apply curve  →", style="Primary.TButton",
                   command=self.apply_curve).pack(fill="x", padx=22, pady=(12, 6))
        self.label(side, f"Prime 3 < p ≤ {ENUMERATION_LIMIT}\na and b are reduced modulo p.",
                   8, "#a7bad0", bg=NAVY, justify="left", anchor="w").pack(fill="x", padx=22)
        self.curve_error = self.label(side, "", 8, "#ffbead", bg=NAVY,
                                      wraplength=192, justify="left", anchor="w")
        self.curve_error.pack(fill="x", padx=22, pady=8)
        self.label(side, "02  TRY AN EXAMPLE", 9, "#9db7d1", True, NAVY,
                   anchor="w").pack(fill="x", padx=22, pady=(8, 6))
        for title, params in (("Classic · E₁₇(2, 2)", (17, 2, 2)),
                              ("Zero tangent · E₅(1, 0)", (5, 1, 0)),
                              ("Larger field · E₉₇(2, 3)", (97, 2, 3))):
            ttk.Button(side, text=title, command=lambda t=params: self.load_example(*t)).pack(
                fill="x", padx=22, pady=2)
        ttk.Button(side, text="Reset to classic", command=self.reset).pack(
            side="bottom", fill="x", padx=22, pady=(0, 20))
        self.label(side, "OFFLINE  /  EXACT INTEGER MATH\nEducational use · small prime fields", 8,
                   "#8ca5c0", bg=NAVY, justify="left", anchor="w").pack(
                       side="bottom", fill="x", padx=22, pady=(10, 13))

        main = tk.Frame(self, bg=BG)
        main.grid(row=0, column=1, sticky="nsew", padx=24, pady=22)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)
        title = tk.Frame(main, bg=BG)
        title.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.label(title, "Elliptic curves, made tangible.", 24, INK, True, BG,
                   anchor="w").pack(fill="x")
        self.label(title, "Explore the group. Follow the arithmetic. Explain every result.",
                   10, MUTED, bg=BG, anchor="w").pack(fill="x", pady=(7, 0))
        metrics = tk.Frame(main, bg=BG)
        metrics.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        metrics.columnconfigure(0, weight=3)
        metrics.columnconfigure(1, weight=1)
        metrics.columnconfigure(2, weight=1)
        self.equation_label = self._metric(metrics, 0, "ACTIVE CURVE", "", 13)
        self.finite_label = self._metric(metrics, 1, "FINITE POINTS", "", 24)
        self.order_label = self._metric(metrics, 2, "GROUP ORDER · + O", "", 24)

        body = tk.PanedWindow(main, orient="horizontal", bg=BG, bd=0,
                              sashwidth=12, sashrelief="flat")
        body.grid(row=2, column=0, sticky="nsew")
        plot_card = tk.Frame(body, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        tools = tk.Frame(body, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        body.add(plot_card, minsize=330, width=470, stretch="always")
        body.add(tools, minsize=395, width=490, stretch="always")
        plot_card.columnconfigure(0, weight=1)
        plot_card.rowconfigure(2, weight=1)
        self.label(plot_card, "The finite-field plane", 14, bold=True, anchor="w").grid(
            row=0, column=0, sticky="ew", padx=18, pady=(18, 3))
        self.label(plot_card, "Discrete solutions only · click a dot to choose a point", 9,
                   MUTED, anchor="w").grid(row=1, column=0, sticky="ew", padx=18)
        self.canvas = tk.Canvas(plot_card, background=CARD, highlightthickness=0,
                                width=400, height=370)
        self.canvas.grid(row=2, column=0, sticky="nsew", padx=6, pady=8)
        self.canvas.bind("<Configure>", lambda event: self.draw_plot())
        self.canvas.bind("<Button-1>", self.pick_plot_point)
        self.canvas.bind("<Motion>", self.hover_plot)
        self.hover_text = tk.StringVar(value="Move over a dot to inspect its coordinates.")
        self.label(plot_card, "", 9, MUTED, textvariable=self.hover_text,
                   anchor="w", wraplength=400).grid(row=3, column=0, sticky="ew", padx=18, pady=3)
        legend = tk.Frame(plot_card, bg=CARD)
        legend.grid(row=4, column=0, sticky="ew", padx=18, pady=(10, 4))
        for text, color in (("● P / A", BLUE), ("● Q", ORANGE), ("● R", TEAL)):
            self.label(legend, text, 10, color, bold=True).pack(side="left", padx=(0, 18))
        pick = tk.Frame(plot_card, bg=CARD)
        pick.grid(row=5, column=0, sticky="ew", padx=18, pady=(3, 4))
        self.label(pick, "Assign clicked point to:", 9, MUTED).pack(side="left", padx=(0, 8))
        for target in ("P", "Q"):
            ttk.Radiobutton(pick, text=target, variable=self.pick_target, value=target).pack(side="left")
        self.infinity_text = tk.StringVar(value="O is the identity; it has no finite coordinates.")
        self.label(plot_card, "", 9, MUTED, textvariable=self.infinity_text,
                   wraplength=400, justify="left", anchor="w").grid(
                       row=6, column=0, sticky="ew", padx=18, pady=(6, 18))

        self.notebook = ttk.Notebook(tools)
        self.notebook.pack(fill="both", expand=True)
        self.tabs = {}
        for key, name in (("explore", "All points"), ("add", "P + Q"),
                          ("multiply", "k × P"), ("learn", "How it works")):
            tab = ttk.Frame(self.notebook, padding=16)
            self.notebook.add(tab, text=name)
            self.tabs[key] = tab
        self.notebook.bind("<<NotebookTabChanged>>", self.tab_changed)
        self._explore_tab()
        self._addition_tab()
        self._scalar_tab()
        self._learn_tab()
        self.status = tk.StringVar(value="Ready")
        self.label(main, "", 9, MUTED, bg=BG, textvariable=self.status, anchor="w").grid(
            row=3, column=0, sticky="ew", pady=(12, 0))

    def _metric(self, parent, column, caption, initial, size):
        card = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        card.grid(row=0, column=column, sticky="nsew", padx=(0, 10 if column < 2 else 0))
        self.label(card, caption, 8, MUTED, True, anchor="w").pack(fill="x", padx=16, pady=(13, 7))
        value = self.label(card, initial, size, INK, True, anchor="w")
        value.pack(fill="x", padx=16, pady=(0, 14))
        value.bind("<Configure>", lambda event: value.config(wraplength=max(100, event.width-8)))
        return value

    def _text(self, parent, height=1):
        outer = ttk.Frame(parent)
        text = tk.Text(outer, wrap="word", bg="#f5f8fc", fg=INK, bd=0,
                       padx=12, pady=12, font=("DejaVu Sans", 10), height=height,
                       spacing1=3, spacing3=5, insertbackground=INK, width=1)
        bar = ttk.Scrollbar(outer, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        text.configure(state="disabled")
        return outer, text

    @staticmethod
    def set_text(widget, content):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled")

    def _explore_tab(self):
        tab = self.tabs["explore"]
        self.label(tab, "Every solution, one point at a time.", 12, bold=True,
                   anchor="w").pack(fill="x", pady=(0, 7))
        self.point_summary = self.label(tab, "", 9, MUTED, wraplength=420,
                                        justify="left", anchor="w")
        self.point_summary.pack(fill="x", pady=(0, 10))
        container = ttk.Frame(tab)
        container.pack(fill="both", expand=True)
        self.point_table = ttk.Treeview(container, columns=("point", "check"),
                                        show="headings", selectmode="browse", height=5)
        self.point_table.heading("point", text="Point (x, y)")
        self.point_table.heading("check", text="y² = x³ + ax + b mod p")
        self.point_table.column("point", width=130, minwidth=90)
        self.point_table.column("check", width=220, minwidth=130)
        scroll = ttk.Scrollbar(container, orient="vertical", command=self.point_table.yview)
        self.point_table.configure(yscrollcommand=scroll.set)
        self.point_table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.point_table.bind("<<TreeviewSelect>>", self.table_selected)
        row = ttk.Frame(tab)
        row.pack(fill="x", pady=(12, 7))
        ttk.Button(row, text="Use as P", command=lambda: self.use_selected("P")).pack(side="left", padx=(0, 7))
        ttk.Button(row, text="Use as Q", command=lambda: self.use_selected("Q")).pack(side="left")
        ttk.Button(tab, text="Export all points · CSV", command=self.export_points).pack(fill="x", pady=(4, 0))

    def _point_input(self, parent, key, caption):
        self.label(parent, caption, 9, MUTED, anchor="w").pack(fill="x", pady=(7, 4))
        combo = ttk.Combobox(parent, textvariable=self.vars[key], width=20)
        combo.pack(fill="x")
        combo.bind("<Return>", lambda event: self.calculate_add() if key in ("P", "Q") else self.calculate_scalar())
        return combo

    def _result(self, parent):
        frame = tk.Frame(parent, bg="#e7f5f1", padx=12, pady=10)
        frame.pack(fill="x", pady=(12, 8))
        value = self.label(frame, "", 17, TEAL, True, "#e7f5f1", anchor="w")
        value.pack(fill="x")
        return value

    def _addition_tab(self):
        tab = self.tabs["add"]
        self.label(tab, "Add, double, or meet infinity.", 12, bold=True, anchor="w").pack(fill="x")
        fields = ttk.Frame(tab)
        fields.pack(fill="x")
        fields.columnconfigure(0, weight=1)
        fields.columnconfigure(1, weight=1)
        left, right = ttk.Frame(fields), ttk.Frame(fields)
        left.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        right.grid(row=0, column=1, sticky="ew")
        self.p_combo = self._point_input(left, "P", "P · first point (or O)")
        self.q_combo = self._point_input(right, "Q", "Q · second point (or O)")
        actions = ttk.Frame(tab)
        actions.pack(fill="x", pady=(12, 0))
        ttk.Button(actions, text="Compute P + Q", width=13, style="Primary.TButton",
                   command=self.calculate_add).pack(side="left")
        ttk.Button(actions, text="Q = P", width=6, command=self.double_input).pack(side="left", padx=7)
        ttk.Button(actions, text="Q = −P", width=6, command=self.inverse_input).pack(side="left")
        self.add_result = self._result(tab)
        outer, self.add_text = self._text(tab)
        outer.pack(fill="both", expand=True)
        ttk.Button(tab, text="Export calculation · TXT", command=lambda: self.export_trace("add")).pack(
            fill="x", pady=(10, 0))

    def _scalar_tab(self):
        tab = self.tabs["multiply"]
        self.label(tab, "A large multiple. A few binary steps.", 12, bold=True, anchor="w").pack(fill="x")
        fields = ttk.Frame(tab)
        fields.pack(fill="x")
        fields.columnconfigure(0, weight=1)
        fields.columnconfigure(1, weight=1)
        left, right = ttk.Frame(fields), ttk.Frame(fields)
        left.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        right.grid(row=0, column=1, sticky="ew")
        self.scalar_p_combo = self._point_input(left, "scalarP", "P · point (or O)")
        self.label(right, "k · signed, ≤256 bits", 9, MUTED, anchor="w").pack(fill="x", pady=(7, 4))
        entry = ttk.Entry(right, textvariable=self.vars["k"], width=16)
        entry.pack(fill="x")
        entry.bind("<Return>", lambda event: self.calculate_scalar())
        ttk.Button(tab, text="Compute k × P", style="Primary.TButton",
                   command=self.calculate_scalar).pack(fill="x", pady=(12, 0))
        self.scalar_result = self._result(tab)
        self.step_caption = self.label(tab, "", 9, MUTED, anchor="w", wraplength=340)
        self.step_caption.pack(fill="x", pady=(0, 6))
        controls = ttk.Frame(tab)
        controls.pack(fill="x", pady=(0, 8))
        self.back_button = ttk.Button(controls, text="← Previous", width=10, command=lambda: self.change_step(-1))
        self.back_button.pack(side="left")
        self.next_button = ttk.Button(controls, text="Next bit →", width=10, command=lambda: self.change_step(1))
        self.next_button.pack(side="left", padx=7)
        ttk.Button(controls, text="Final result", width=10, command=self.show_scalar_final).pack(side="left")
        outer, self.scalar_text = self._text(tab)
        outer.pack(fill="both", expand=True)
        ttk.Button(tab, text="Export full trace · TXT", command=lambda: self.export_trace("multiply")).pack(
            fill="x", pady=(10, 0))

    def _learn_tab(self):
        tab = self.tabs["learn"]
        self.label(tab, "The mathematics behind the controls", 12, bold=True,
                   anchor="w").pack(fill="x", pady=(0, 8))
        outer, text = self._text(tab, 20)
        outer.pack(fill="both", expand=True)
        self.set_text(text, "1 / THE CURVE\n"
            "Eₚ(a, b): y² ≡ x³ + ax + b (mod p). We use a prime p > 3. "
            "The expression 4a³ + 27b² must be nonzero modulo p. "
            "This excludes singular curves. Coefficients are normalized modulo p; "
            "finite point coordinates must already be in 0…p−1.\n\n"
            "2 / FINDING ALL POINTS\n"
            "Build a dictionary mapping each residue y² mod p to every matching y. "
            "For each x, look up x³ + ax + b mod p. Include both roots, y = 0 where "
            "present, and the separate identity O. Group order = finite points + 1.\n\n"
            "3 / ADDITION\n"
            "For different x coordinates:\nλ = (y₂ − y₁)(x₂ − x₁)⁻¹ mod p.\n"
            "For doubling with y₁ ≠ 0:\nλ = (3x₁² + a)(2y₁)⁻¹ mod p.\n"
            "Then x₃ = λ² − x₁ − x₂ mod p and y₃ = λ(x₁ − x₃) − y₁ mod p. "
            "The inverse is computed by extended Euclid, never floating-point division.\n\n"
            "4 / SPECIAL CASES\nO + P = P. The negative of (x, y) is (x, −y mod p). "
            "P + (−P) = O. Doubling with y = 0 also gives O. O is a group element, "
            "not a dot somewhere outside the plot.\n\n"
            "5 / SCALAR MULTIPLICATION\nStart R = O, A = P. Read |k| in binary from "
            "right to left. If the current bit is 1, set R = R + A. Double A, then "
            "shift k right. For negative k, use −P. The operation count grows with "
            "the number of binary digits rather than |k|.\n\n"
            "6 / READING THE PLOT\nEach dot is a finite-field solution. There is no "
            "continuous real curve here. Click a dot or use the list to fill P or Q. "
            "When tracing multiplication, blue is A and green is R. A label such as "
            "P/R means the points coincide. Dense fields can have overlapping dots; "
            "the coordinate list always contains every point.\n\n"
            "7 / PROJECT SCOPE\nThe three operations above are Project 13. This "
            "application does not implement encryption, ECDH, or signatures. Small "
            "fields and explanatory, variable-time algorithms are for education, "
            "not production cryptographic use.\n\n"
            "Keyboard: Enter applies a field or calculation. Ctrl+Enter computes "
            "the current operation. Tab / Shift+Tab moves between controls.")

    def load_example(self, p, a, b):
        for key, value in (("p", p), ("a", a), ("b", b)):
            self.vars[key].set(str(value))
        self.apply_curve()

    def reset(self):
        self.load_example(17, 2, 2)
        self.notebook.select(self.tabs["explore"])
        self.pick_target.set("P")

    def apply_curve(self):
        """Validate first, then commit state: invalid drafts preserve the active curve."""
        try:
            p, a, b = (parse_integer(self.vars[k].get(), k) for k in ("p", "a", "b"))
            if p > ENUMERATION_LIMIT:
                raise ValueError(f"For enumeration and plotting, use p ≤ {ENUMERATION_LIMIT}.")
            curve = Curve(p, a, b)
            points = curve.enumerate_points()
        except ValueError as error:
            self.curve_error.config(text=str(error))
            self.status.set("Curve not applied. Correct the highlighted input; the active curve is unchanged.")
            return False
        self.curve, self.points = curve, points
        self.curve_error.config(text="")
        for key, value in (("p", curve.p), ("a", curve.a), ("b", curve.b)):
            self.vars[key].set(str(value))
        self.equation_label.config(text=curve.equation)
        self.finite_label.config(text=str(len(points) - 1))
        self.order_label.config(text=str(len(points)))
        self.point_summary.config(text=f"All {len(points)} group elements, including O. "
                                  f"Nonsingularity check: (4a³ + 27b²) mod p = {curve.discriminant} ≠ 0.")
        self.point_table.delete(*self.point_table.get_children())
        for i, point in enumerate(points):
            check = "Identity · no finite coordinates" if point is None else str(point[1] ** 2 % curve.p)
            self.point_table.insert("", "end", iid=str(i), values=(format_point(point), check))
        options = tuple(format_point(pt) for pt in points)
        for combo in (self.p_combo, self.q_combo, self.scalar_p_combo):
            combo.config(values=options)
        default_p = (5, 1) if curve == Curve(17, 2, 2) else points[1]
        default_q = curve.add(default_p, default_p)
        self.vars["P"].set(format_point(default_p))
        self.vars["Q"].set(format_point(default_q))
        self.vars["scalarP"].set(format_point(default_p))
        self.vars["k"].set("7")
        self.scalar_trace = None
        self.step_index = -1
        self.add_calculation = None
        self.add_result.config(text="R = P + Q", fg=TEAL)
        self.scalar_result.config(text="R = k × P", fg=TEAL)
        self.set_text(self.add_text, "Choose P and Q, then compute. You may type coordinates or select from the list.")
        self.set_text(self.scalar_text, "Choose a point and an integer. Compute to reveal the binary double-and-add trace.")
        self.step_caption.config(text="No calculation yet.")
        self.back_button.config(state="disabled")
        self.next_button.config(state="disabled")
        self.highlights = {}
        self.hover_text.set("Move over a dot to inspect its coordinates.")
        self.draw_plot()
        self.status.set(f"Curve applied · {len(points)-1} finite points + O · all arithmetic modulo {curve.p}")
        return True

    def _get_point(self, key):
        point = parse_point(self.vars[key].get())
        self.curve.validate_point(point)
        return point

    def _operation_error(self, widget, label, error):
        label.config(text="Check your input", fg="#b44435")
        self.set_text(widget, str(error))
        self.highlights = {}
        self.draw_plot()
        self.status.set(str(error))

    def calculate_add(self):
        try:
            left, right = self._get_point("P"), self._get_point("Q")
            calculation = self.curve.explain_add(left, right)
        except ValueError as error:
            self.add_calculation = None
            self._operation_error(self.add_text, self.add_result, error)
            return False
        self.add_calculation = calculation
        self.add_result.config(text=f"R = {format_point(calculation.result)}", fg=TEAL)
        self.set_text(self.add_text, f"{calculation.case.upper()}\n\n" + "\n".join(calculation.steps))
        self.highlights = {"P": left, "Q": right, "R": calculation.result}
        self.draw_plot()
        self.status.set(f"{format_point(left)} + {format_point(right)} = {format_point(calculation.result)} · {calculation.case}")
        return True

    def double_input(self):
        self.vars["Q"].set(self.vars["P"].get())
        self.calculate_add()

    def inverse_input(self):
        try:
            self.vars["Q"].set(format_point(self.curve.negate(self._get_point("P"))))
        except ValueError as error:
            self.add_calculation = None
            self._operation_error(self.add_text, self.add_result, error)
            return
        self.calculate_add()

    def calculate_scalar(self):
        try:
            point = self._get_point("scalarP")
            k = parse_integer(self.vars["k"].get(), "k", 78)
            if k.bit_length() > 256:
                raise ValueError("For a readable trace, use |k| < 2²⁵⁶.")
            trace = self.curve.explain_multiply(k, point)
        except ValueError as error:
            self.scalar_trace = None
            self.step_index = -1
            self.step_caption.config(text="No valid calculation.")
            self.back_button.config(state="disabled")
            self.next_button.config(state="disabled")
            self._operation_error(self.scalar_text, self.scalar_result, error)
            return False
        self.scalar_trace = trace
        self.step_index = -1
        scalar_label = str(k) if len(str(k)) <= 12 else "k"
        self.scalar_result.config(text=f"{scalar_label} × P = {format_point(trace.result)}", fg=TEAL)
        self.set_text(self.scalar_text, trace.as_text())
        self.show_scalar_final()
        self.status.set(f"{k} × {format_point(point)} = {format_point(trace.result)} · "
                        f"{len(trace.steps)} binary iterations")
        return True

    def show_scalar_final(self):
        trace = self.scalar_trace
        if not trace:
            return
        self.step_index = -1
        self.highlights = {"P": trace.original_point, "R": trace.result}
        self.step_caption.config(text=f"Final result · {len(trace.steps)} bits processed. "
                                 "Next bit starts the walkthrough.")
        self.back_button.config(state="disabled")
        self.next_button.config(state="normal" if trace.steps else "disabled")
        self.set_text(self.scalar_text, trace.as_text())
        self.draw_plot()

    def change_step(self, direction):
        trace = self.scalar_trace
        if not trace or not trace.steps:
            return
        self.step_index = max(0, min(len(trace.steps) - 1, self.step_index + direction))
        s = trace.steps[self.step_index]
        self.highlights = {"A": s.addend, "R": s.accumulator_after}
        self.step_caption.config(text=f"Bit {s.index} of {len(trace.steps)-1} = {s.bit} · "
                                 f"R: {format_point(s.accumulator_before)} → {format_point(s.accumulator_after)}")
        lines = [f"ITERATION {s.index+1} / {len(trace.steps)}", f"Binary digit: {s.bit}",
                 f"Current addend A = {format_point(s.addend)}", ""]
        lines.extend(s.addition.steps if s.addition else ("Bit 0: skip R + A; R stays unchanged.",))
        lines.extend(("", "DOUBLE A for the next bit:", *s.doubling.steps))
        self.set_text(self.scalar_text, "\n".join(lines))
        self.back_button.config(state="normal" if self.step_index > 0 else "disabled")
        self.next_button.config(state="normal" if self.step_index < len(trace.steps)-1 else "disabled")
        self.draw_plot()

    def _keyboard_calculate(self, event=None):
        if self.active_mode == "add":
            self.calculate_add()
        elif self.active_mode == "multiply":
            self.calculate_scalar()
        else:
            self.apply_curve()
        return "break"

    def tab_changed(self, event=None):
        selected = self.notebook.select()
        self.active_mode = next((key for key, tab in self.tabs.items() if str(tab) == selected), "explore")
        # Avoid displaying highlights from a different calculation mode.
        self.highlights = {}
        self.draw_plot()

    def table_selected(self, event=None):
        selected = self.point_table.selection()
        if selected:
            self.highlights = {"P": self.points[int(selected[0])]}
            self.draw_plot()

    def use_selected(self, target):
        selected = self.point_table.selection()
        if not selected:
            self.status.set("Select a point in the list first.")
            return
        self.assign_point(self.points[int(selected[0])], target)

    def assign_point(self, point, target):
        self.vars[target].set(format_point(point))
        if target == "P":
            self.vars["scalarP"].set(format_point(point))
        self.highlights = {target: point}
        self.draw_plot()
        self.status.set(f"{target} set to {format_point(point)}. Compute to update the operation result.")

    def draw_plot(self):
        if not self.curve:
            return
        c = self.canvas
        c.delete("all")
        width, height = max(c.winfo_width(), 100), max(c.winfo_height(), 100)
        size = max(20, min(width - 82, height - 65))
        left = (width - size) / 2 + 12
        top = max(16, (height - size - 35) / 2)
        p = self.curve.p
        def position(point):
            return left + point[0] * size / (p - 1), top + size - point[1] * size / (p - 1)
        tick_step = 1 if p <= 23 else max(1, (p - 1) // 5)
        ticks = sorted(set(range(0, p, tick_step)) | {p - 1})
        for t in ticks:
            x, y = position((t, t))
            c.create_line(x, top, x, top + size, fill="#edf2f7")
            c.create_line(left, y, left + size, y, fill="#edf2f7")
            # On a small canvas, retain all grid lines but reduce number labels.
            if p > 23 or t % (1 if size >= 380 else 2) == 0 or t == p - 1:
                c.create_text(x, top + size + 17, text=str(t), fill=MUTED, font=("DejaVu Sans", 8))
                c.create_text(left - 14, y, text=str(t), fill=MUTED, font=("DejaVu Sans", 8))
        c.create_rectangle(left, top, left + size, top + size, outline="#c9d5e4")
        c.create_text(left + size + 22, top + size, text="x", fill=MUTED)
        c.create_text(left, top - 11, text="y", fill=MUTED)
        radius = 4.5 if p <= 31 else 3 if p <= 101 else 1.8
        self.plot_positions = []
        for point in self.points[1:]:
            x, y = position(point)
            self.plot_positions.append((x, y, point))
            c.create_oval(x-radius, y-radius, x+radius, y+radius, fill=POINT, outline="")
        grouped = {}
        infinity_roles = []
        for role, point in self.highlights.items():
            if point is None:
                infinity_roles.append(role)
            else:
                grouped.setdefault(point, []).append(role)
        for point, roles in grouped.items():
            x, y = position(point)
            color = TEAL if "R" in roles else ORANGE if "Q" in roles else BLUE
            c.create_oval(x-8, y-8, x+8, y+8, fill=CARD, outline=color, width=2)
            c.create_oval(x-4, y-4, x+4, y+4, fill=color, outline="")
            label_x, anchor = (x-12, "e") if x > left + size * .75 else (x+12, "w")
            label_y = y-14 if y > top+20 else y+15
            c.create_text(label_x, label_y, anchor=anchor,
                          text="/".join(roles) + " " + format_point(point),
                          fill=color, font=("DejaVu Sans", 9, "bold"))
        self.infinity_text.set(("O · " + ", ".join(infinity_roles) + " at infinity. ")
                               if infinity_roles else "O is the identity; it has no finite coordinates.")

    def _near_point(self, event):
        if not self.plot_positions:
            return None
        x, y, point = min(self.plot_positions,
                         key=lambda item: (item[0]-event.x)**2 + (item[1]-event.y)**2)
        return point if (x-event.x)**2 + (y-event.y)**2 <= 100 else None

    def hover_plot(self, event):
        point = self._near_point(event)
        self.hover_text.set(f"{format_point(point)} · y² mod p = {point[1]**2 % self.curve.p}" if point is not None
                            else "Move over a dot to inspect its coordinates.")
        self.canvas.configure(cursor="hand2" if point is not None else "")

    def pick_plot_point(self, event):
        point = self._near_point(event)
        if point is not None:
            self.assign_point(point, self.pick_target.get())

    def export_points(self):
        path = filedialog.asksaveasfilename(parent=self, title="Export every curve point",
                    defaultextension=".csv", initialfile=f"curve_{self.curve.p}_{self.curve.a}_{self.curve.b}_points.csv",
                    filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            self.write_points(path)
        except OSError as error:
            messagebox.showerror("Could not save", str(error), parent=self)
            return
        self.status.set(f"Exported {len(self.points)} points to {Path(path).name}")

    def write_points(self, path):
        with open(path, "w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow(("p", "a", "b", "point", "x", "y", "is_infinity"))
            for point in self.points:
                writer.writerow((self.curve.p, self.curve.a, self.curve.b, format_point(point),
                                 "" if point is None else point[0], "" if point is None else point[1],
                                 point is None))

    def export_trace(self, mode):
        if mode == "add":
            calculation = getattr(self, "add_calculation", None)
            trace = "\n".join(calculation.steps) if calculation else None
        else:
            trace = self.scalar_trace.as_text() if self.scalar_trace else None
        if trace is None:
            self.status.set("Compute a valid result before exporting its calculation.")
            return
        path = filedialog.asksaveasfilename(parent=self, title="Export mathematical trace",
                    defaultextension=".txt", initialfile=f"ecc_{mode}_trace.txt",
                    filetypes=[("Text files", "*.txt")])
        if path:
            try:
                Path(path).write_text(self.curve.equation + "\n\n" + trace + "\n", encoding="utf-8")
                self.status.set(f"Saved trace to {Path(path).name}")
            except OSError as error:
                messagebox.showerror("Could not save", str(error), parent=self)


def main():
    try:
        app = FieldLab()
    except tk.TclError as error:
        print("The graphical interface could not start. A desktop display and Tk are required.\n"
              "Try 'python -m tkinter' to check your Python/Tk installation.\n"
              f"Details: {error}", file=sys.stderr)
        return 1
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
