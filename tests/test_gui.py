"""Real-Tk integration tests. Skipped explicitly without a graphical display.

These exercise the actual widgets/controller with real mathematics. Run on a
normal desktop with `python -m unittest tests.test_gui -v`.
"""
import csv
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
try:
    import tkinter as tk
    from app import FieldLab, TEAL
except ImportError:
    tk = None


def display_available():
    if tk is None:
        return False
    try:
        root = tk.Tk()
        root.destroy()
        return True
    except tk.TclError:
        return False


@unittest.skipUnless(display_available(), "Tk or a graphical desktop display is unavailable")
class GuiTests(unittest.TestCase):
    def setUp(self):
        self.app = FieldLab()
        self.errors = []
        self.app.report_callback_exception = lambda *args: self.errors.append(args)
        self.app.update()

    def tearDown(self):
        self.app.destroy()
        self.assertEqual(self.errors, [], "An uncaught Tk callback exception occurred")

    def select_mode(self, name):
        self.app.notebook.select(self.app.tabs[name])
        self.app.update()

    def test_default_curve_and_list(self):
        a = self.app
        self.assertEqual(len(a.points), 19)
        self.assertEqual(len(a.point_table.get_children()), 19)
        self.assertEqual(a.finite_label.cget("text"), "18")
        self.assertEqual(a.order_label.cget("text"), "19")
        self.assertEqual(a.point_table.item("0", "values")[0], "O")
        self.assertEqual(len(a.plot_positions), 18)
        for mode, widget in (("add", a.add_text), ("multiply", a.scalar_text)):
            self.select_mode(mode)
            scrollbar = [c for c in widget.master.winfo_children() if c is not widget][0]
            self.assertTrue(scrollbar.winfo_ismapped())
            self.assertGreater(scrollbar.winfo_width(), 8)

    def test_apply_invalid_curve_is_transactional(self):
        a = self.app
        old_curve, old_points = a.curve, a.points
        for p, aa, b in (("15", "2", "2"), ("17", "0", "0"),
                          ("1009", "2", "2"), ("oops", "2", "2")):
            for key, value in (("p", p), ("a", aa), ("b", b)):
                a.vars[key].set(value)
            self.assertFalse(a.apply_curve())
            self.assertEqual(a.curve, old_curve)
            self.assertEqual(a.points, old_points)
            self.assertTrue(a.curve_error.cget("text"))
        a.reset()
        self.assertEqual(a.curve_error.cget("text"), "")

    def test_normalization_and_example_switch_clear_state(self):
        a = self.app
        a.vars["a"].set("-15")
        a.vars["b"].set("36")
        self.assertTrue(a.apply_curve())
        self.assertEqual(a.vars["a"].get(), "2")
        a.calculate_scalar()
        a.load_example(97, 2, 3)
        self.assertEqual(a.curve.p, 97)
        self.assertIsNone(a.scalar_trace)
        self.assertEqual(a.highlights, {})
        self.assertIn("O", a.p_combo.cget("values"))

    def test_addition_buttons_and_error_recovery(self):
        a = self.app
        self.select_mode("add")
        self.assertTrue(a.calculate_add())
        self.assertEqual(a.add_calculation.result, (10, 6))
        a.double_input()
        self.assertEqual(a.add_calculation.result, (6, 3))
        a.inverse_input()
        self.assertIsNone(a.add_calculation.result)
        self.assertIn("R", a.infinity_text.get())
        a.vars["P"].set("(1, 1)")
        self.assertFalse(a.calculate_add())
        self.assertIsNone(a.add_calculation)
        a.vars["P"].set("O")
        self.assertTrue(a.calculate_add())
        self.assertEqual(a.add_calculation.result, (5, 16))
        self.assertEqual(a.add_result.cget("fg"), TEAL)

    def test_vertical_tangent(self):
        a = self.app
        a.load_example(5, 1, 0)
        a.vars["P"].set("(0, 0)")
        a.vars["Q"].set("(0, 0)")
        self.assertTrue(a.calculate_add())
        self.assertEqual(a.add_calculation.case, "vertical tangent")

    def test_scalar_trace_controls(self):
        a = self.app
        self.select_mode("multiply")
        self.assertTrue(a.calculate_scalar())
        self.assertEqual(a.scalar_trace.result, (0, 6))
        a.change_step(1)
        self.assertEqual(a.step_index, 0)
        self.assertEqual(a.highlights["R"], (5, 1))
        a.change_step(1)
        self.assertEqual(a.highlights["R"], (10, 6))
        a.change_step(1)
        self.assertEqual(a.highlights["R"], (0, 6))
        self.assertIn("disabled", a.next_button.state())
        a.change_step(-1)
        self.assertEqual(a.step_index, 1)
        a.show_scalar_final()
        self.assertEqual(a.step_index, -1)
        self.assertIn("Bit 2", a.scalar_text.get("1.0", "end"))

    def test_zero_negative_infinity_and_scalar_validation(self):
        a = self.app
        for k, point, expected in (("0", "(5, 1)", None), ("-1", "(5, 1)", (5, 16)),
                                    ("19", "(5, 1)", None), ("99", "O", None)):
            a.vars["k"].set(k)
            a.vars["scalarP"].set(point)
            self.assertTrue(a.calculate_scalar())
            self.assertEqual(a.scalar_trace.result, expected)
        a.vars["scalarP"].set("(5, 1)")
        a.vars["k"].set(str(2**256 - 1))
        self.assertTrue(a.calculate_scalar())
        self.assertLess(len(a.scalar_result.cget("text")), 30)
        for value in ("2.5", "cat", str(2**256), "1"*1000):
            a.vars["k"].set(value)
            self.assertFalse(a.calculate_scalar())
            self.assertIsNone(a.scalar_trace)
            self.assertIn("disabled", a.next_button.state())
        a.reset()
        self.assertEqual(a.scalar_result.cget("fg"), TEAL)

    def test_point_selection_and_csv(self):
        a = self.app
        a.point_table.selection_set("6")
        a.use_selected("P")
        self.assertEqual(a.vars["P"].get(), "(5, 16)")
        self.assertEqual(a.vars["scalarP"].get(), "(5, 16)")
        a.assign_point((6, 3), "Q")
        self.assertEqual(a.vars["Q"].get(), "(6, 3)")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"points.csv"
            a.write_points(path)
            with path.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 19)
            self.assertEqual(rows[0]["is_infinity"], "True")
            self.assertEqual(rows[0]["x"], "")
            self.assertTrue(all(row["p"] == "17" for row in rows))
            with patch("app.filedialog.asksaveasfilename", return_value=str(path)):
                a.export_points()
            addition_path = Path(directory)/"addition.txt"
            self.assertTrue(a.calculate_add())
            with patch("app.filedialog.asksaveasfilename", return_value=str(addition_path)):
                a.export_trace("add")
            self.assertIn("Result =", addition_path.read_text(encoding="utf-8"))
            scalar_path = Path(directory)/"scalar.txt"
            self.assertTrue(a.calculate_scalar())
            a.change_step(1)
            with patch("app.filedialog.asksaveasfilename", return_value=str(scalar_path)):
                a.export_trace("multiply")
            saved_trace = scalar_path.read_text(encoding="utf-8")
            self.assertIn("Bit 0", saved_trace)
            self.assertIn("Bit 2", saved_trace)  # export the full trace, not only the viewed step
            self.assertIn(a.curve.equation, saved_trace)

    def test_largest_gui_field(self):
        a = self.app
        a.load_example(997, 2, 2)
        a.update()
        self.assertEqual(a.curve.p, 997)
        self.assertEqual(len(a.plot_positions), len(a.points)-1)
        self.assertEqual(len(a.point_table.get_children()), len(a.points))
        self.assertTrue(a.calculate_add())
        self.assertTrue(a.calculate_scalar())

    def test_controls_fit_minimum_and_default_window(self):
        a = self.app
        for width, height in ((1080, 740), (1280, 840)):
            a.geometry(f"{width}x{height}")
            a.update()
            sidebar = a.winfo_children()[0]
            for child in sidebar.winfo_children():
                self.assertTrue(child.winfo_ismapped())
                self.assertGreater(child.winfo_height(), 8)
                self.assertLessEqual(child.winfo_y()+child.winfo_height(), sidebar.winfo_height())
            for mode in ("explore", "add", "multiply"):
                self.select_mode(mode)
                tab = a.tabs[mode]
                for child in tab.winfo_children():
                    self.assertTrue(child.winfo_ismapped(), (mode, str(child)))
                    self.assertLessEqual(child.winfo_y() + child.winfo_height(),
                                         tab.winfo_height(), (width, height, mode, str(child)))
                    self.assertGreater(child.winfo_height(), 18, (mode, str(child)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
