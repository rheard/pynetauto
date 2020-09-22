# pynetauto
A Pythonic entry point for the .NET Automation libraries. This library uses [expanded-pythonnet](https://github.com/rheard/expanded-pythonnet) as a base,
    and as such contains all its features. For full examples, look at the tests.

Much of the usage comes from the .NET Automation documentation, however some convenience overhead is added is some places.
    For instance, the pattern availability properties have been shortened with nicknames. Normally you would have to
    use `IsWindowPatternAvailable` to see if the window pattern is available, but `IsWindow` (and `is_window`) work
    just as well.
    
Inspect.exe (or UISpy) is a highly recommended resource while developing with this library.


### Entry Point
The entry point can be the standard `Element.RootElement` from the documentation, `Element.root_element`, derived 
    from the features of expanded-pythonnet, or `Element.desktop`.
    
Another option is to start from the focused element, which can be accessed using any of the following: 
    `Element.FocusedElement`, `Element.focused_element` or `Element.focused`.


### Finding Elements
To find an element, the methods `find_element` and `find_elements` are provided, along with a `Condition` system 
    for more complex logic which works similar to Django's `Q` object for queries.
    
The properties to search for can be found in the .NET Automation documentation. A `timeout` and `min_searches` can
    be provided for waiting, which default to 0 and 1 respectively. A single search from the desktop can take a few
    seconds on later versions of Windows 10, bypassing a `timeout` value, hence the need for the `min_searches` argument.
    The methods will only give up their search after both the `timeout` and `min_searches` arguments are satisfied. A
    `timeout` of `float('inf')` can be provided to search forever.
    
Both methods also accept a `scope` argument, which should be a `TreeScope` value and defaults to `TreeScope.Descendants`.

##### Example
As an example, to find the Calculator window:
```python
from netauto import Element, TreeScope

Element.desktop.find_element(
    name="Calculator", is_window=True, scope=TreeScope.Children, timeout=5, min_searches=2,
)
```

`name="Calculator"` and `is_window=True` are the properties being searched. The search is limited to only the direct
    children of the desktop using `scope=TreeScope.Children`. Lastly `timeout=5, min_searches=2` tells it to search for
    5 seconds, at least twice, in case we just executed the calculator and it is opening still.

#### Complex Searches and Condition objects
For complex queries, `Condition` objects can be used which act similarly to Django's `Q` for queries. For example,
    to build a `Condition` to find all windows and invoke elements, we would do:

```python
from netauto import Condition as C

C(is_window=True) | C(is_invoke=True)
```

##### Conflicting property names
There are instances where 2 patterns can share the same property, namely both the `RangeValue` and `Value` patterns
    provide the `Value` property. This shouldn't be a problem when getting the property from an existing `Element` and
    is only a problem when searching or creating `Condition` objects.

To avoid this problem, the pattern name for properties can be provided explicitly. To find the `RangeValue` with
    a specific value: `Condition(range_value__value=5)`.


### Wait for Close
After certain actions such as closing a window, a user might want to wait until the window closes 
    (or simply goes offscreen). To this end, `Element.wait_unavailable` is provided with a default `timeout` of 
    30 seconds. An `include_offscreen` argument is also provided which defaults to `True`, meaning that the `Element` 
    going offscreen will consider it unavailable. If the `timeout` expires, `False` is returned, otherwise `True` is.