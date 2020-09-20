import os

from unittest import TestCase

from netauto import Element, TreeScope


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

    def test_maximize_button(self):
        self.assertNotEqual(self.calculator.window_visual_state, 1)
        self.calculator.find_element(automation_id="Maximize", is_invoke=True).invoke()
        # On maximizing, the button we just clicked will change to a restore button. Wait for it...
        self.calculator.find_element(automation_id="Restore", is_invoke=True, timeout=5)
        self.assertEqual(self.calculator.window_visual_state, 1)


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
