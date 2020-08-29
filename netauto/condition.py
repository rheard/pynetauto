from clr import System
from expanded_clr import get_wrapper_class
from expanded_clr.utils import python_name_to_csharp_name

from . import element


class PropertyCondition(get_wrapper_class(System.Windows.Automation.PropertyCondition)):
    """This is not to be used directly, and only provides for wrapper methods and serves the Condition wrapper."""
    def __or__(self, other):
        return OrCondition([self.instance, getattr(other, 'instance', other)])

    def __and__(self, other):
        return AndCondition([self.instance, getattr(other, 'instance', other)])


class AndCondition(get_wrapper_class(System.Windows.Automation.AndCondition)):
    """This is not to be used directly, and only provides for wrapper methods and serves the Condition wrapper."""
    def __or__(self, other):
        return OrCondition([self.instance, getattr(other, 'instance', other)])

    def __and__(self, other):
        return AndCondition([self.instance, getattr(other, 'instance', other)])


class OrCondition(get_wrapper_class(System.Windows.Automation.OrCondition)):
    """This is not to be used directly, and only provides for wrapper methods and serves the Condition wrapper."""
    def __or__(self, other):
        return OrCondition([self.instance, getattr(other, 'instance', other)])

    def __and__(self, other):
        return AndCondition([self.instance, getattr(other, 'instance', other)])


class Condition(get_wrapper_class(System.Windows.Automation.Condition)):
    """
    A Condition wrapper, similar to Django's Q object.

    Allows for us to define arbitrary conditions to search for. Note that the find methods will call this, so this
        is only needed for more complex logic.

    Args:
        args: Any existing Condition objects.
        kwargs: Allow for PropertyConditions. For example, to find Elements named "Untitled - Notepad":
            Condition(name="Untitled - Notepad")

    Notes:
        If no arguments are provided, a Condition.true is returned. Condition.false is also available.
        If multiple arguments or keyword arguments are provided, they will be ANDed together.

        There are some property names that have duplicate property IDs. For example, Condition(is_read_only=True)
            is ambiguous (and unpredictable), since both RangeValue and Value patterns provide for is_read_only,
            and we will use the first ID we find.

            To avoid this issue, you can optionally provide the pattern name in a similar fashion to a Django JOIN.
            For is_read_only RangeValues: Condition(range_value__is_read_only=True)
            For is_read_only Values: Condition(value__is_read_only=True)
            For is_read_only either: Condition(value__is_read_only=True) | Condition(range_value__is_read_only=True)
    """
    def __new__(cls, *args, instance=None, **kwargs):
        if instance is not None:
            # We were given an instance. This must be the TrueCondition or something. Just wrap it...
            return super(Condition, cls).__new__(cls)

        args = list(args)
        for prop_name, prop_val in kwargs.items():
            # We want to convert each of these to a PropertyCondition. To do that, we need the Property object.
            #   If we were given a simple property name, we will look for a property that works and use that.
            #   If we were given a pattern_name__property_name, we will use the more specific property.
            prop = None
            if '__' in prop_name:
                pattern_name, real_prop_name = prop_name.split('__', 1)
                pattern_name = python_name_to_csharp_name(pattern_name)
                csharp_prop_name = python_name_to_csharp_name(real_prop_name)
                prop = element.Element.PROPERTIES.get(pattern_name, {})[csharp_prop_name]
            else:
                csharp_prop_name = python_name_to_csharp_name(prop_name)
                for properties in element.Element.PROPERTIES.values():
                    if csharp_prop_name in properties:
                        prop = properties[csharp_prop_name]

            if prop is None:
                raise ValueError(f'Failed to find property for {prop_name}')

            args.append(PropertyCondition(prop, getattr(prop_val, 'instance', prop_val)))

        if len(args) == 0:
            return cls.TrueCondition

        while len(args) > 1:
            left = args.pop()
            right = args.pop()
            args.append(AndCondition([left.instance, right.instance]))

        return args[0]

    def __or__(self, other):
        return OrCondition([self.instance, getattr(other, 'instance', other)])

    def __and__(self, other):
        return AndCondition([self.instance, getattr(other, 'instance', other)])


true = Condition.true = Condition.TrueCondition
false = Condition.false = Condition.FalseCondition
