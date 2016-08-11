"""A simple wrapper over numpy arrays with some goodies."""

import numpy


class HashableDict(dict):
    """This is just a dict that can be hashed."""

    def __init__(self, *args, **kwargs):
        super(HashableDict, self).__init__(*args, **kwargs)
        self.__hash = None

    def __setitem__(self, key, value):
        """The map shouldn't be mutated after is is hashed."""
        if self.__hash is not None:
            raise RuntimeError('This dict is not mutable any more.')
        super(HashableDict, self).__setitem__(key, value)

    def __hash__(self):
        """Generates and returns the hash of the dict."""
        if self.__hash is None:
            self.__hash = hash(frozenset(self.items()))
        return self.__hash


# pylint: disable=too-few-public-methods
class HashableArray(object):
    """This just contains the NumPy array and the hash."""

    def __init__(self, data, sort=False):
        super(HashableArray, self).__init__()
        self.__array = numpy.asarray(data)
        if sort:
            self.__array.sort()
        self.__array.flags.writeable = False
        self.__hash = hash(self.__array.data.tobytes())

    @property
    def array(self):
        """Returns the enclosed array."""
        return self.__array

    def __getitem__(self, index):
        """Make this object subscriptable."""
        return self.__array[index]

    def __len__(self):
        """The len is always the len of the enclosed."""
        return len(self.__array)

    def __hash__(self):
        """Returns the hash of the enclosing."""
        return self.__hash
