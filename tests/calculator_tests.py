import math
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

    @property
    def calculator_mode(self):
        return self.calculator.find_element(automation_id="Header", is_text=True).document_range.text

    @calculator_mode.setter
    def calculator_mode(self, value):
        if self.calculator_mode != value:
            pane_root = self.calculator.find_element(automation_id="PaneRoot", is_offscreen=False)
            if not pane_root:
                # The mode selector pane is not open. Open it.
                self.calculator.find_element(automation_id="TogglePaneButton", is_invoke=True).invoke()
                pane_root = self.calculator.find_element(automation_id="PaneRoot", timeout=5, min_searches=2,
                                                         is_offscreen=False)

            # Now that the pane is open, lets click the mode we want...
            pane_root.find_element(automation_id=value, is_invoke=True).invoke()
            pane_root.wait_unavailable(timeout=5)

    def enter_number(self, number):
        """Enter a number. Will not clear."""
        number = str(number)
        for digit in number:
            self.calculator.find_element(automation_id=f"num{digit}Button").invoke()

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


class StandardCalculatorTestCase(CalculatorTestCase):
    """Ensure that the Standard calculator is open for the start of the test."""
    def setUp(self):
        super(StandardCalculatorTestCase, self).setUp()
        self.calculator_mode = "Standard"

    def test_one_plus_one_is_two(self):
        self.enter_number(1)
        self.calculator.find_element(automation_id='plusButton').invoke()
        self.enter_number(1)
        self.calculator.find_element(automation_id='equalButton').invoke()
        self.assertEqual(
            self.calculator.find_element(automation_id="CalculatorResults").name,
            "Display is 2",
        )

    def test_five_squared(self):
        self.enter_number(5)
        self.calculator.find_element(automation_id='xpower2Button').invoke()
        self.assertEqual(
            self.calculator.find_element(automation_id="CalculatorResults").name,
            "Display is 25",
        )


class ScientificCalculatorTestCase(CalculatorTestCase):
    """Ensure that the Scientific calculator is open for the start of the test."""
    def setUp(self):
        super(ScientificCalculatorTestCase, self).setUp()
        self.calculator_mode = "Scientific"

    def test_ten_factorial(self):
        """Compute 10!"""
        self.enter_number(10)
        self.calculator.find_element(automation_id="factorialButton").invoke()
        self.assertEqual(
            self.calculator.find_element(automation_id="CalculatorResults").name,
            f"Display is {math.factorial(10):,}",
        )


class ProgrammerCalculatorTestCase(CalculatorTestCase):
    """Ensure that the Programmer calculator is open for the start of the test."""
    def setUp(self):
        super(ProgrammerCalculatorTestCase, self).setUp()
        self.calculator_mode = "Programmer"

    @property
    def radix(self):
        return self.calculator.find_elements(
            class_name="RadioButton", is_selected=True,
        ).automation_id.replace('Button', '')

    @radix.setter
    def radix(self, value):
        automation_id = f"{value.lower()}Button"
        radix_button = self.calculator.find_element(automation_id=automation_id)
        if not radix_button.is_selected:
            radix_button.select()
            self.calculator.find_element(automation_id=automation_id, is_selected=True, timeout=2)

    def test_base_conversion(self):
        """Convert 10 to different bases..."""
        self.radix = "decimal"
        test_num = 10
        self.enter_number(test_num)
        # Note that hex, oct and bin all have a space at the end. Decimal does not.
        self.assertEqual(
            self.calculator.find_element(automation_id="hexButton").name,
            f'HexaDecimal {test_num:X} '
        )
        self.assertEqual(
            self.calculator.find_element(automation_id="decimalButton").name,
            f'Decimal {test_num}'
        )
        # The following two will have a space between each character. So convert to the target using an f-string,
        #   then use " ".join, all inside of an f-string. Its f-string-ception.
        self.assertEqual(
            self.calculator.find_element(automation_id="octolButton").name,  # Note the typo...
            f'Octal {" ".join(f"{test_num:o}")} '
        )
        self.assertEqual(
            self.calculator.find_element(automation_id="binaryButton").name,
            f'Binary {" ".join(f"{test_num:b}")} '
        )

    def test_left_shift(self):
        """Compute 10 << 2"""
        self.radix = "decimal"
        test_num = 10
        test_shift = 2
        self.enter_number(test_num)
        self.calculator.find_element(automation_id='lshButton').invoke()
        self.enter_number(test_shift)
        self.calculator.find_element(automation_id='equalButton').invoke()
        self.assertEqual(
            self.calculator.find_element(automation_id="CalculatorResults").name,
            f"Display is {test_num << test_shift}",
        )

    def test_numbers_disabled_by_base(self):
        """Test that when we change to a base, only the numbers in that base are available to click"""
        all_numbers = '0123456789abcdef'
        test_data = {
            'hex': all_numbers,
            'decimal': '0123456789',
            'octol': '01234567',
            'binary': '01',
        }

        for test_radix, supposed_available_numbers in test_data.items():
            self.radix = test_radix
            for digit in all_numbers:
                automation_id = f"num{digit}Button" if digit.isdecimal() else f"{digit}Button"
                this_button = self.calculator.find_element(automation_id=automation_id, is_invoke=True)
                self.assertEqual(this_button.is_enabled, digit in supposed_available_numbers)
