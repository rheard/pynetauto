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
    PATTERNS = dict()
    PROPERTIES = defaultdict(dict)

    def __getattr__(self, name):
        csharp_name = python_name_to_csharp_name(name)
        for _, supported_properties in self.supported_properties.items():
            for supported_property_name, supported_property in supported_properties.items():
                if supported_property_name == csharp_name:
                    return ValueConverter.to_python(self.instance.GetCurrentPropertyValue(supported_property))

        # Well we didn't find a property... Lets look for a method, on one of the supported patterns
        for supported_pattern_name, supported_pattern in self.supported_patterns.items():
            if supported_pattern_name != 'AutomationElementIdentifiers':
                found_prop = getattr(self.instance.GetCurrentPattern(supported_pattern), csharp_name, None)
                if found_prop is not None:
                    return found_prop

        return super(Element, self).__getattr__(name)

    def __bool__(self):
        try:
            return bool(self.process_id)
        except System.Windows.Automation.ElementNotAvailableException:
            return False

    @classproperty
    def desktop(cls):
        return cls.RootElement

    @classproperty
    def focused(cls):
        return cls.FocusedElement

    @property
    def supported_properties(self):
        supported_properties = set(self.instance.GetSupportedProperties())
        ret = {k: {k1: v1 for k1, v1 in v.items() if v1 in supported_properties} for k, v in self.PROPERTIES.items()}
        return {k: v for k, v in ret.items() if v}  # Filter out patterns that have no supported props left

    @property
    def supported_patterns(self):
        supported_patterns = set(self.instance.GetSupportedPatterns())
        return {k: v for k, v in self.PATTERNS.items() if v in supported_patterns}

    @property
    def children(self):
        return self.find_elements(scope=System.Windows.Automation.TreeScope.Children)

    @property
    def parent(self):
        return Element(instance=System.Windows.Automation.TreeWalker.RawViewWalker.GetParent(self.instance))

    def wait_unavailable(self, timeout=30):
        """Wait for this element to become unavailable."""
        if timeout == float('inf'):
            timeout = dt.datetime.max
        elif isinstance(timeout, dt.timedelta):
            timeout += dt.datetime.now()
        elif isinstance(timeout, (float, int)):
            timeout = dt.datetime.now() + dt.timedelta(seconds=timeout)

        try:
            while dt.datetime.now() < timeout:
                self.process_id

            return False
        except System.Windows.Automation.ElementNotAvailableException:
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

            if element:
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
