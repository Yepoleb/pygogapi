class Property:
    def __init__(self, *args):
        self.updaters = args

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            raise AttributeError("Property owner must be instanciated")
        if not instance._updated.get(self.name, False):
            getattr(instance, "update_" + self.updaters[0])()
        return getattr(instance, '_' + self.name)

    def __set__(self, instance, value):
        setattr(instance, '_' + self.name, value)
        instance._updated[self.name] = True

# https://stackoverflow.com/a/42023924
class GogMeta(type):
    def __new__(mcls, name, bases, attrs):
        cls = super(GogMeta, mcls).__new__(mcls, name, bases, attrs)
        for attr, obj in attrs.items():
            if isinstance(obj, Property):
                obj.__set_name__(cls, attr)
        return cls

class GogBase(metaclass=GogMeta):
    def __init__(self):
        self._updated = {}
