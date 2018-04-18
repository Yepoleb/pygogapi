import logging


logging.basicConfig()
logger = logging.getLogger("gogapi")


# TODO: Implement exceptions properly
class GogError(Exception):
    pass

class ApiError(GogError):
    def __init__(self, error, description):
        super().__init__()
        self.error = error
        self.description = description

class MissingResourceError(GogError):
    pass

class NotAuthorizedError(GogError):
    pass


class GogObject:
    def __init__(self, api):
        self.api = api
        self.loaded = set()

    def has(self, *attrs):
        return all(hasattr(self, attr) for attr in attrs)

    def simple_repr(self, attributes):
        attr_pairs = []
        for name in attributes:
            value = getattr(self, name, None)
            attr_pairs.append("{}={!r}".format(name, value))

        return "{}({})".format(self.__class__.__name__, ", ".join(attr_pairs))
