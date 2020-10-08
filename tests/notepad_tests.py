import logging
import os

from subprocess import Popen
from unittest import TestCase

from faker import Faker

from netauto import Element, TreeScope

faker = Faker()
logger = logging.getLogger(__name__)


# TODO: There appears to be a problem with C#'s AutomationElement's IsValuePatternAvailableProperty.
#   Inspect.exe reports Notepad's "Text Editor" supports the Value pattern, and using C (IUIAutomationElement),
#       this is what we find and the SetValue method works. However using C# (AutomationElement), the Value pattern
#       is reported as not available and SetValue cannot be used.
#   This is most certainly a bug with C# that has been reported to Microsoft via Visual Studio.
#       For now use `send_keys`, and when this is fixed, use `.value = ` (`set_value`)


class NotepadTestCase(TestCase):
    def setUp(self):
        """Startup notepad. As a convenience, find it too."""
        p = Popen("notepad.exe")
        self.notepad = Element.desktop.find_element(
            process_id=p.pid, class_name='Notepad', is_window=True,
            timeout=5, min_searches=2, scope=TreeScope.Children,
        )
        self.assertIsNotNone(self.notepad)
        self.PATHS = set()

    def tearDown(self):
        """If the calculator is left open, we want to close it"""
        os.system("taskkill /f /im notepad.exe")

        for path in self.PATHS:
            if os.path.exists(path):
                os.remove(path)

    def get_path(self, index=1, clean=True):
        """Gets the path of a test file"""
        path = os.path.join(os.environ['TEMP'], f'netauto_test_{index}.txt')
        self.PATHS.add(path)

        if clean and os.path.exists(path):
            os.remove(path)

        return path

    @property
    def menu_bar(self):
        return self.notepad.find_element(automation_id="MenuBar")

    @property
    def file_menu_item(self):
        return self.menu_bar.find_element(automation_id="Item 1", is_expand_collapse=True)

    @property
    def context_menu(self):
        return self.notepad.find_element(class_name="#32768", timeout=1)

    @property
    def save_button(self):
        """Requires that the File menu be opened first."""
        return self.context_menu.find_element(automation_id="Item 3", is_invoke=True)


class SaveTests(NotepadTestCase):
    """Tests around saving in Notepad."""
    TEST_STR = "test"

    def test_basic_save(self):
        """Test that we can save to the file system."""
        editor = self.notepad.find_element(automation_id="15")
        editor.send_keys(self.TEST_STR)
        self.assertEqual(editor.document_range.text, self.TEST_STR)

        # We could send the hotkey for save... but thats boring
        self.file_menu_item.expand()  # Open the File menu
        self.save_button.invoke()  # Click save

        test_file_path = self.get_path()
        save_dialog = self.notepad.find_element(is_window=True, scope=TreeScope.Children, timeout=5)
        save_dialog.find_element(automation_id="1001", is_value=True).value = test_file_path
        save_dialog.find_element(automation_id="1", class_name="Button", is_invoke=True).invoke()
        save_dialog.wait_unavailable()

        # Here, use find_element with TreeScope.Element to wait for the current Window's name to change,
        #   as an indication that the file save process is complete.
        self.notepad.find_element(
            name=f"{os.path.basename(test_file_path)} - Notepad", timeout=5, scope=TreeScope.Element,
        )

        self.assertTrue(os.path.exists(test_file_path))
        with open(test_file_path, "r") as rb:
            self.assertEqual(self.TEST_STR, rb.read())

    def test_overwrite_save(self):
        """Test that we can save to the file system, and overwrite a file by doing that."""
        editor = self.notepad.find_element(automation_id="15")
        editor.send_keys(self.TEST_STR)
        self.assertEqual(editor.document_range.text, self.TEST_STR)

        # We could send the hotkey for save... but thats boring
        self.file_menu_item.expand()  # Open the File menu
        self.save_button.invoke()  # Click save

        test_file_path = self.get_path()
        with open(test_file_path, "w") as wb:
            wb.write("")

        save_dialog = self.notepad.find_element(is_window=True, scope=TreeScope.Children, timeout=5)
        save_dialog.find_element(automation_id="1001", is_value=True).value = test_file_path
        save_dialog.find_element(automation_id="1", class_name="Button", is_invoke=True).invoke()

        # Find the "Confirm Save As" dialog, and click the Yes button.
        save_dialog.find_element(
            is_window=True, scope=TreeScope.Children,
        ).find_element(
            is_invoke=True, automation_id="CommandButton_6"
        ).invoke()
        save_dialog.wait_unavailable()

        # Here, use find_element with TreeScope.Element to wait for the current Window's name to change,
        #   as an indication that the file save process is complete.
        self.notepad.find_element(
            name=f"{os.path.basename(test_file_path)} - Notepad", timeout=5, scope=TreeScope.Element,
        )

        self.assertTrue(os.path.exists(test_file_path))
        with open(test_file_path, "r") as rb:
            self.assertEqual(self.TEST_STR, rb.read())
