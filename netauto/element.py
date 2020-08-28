from collections import defaultdict

import clr

from clr import System
from expanded_clr import get_wrapper_class
from expanded_clr.utils import is_python_name, python_name_to_csharp_name


class Element(get_wrapper_class(System.Windows.Automation.AutomationElement)):
    PATTERNS = dict()
    PROPERTIES = defaultdict(dict)

    @property
    def supported_properties(self):
        supported_properties = set(self.instance.GetSupportedProperties())
        ret = {k: {k1: v1 for k1, v1 in v.items() if v1 in supported_properties} for k, v in self.PROPERTIES.items()}
        return {k: v for k, v in ret.items() if v}  # Filter out patterns that have no supported props left

    @property
    def supported_patterns(self):
        supported_patterns = set(self.instance.GetSupportedPatterns())
        return {k: v for k, v in self.PATTERNS.items() if v in supported_patterns}

    def __getattr__(self, name):
        csharp_name = python_name_to_csharp_name(name)
        for _, supported_properties in self.supported_properties.items():
            for supported_property_name, supported_property in supported_properties.items():
                if supported_property_name == csharp_name:
                    return self.instance.GetCurrentPropertyValue(supported_property)

        # Well we didn't find a property... Lets look for a method, on one of the supported patterns
        for supported_pattern_name, supported_pattern in self.supported_patterns.items():
            if supported_pattern_name != 'AutomationElementIdentifiers':
                found_prop = getattr(self.instance.GetCurrentPattern(supported_pattern), csharp_name, None)
                if found_prop is not None:
                    return found_prop

        return super(Element, self).__getattr__(name)


# region Define Element things..
Element.desktop = Element.root_element

for id_ in range(10000, 11000):
    pat = System.Windows.Automation.AutomationPattern.LookupById(id_)
    if pat:
        Element.PATTERNS[System.Windows.Automation.Automation.PatternName(pat)] = pat

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
for prop_name, prop in list(Element.PROPERTIES['AutomationElementIdentifiers'].items()):
    if prop_name.endswith('PatternAvailable'):
        Element.PROPERTIES['AutomationElementIdentifiers'][prop_name[:-16]] = prop
# endregion
