"""A simple wrapper over numpy arrays with some goodies."""

import numpy


class HashableDict(dict):
    """This is just a dict that can be hashed."""

    def __hash__(self):
        return hash(frozenset(self.items()))


# pylint: disable=too-few-public-methods
class HashableArray(object):
    """This just contains the NumPy array and the hash."""

    def __init__(self, data, sort=False):
        super(HashableArray, self).__init__()
        self.__sealed = False
        try:
            self.__hash = hash(data)
        except TypeError:
            self.__hash = hash(tuple(data))
        if sort:
            self.__array = sorted(data)
        else:
            self.__array = list(data)

    def seal(self, sort=False):
        """Makes the array a numpy array and makes it immutable."""
        if not self.__sealed:
            if sort:
                self.__array = numpy.sort(self.__array)
            else:
                self.__array = numpy.asarray(self.__array)
            self.__array.setflags(write=False)  # pylint: disable=no-member
            self.__sealed = True

    def extend(self, other):
        """Extends the array contents with new array."""
        if self.__sealed:
            raise RuntimeError('Array is sealed, cannot extend.')
        self.__array.extend(other)

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
