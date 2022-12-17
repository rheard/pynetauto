import datetime as dt

from collections import defaultdict

import clr

from clr import System
from expanded_clr import get_wrapper_class
from expanded_clr.converters import ValueConverter
from expanded_clr.utils import is_python_name, python_name_to_csharp_name

from . import condition
from .utils import classproperty


class Element(get_wrapper_class(System.Windows.Automation.AutomationElement)):
    """
    A wrapper class for System.Windows.Automation.AutomationElement that allows access to properties and methods
        using Python naming conventions.
    """
    PATTERNS = dict()
    PROPERTIES = defaultdict(dict)

    def __getattr__(self, name):
        """
        Override the attribute accessor to allow access to properties and methods using Python naming conventions.

        Args:
            name (str): The name of the attribute to access.

        Returns:
            The value of the attribute.
        """
        # Check if the attribute is a supported property of the Element
        csharp_name = python_name_to_csharp_name(name)
        for supported_pattern, supported_properties in self.supported_properties.items():
            supported_property = supported_properties.get(csharp_name)
            if supported_property:
                # Return the value of the property using the ValueConverter to convert it to a Python object
                return ValueConverter.to_python(self.instance.GetCurrentPropertyValue(supported_property))

        # The attribute was not a supported property, so check if it is a method of a supported pattern
        for supported_pattern_name, supported_pattern in self.supported_patterns.items():
            if supported_pattern_name != 'AutomationElementIdentifiers':
                # Get the current pattern for the Element
                this_pattern = self.instance.GetCurrentPattern(supported_pattern)
                # Check if the pattern has the attribute as a method
                if hasattr(this_pattern, csharp_name):
                    # Return the value of the method using the ValueConverter to convert it to a Python object
                    return ValueConverter.to_python(getattr(this_pattern, csharp_name))

        # If the attribute was not found, raise an AttributeError
        return super(Element, self).__getattr__(name)

    def __bool__(self):
        """A way to check if the element is still "valid" and will continue to work"""
        try:
            return bool(self.process_id)
        except System.Windows.Automation.ElementNotAvailableException:
            return False

    @classproperty
    def desktop(cls):
        """Gets the root element, ie, the desktop"""
        return cls.RootElement

    @classproperty
    def focused(cls):
        """Gets the current focused element"""
        return cls.FocusedElement

    @property
    def supported_properties(self):
        """
        Get a dictionary of the supported properties for the Element, grouped by pattern.

        Returns:
            dict: A dictionary of the supported properties for the Element, grouped by pattern.
        """
        # Get the set of supported properties for the Element
        supported_properties = set(self.instance.GetSupportedProperties())

        # Filter out the properties for the AutomationElementIdentifiers pattern, as all elements support these
        #   properties whether they want to admit it or not
        ret = {k: {k1: v1 for k1, v1 in v.items() if v1 in supported_properties}
               if k != 'AutomationElementIdentifiers' else v
               for k, v in self.PROPERTIES.items()}

        # Filter out patterns that have no supported properties left
        return {k: v for k, v in ret.items() if v}

    @property
    def supported_patterns(self):
        """Get a dictionary of the supported patterns for the Element."""
        # Get the set of supported patterns for the Element
        supported_patterns = set(self.instance.GetSupportedPatterns())

        # Filter out patterns that are not supported by the Element
        return {k: v for k, v in self.PATTERNS.items() if v in supported_patterns}

    @property
    def children(self):
        """Get a list of the immediate children of the Element."""
        return self.find_elements(scope=System.Windows.Automation.TreeScope.Children)

    @property
    def parent(self):
        """Get the parent of the Element."""
        # Get the parent of the Element using the RawViewWalker and the `GetParent` method
        return Element(instance=System.Windows.Automation.TreeWalker.RawViewWalker.GetParent(self.instance))

    def send_keys(self, value):
        """
        Enter text through SendWait.

        Notes:
            If possible, avoid using this.

            For instance, the ValuePattern should be available which has `set_value`.
                Side note: The Notepad input document supports the value pattern according to the C APIs, but not
                    according to the same C# APIs?
        """
        self.set_focus()
        return System.Windows.Forms.SendKeys.SendWait(value)

    def wait_unavailable(self, timeout=float("int"), include_offscreen=True):
        """
        Wait for the Element to become unavailable.

        Args:
            timeout (int, float, datetime.timedelta, optional): The maximum amount of time to wait for the Element
                to become unavailable. Can be specified as an integer or float representing the number of seconds to
                wait, or as a datetime.timedelta object. Defaults to infinity.
            include_offscreen (bool, optional): Whether to consider the Element as unavailable if it is offscreen.
                Defaults to True.

        Returns:
            bool: True if the Element became unavailable within the specified timeout, False otherwise.
        """
        # Convert the timeout to a datetime object
        if timeout == float('inf'):
            timeout = dt.datetime.max
        elif isinstance(timeout, dt.timedelta):
            timeout += dt.datetime.now()
        elif isinstance(timeout, (float, int)):
            timeout = dt.datetime.now() + dt.timedelta(seconds=timeout)

        try:
            # Keep checking the availability of the Element until the timeout is reached
            while dt.datetime.now() < timeout:
                # Check the process_id property of the Element to see if it is available
                self.process_id

                # If the Element is offscreen and we are including offscreen Elements as unavailable, return True
                if include_offscreen and self.is_offscreen:
                    return True

            # The timeout was reached without the Element becoming unavailable
            return False
        except System.Windows.Automation.ElementNotAvailableException:
            # The Element became unavailable before the timeout was reached
            return True

    def find_element(self, *args, timeout=0, min_searches=1, scope=System.Windows.Automation.TreeScope.Descendants,
                     **kwargs):
        """
        Find an Element off this element.

        Args:
            args: See Condition for further documentation.
            timeout (int, float, datetime, timedelta): The minimum amount of time to search for until we give up and
                    and return None.
                Can be an integer or float, which is the number of seconds to wait for,
                    which optionally can be float("int") to wait forever.
                Or can be a timedelta, which is the time from now.
                Or can be a datetime when to stop.
            min_searches (int): The minimum number of times to search for until we give up and return None.
                    Defaults to 1.
            scope (TreeScope): The scope to search. Note that Window's UIAutomation only allows for Element,
                Descendants or Children.
            kwargs: See Condition for further documentation.

        Notes:
            On Windows 10, there seems to be an issues involving interfacing with the current window.
                Searching from the desktop can run into this issue, so 1 FindFirst call off the desktop could take 2-3s,
                so a timeout of 1s is pointless. But on Windows 7/8, a timeout of 5s might be too long.

                Thus using the min_searches argument, we can force 2 searches, no matter how long they take.
        """
        cond = condition.Condition(*args, **kwargs)

        if timeout == float('inf'):
            timeout = dt.datetime.max
        elif isinstance(timeout, dt.timedelta):
            timeout += dt.datetime.now()
        elif isinstance(timeout, (float, int)):
            timeout = dt.datetime.now() + dt.timedelta(seconds=timeout)

        while dt.datetime.now() < timeout or min_searches > 0:
            element = self.instance.FindFirst(scope, getattr(cond, 'instance', cond))

            if element is not None:
                return Element(instance=element)

            min_searches -= 1

        return None

    def find_elements(self, *args, timeout=0, min_searches=1, min_count=1,
                      scope=System.Windows.Automation.TreeScope.Descendants, **kwargs):
        """
        Find an Elements off this element.

        Args:
            args: See Condition for further documentation.
            timeout (int, float, datetime, timedelta): The minimum amount of time to search for until we give up and
                    and return None.
                Can be an integer or float, which is the number of seconds to wait for,
                    which optionally can be float("int") to wait forever.
                Or can be a timedelta, which is the time from now.
                Or can be a datetime when to stop.
            min_searches (int): The minimum number of times to search for until we give up and return None.
                    Defaults to 1.
            min_count (int): The minimum number of element to consider a search successful. Defaults to 1.
                If we do not find this many, and the timeout or min_searches condition expires, then we will return
                    whatever we got with the last call.
            scope (TreeScope): The scope to search. Note that Window's UIAutomation only allows for Element,
                Descendants or Children.
            kwargs: See Condition for further documentation.
        """
        cond = condition.Condition(*args, **kwargs)

        if timeout == float('inf'):
            timeout = dt.datetime.max
        elif isinstance(timeout, dt.timedelta):
            timeout += dt.datetime.now()
        elif isinstance(timeout, (float, int)):
            timeout = dt.datetime.now() + dt.timedelta(seconds=timeout)

        elements = []
        while dt.datetime.now() < timeout or min_searches > 0 and len(elements) < min_count:
            elements = self.instance.FindAll(scope, getattr(cond, 'instance', cond))
            min_searches -= 1

        return ValueConverter.to_python(elements)

    @property
    def clickable_point(self):
        """A property alias for the get_clickable_point method"""
        return self.get_clickable_point()

    @property
    def window_visual_state(self):
        return self.__getattr__('window_visual_state')  # This should still work the same.

    @window_visual_state.setter
    def window_visual_state(self, val):
        """A property alias for the set_window_visual_state method"""
        self.set_window_visual_state(val)

    @property
    def value(self):
        return self.__getattr__('value')  # This should still work the same.

    @value.setter
    def value(self, val):
        """A property alias for the set_value method"""
        self.set_value(val)


# region Define Element things..
# I don't know why, but if we don't get Element.root_element, then all the LookupByIds will always return None!
Element.root_element

# First up, lets lookup all the possible AutomationPatterns...
for id_ in range(10000, 11000):
    pat = System.Windows.Automation.AutomationPattern.LookupById(id_)
    if pat:
        Element.PATTERNS[System.Windows.Automation.Automation.PatternName(pat)] = pat

# Now lets lookup the possible AutomationProperties
for id_ in range(30000, 31000):
    prop = System.Windows.Automation.AutomationProperty.LookupById(id_)
    if prop:
        target_pattern_name = prop.ProgrammaticName.split('.', 1)[0]
        programmatic_pattern_name = f"{target_pattern_name}.Pattern"
        for pattern_name, pattern in Element.PATTERNS.items():
            if programmatic_pattern_name == pattern.ProgrammaticName:
                Element.PROPERTIES[pattern_name][System.Windows.Automation.Automation.PropertyName(prop)] = prop
                break
        else:
            if target_pattern_name != 'AutomationElementIdentifiers':
                # The only pattern we expect to not find is the standard element pattern, which we won't be using anyway
                raise NotImplementedError(programmatic_pattern_name)

            Element.PROPERTIES[target_pattern_name][System.Windows.Automation.Automation.PropertyName(prop)] = prop

# I also want to provide some shortcuts...
#   For example, I want IsWindow to work for IsWindowPatternAvailable
for prop_name, prop in list(Element.PROPERTIES.get('AutomationElementIdentifiers', dict()).items()):
    if prop_name.endswith('PatternAvailable'):
        Element.PROPERTIES['AutomationElementIdentifiers'][prop_name[:-16]] = prop
# endregion


class TextRange(get_wrapper_class(System.Windows.Automation.Text.TextPatternRange)):
    @property
    def text(self):
        return self.get_text(-1)
