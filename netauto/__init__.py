import clr

from clr import System
from expanded_clr.utils import get_wrapper_class, python_name_to_csharp_name


# TODO: Build a searching mechanism (is there one in pythonnet or C#) so these don't need to be in the cwd.
clr.AddReference('UIAutomationClient')


from . import element, condition
from .element import Element
from .condition import Condition


def __getattr__(name):
    """This module is also an entry point for items found in System.Windows.Automation"""
    name = python_name_to_csharp_name(name)
    return get_wrapper_class(getattr(System.Windows.Automation, name))
