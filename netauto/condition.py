from clr import System
from expanded_clr import get_wrapper_class
from expanded_clr.utils import python_name_to_csharp_name

from . import element


class PropertyCondition(get_wrapper_class(System.Windows.Automation.PropertyCondition)):
    def __or__(self, other):
        return OrCondition([self.instance, getattr(other, 'instance', other)])

    def __and__(self, other):
        return AndCondition([self.instance, getattr(other, 'instance', other)])


class AndCondition(get_wrapper_class(System.Windows.Automation.AndCondition)):
    def __or__(self, other):
        return OrCondition([self.instance, getattr(other, 'instance', other)])

    def __and__(self, other):
        return AndCondition([self.instance, getattr(other, 'instance', other)])


class OrCondition(get_wrapper_class(System.Windows.Automation.OrCondition)):
    def __or__(self, other):
        return OrCondition([self.instance, getattr(other, 'instance', other)])

    def __and__(self, other):
        return AndCondition([self.instance, getattr(other, 'instance', other)])


class Condition(get_wrapper_class(System.Windows.Automation.Condition)):
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
