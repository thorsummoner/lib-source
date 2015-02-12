#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Server object
"""

class Server(object):
    """Server class.
    """
    def __init__(self, ipv4, port):
        self.ipv4 = ipv4
        self.port = int(port)

    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            return self.__dict__.get(attr, None)

    def __repr__(self):
        return '<Server: {0}>'.format(self)

    def __str__(self):
        return '{0}:{1}'.format(self.ipv4, self.port)

    def __eq__(self, other):
        return str(self) == str(other)

    def __ne__(self, other):
        return str(self) != str(other)

    def __iter__(self):
        for attribute in self.__dict__:
            if not attribute.startswith('_'):
                yield attribute

    @property
    def name(self):
        """Get name property.
        """
        return self.__dict__.setdefault('name', self.ipv4)
    @name.setter
    def name(self, name):
        """Set name property.
        """
        self.__dict__['name'] = name

    @classmethod
    def new_from_str(cls, string):
        """New Server object from connection string.
        """
        ipv4, port = string.split(':')
        return cls(ipv4, port)

    def as_tuple(self):
        """Return data as tuple.
        """
        return (self.ipv4, self.port)
