class classproperty(object):
    """
    Like a mix between classmethod and property

    https://stackoverflow.com/questions/5189699

    If we need this to be writable at some point, use the more complex method given there.
    """
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)
