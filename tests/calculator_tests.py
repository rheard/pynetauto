import os

from unittest import TestCase

from netauto import Condition as C, Element, TreeScope, WindowVisualState


class CalculatorTestCase(TestCase):
    def setUp(self):
        """Startup the calculator. As a convenience, find it too."""
        os.system("calc.exe")
        self.calculator = Element.desktop.find_element(
            name='Calculator', class_name='ApplicationFrameWindow',
            is_window=True,
            timeout=5, min_searches=2, scope=TreeScope.Children,
        )

    def tearDown(self):
        """If the calculator is left open, we want to close it"""
        os.system("taskkill /f /im calculator.exe")


class WindowTests(CalculatorTestCase):
    def test_close_button(self):
        """Test that the close button works"""
        self.calculator.find_element(automation_id="Close", is_invoke=True).invoke()
        self.assertTrue(self.calculator.wait_unavailable(timeout=5))

    def test_maximize_button(self, run_again=True):
        """
        Test that invoking the maximize/restore button will maximize/normalize the window.

        Args:
            run_again (bool): Run this test once more? This is an internal function. Running once will change the
                maximized state. Running again will change it back.
        """
        button = self.calculator.find_element(C(name="Maximize Calculator") | C(name="Restore Calculator"),
                                              is_invoke=True)

        if "Maximize" in button.name:
            self.assertEqual(self.calculator.window_visual_state, WindowVisualState.Normal)
            button.invoke()
            self.calculator.find_element(name="Restore Calculator", is_invoke=True, timeout=5)
            self.assertEqual(self.calculator.window_visual_state, WindowVisualState.Maximized)
        else:
            self.assertEqual(self.calculator.window_visual_state, WindowVisualState.Maximized)
            button.invoke()
            self.calculator.find_element(name="Maximize Calculator", is_invoke=True, timeout=5)
            self.assertEqual(self.calculator.window_visual_state, WindowVisualState.Normal)

        if run_again:
            self.test_maximize_button(run_again=False)

    def test_setting_visual_state(self):
        """Test that the visual state property acts like a property we can set."""
        self.calculator.window_visual_state = WindowVisualState.Normal
        self.assertTrue(bool(self.calculator.find_element(name="Maximize Calculator", is_invoke=True, timeout=5)))
        self.calculator.window_visual_state = WindowVisualState.Maximized
        self.assertTrue(bool(self.calculator.find_element(name="Restore Calculator", is_invoke=True, timeout=5)))
        self.calculator.window_visual_state = WindowVisualState.Normal
        self.assertTrue(bool(self.calculator.find_element(name="Maximize Calculator", is_invoke=True, timeout=5)))


class BasicMath(CalculatorTestCase):
    """Just attempt to do some basic math with the calculator..."""
    def test_one_plus_one_is_two(self):
        one_button = self.calculator.find_element(automation_id="num1Button")
        one_button.invoke()
        self.calculator.find_element(automation_id='plusButton').invoke()
        one_button.invoke()
        self.calculator.find_element(automation_id='equalButton').invoke()
        self.assertEqual(
            self.calculator.find_element(automation_id="CalculatorResults").name,
            "Display is 2",
        )

    def test_five_squared(self):
        self.calculator.find_element(automation_id="num5Button").invoke()
        self.calculator.find_element(automation_id='xpower2Button').invoke()
        self.assertEqual(
            self.calculator.find_element(automation_id="CalculatorResults").name,
            "Display is 25",
        )
