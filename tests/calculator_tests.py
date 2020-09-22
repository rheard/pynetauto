import logging
import math
import os
import string

from unittest import TestCase

from faker import Faker

from netauto import Element, TreeScope, WindowVisualState

faker = Faker()
logger = logging.getLogger(__name__)


class CalculatorTestCase(TestCase):
    def setUp(self):
        """Startup the calculator. As a convenience, find it too."""
        os.system("calc.exe")
        self.calculator = Element.desktop.find_element(
            name='Calculator', class_name='ApplicationFrameWindow',
            is_window=True,
            timeout=5, min_searches=2, scope=TreeScope.Children,
        )
        self.assertIsNotNone(self.calculator)

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
        negative = number[0] == '-'
        if negative:
            number = number[1:]

        for digit in number:
            if digit.isdecimal():
                automation_id = f"num{digit}Button"
            elif digit == '.':
                automation_id = "decimalSeparatorButton"
            else:
                # A-F hexadecimal
                automation_id = f"{digit}Button"

            self.calculator.find_element(automation_id=automation_id).invoke()

        if negative:
            self.calculator.find_element(automation_id="negateButton").invoke()

    def tearDown(self):
        """If the calculator is left open, we want to close it"""
        os.system("taskkill /f /im calculator.exe")


class BasicTests(CalculatorTestCase):
    """Basic tests that aren't actually Calculator specific"""

    def test_close_button(self):
        """Test that the close button works"""
        self.calculator.find_element(automation_id="Close", is_invoke=True).invoke()
        self.assertTrue(self.calculator.wait_unavailable(timeout=5),
                        "The calculator is still available even after clicking close!")

    def test_maximize_button(self, run_again=True):
        """
        Test that invoking the maximize/restore button will maximize/normalize the window.

        Args:
            run_again (bool): Run this test once more? This is an internal function. Running once will change the
                maximized state. Running again will change it back.
        """
        button = self.calculator.find_element(automation_id="Maximize", is_invoke=True)
        logger.info("Button name: %s", button.name)

        # An illusion here is that the `button.name` will change depending on if the window is maximized or not.
        if "Maximize" in button.name:
            # If the button.name is "Maximize Calculator", then the window should NOT currently be maximized,
            #   so maximize it, and wait for it to change...
            self.assertEqual(self.calculator.window_visual_state, WindowVisualState.Normal)
            button.invoke()
            self.calculator.find_element(name="Restore Calculator", is_invoke=True, timeout=5)
            self.assertEqual(self.calculator.window_visual_state, WindowVisualState.Maximized)
        else:
            # If the button.name is "Restore Calculator", then the window should currently be maximized,
            #   so un-maximize it, and wait for it to change...
            self.assertEqual(self.calculator.window_visual_state, WindowVisualState.Maximized)
            button.invoke()
            self.calculator.find_element(name="Maximize Calculator", is_invoke=True, timeout=5)
            self.assertEqual(self.calculator.window_visual_state, WindowVisualState.Normal)

        if run_again:
            self.test_maximize_button(run_again=False)

    def test_setting_visual_state(self):
        """Test that the visual state property acts like a property we can set."""
        self.calculator.window_visual_state = WindowVisualState.Normal
        self.assertIsNotNone(self.calculator.find_element(name="Maximize Calculator", is_invoke=True, timeout=5))
        self.calculator.window_visual_state = WindowVisualState.Maximized
        self.assertIsNotNone(self.calculator.find_element(name="Restore Calculator", is_invoke=True, timeout=5))
        self.calculator.window_visual_state = WindowVisualState.Normal
        self.assertIsNotNone(self.calculator.find_element(name="Maximize Calculator", is_invoke=True, timeout=5))


class StandardCalculatorTestCase(CalculatorTestCase):
    """Ensure that the Standard calculator is open for the start of the test."""

    def setUp(self):
        super(StandardCalculatorTestCase, self).setUp()
        self.calculator_mode = "Standard"

    def test_plus_basic(self, negative=False):
        """Test x + y == z with integers"""
        x = faker.pyint(min_value=-9999 if negative else -0)
        y = faker.pyint(min_value=-9999 if negative else -0)
        z = x + y
        self.enter_number(x)
        self.calculator.find_element(automation_id='plusButton').invoke()
        self.enter_number(y)
        self.calculator.find_element(automation_id='equalButton').invoke()
        self.assertEqual(
            self.calculator.find_element(automation_id="CalculatorResults").name,
            f"Display is {z:,}",
            f"Equation: {x} + {y} = {z}",
        )

    def test_plus_negative(self):
        """Test x + y == z with integers, that may be positive or negative"""
        self.test_plus_basic(negative=True)

    def test_square_basic(self, negative=False):
        """Test n**2 with integers"""
        n = faker.pyint(min_value=-9999 if negative else -0)
        n_2 = n**2
        self.enter_number(n)
        self.calculator.find_element(automation_id='xpower2Button').invoke()
        self.assertEqual(
            self.calculator.find_element(automation_id="CalculatorResults").name,
            f"Display is {n_2:,}",
            f"Equation: {n}**2 = {n_2}",
        )

    def test_square_negative(self):
        """Test n**2 with integers, that may be positive or negative"""
        self.test_square_basic(negative=True)


class ScientificCalculatorTestCase(CalculatorTestCase):
    """Ensure that the Scientific calculator is open for the start of the test."""

    def setUp(self):
        super(ScientificCalculatorTestCase, self).setUp()
        self.calculator_mode = "Scientific"

    def test_factorial(self):
        """Compute n!"""
        n = faker.pyint(max_value=20)  # If we go too big, it will use scientific notation
        n_f = math.factorial(n)
        self.enter_number(n)
        self.calculator.find_element(automation_id="factorialButton").invoke()
        self.assertEqual(
            self.calculator.find_element(automation_id="CalculatorResults").name,
            f"Display is {n_f:,}",
            f"{n}! = {n_f}",
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
        """Convert n to different bases..."""
        self.radix = "decimal"
        test_num = faker.pyint()
        self.enter_number(test_num)
        # Note that hex, oct and bin all have a space at the end. Decimal does not.
        self.assertEqual(
            self.calculator.find_element(automation_id="hexButton").name.split(' ', 1)[1].replace(' ', ''),
            f'{test_num:X}', f"Value: {test_num}"
        )
        self.assertEqual(
            self.calculator.find_element(automation_id="decimalButton").name.split(' ', 1)[1], f'{test_num:,}'
        )
        self.assertEqual(
            # Note the typo...
            self.calculator.find_element(
                automation_id="octolButton"
            ).name.split(' ', 1)[1].replace(' ', '').lstrip('0'),
            f"{test_num:o}", f"Value: {test_num}"
        )
        self.assertEqual(
            self.calculator.find_element(
                automation_id="binaryButton"
            ).name.split(' ', 1)[1].replace(' ', '').lstrip('0'),
            f"{test_num:b}", f"Value: {test_num}"
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
        all_numbers = set(string.hexdigits.lower())
        test_data = {
            'hex': all_numbers,
            'decimal': string.digits,
            'octol': string.octdigits,
            'binary': '01',
        }

        for test_radix, supposed_available_numbers in test_data.items():
            self.radix = test_radix
            for digit in all_numbers:
                automation_id = f"num{digit}Button" if digit.isdecimal() else f"{digit}Button"
                this_button = self.calculator.find_element(automation_id=automation_id, is_invoke=True)
                self.assertEqual(this_button.is_enabled, digit in supposed_available_numbers)
