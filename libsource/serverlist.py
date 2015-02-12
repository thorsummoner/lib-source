#!/usr/bin/python
# -*- coding: utf-8 -*-

""" High level server list module.
"""

from libsource import server

class ServerList(list):
    """ Get server list.
    """
    def __init__(self):
        super(ServerList, self).__init__([])

    def __repr__(self):
        return '<ServerList: {0}>'.format(len(self))

    def append(self, item):
        """Append server object to server list.
        """
        if not isinstance(item, server.Server):
            raise TypeError('item must be from type Server')
        if not item in self:
            super(ServerList, self).append(item)
