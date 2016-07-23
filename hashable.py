"""A simple wrapper over numpy arrays with some goodies."""

import numpy


# pylint: disable=too-few-public-methods
class HashableArray(object):
    """This is just contains the NumPy array and the hash."""

    def __init__(self, data, sort=False):
        super(HashableArray, self).__init__()
        try:
            self.__hash = hash(data)
        except TypeError:
            self.__hash = hash(tuple(data))
        if sort:
            self.__array = numpy.sort(data)
        else:
            self.__array = numpy.asarray(data)
        self.__array.setflags(write=False)

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
