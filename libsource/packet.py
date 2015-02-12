#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Manipulate Packets.
"""

import io
import struct


class PacketBuffer(io.BytesIO):
    """Manipulate packets as streams.
    """
    # pylint: disable=missing-docstring
    def __len__(self):
        return len(self.getvalue())

    def __repr__(self):
        return '<PacketBuffer: {}>'.format(len(self))

    def __str__(self):
        return str(self.getvalue())

    def is_empty(self):
        return self.tell() == len(self)

    def get_byte(self):
        return struct.unpack('<B', self.read(1))[0]

    def put_byte(self, value):
        self.write(struct.pack('<B', value))

    def get_short(self):
        return struct.unpack('<h', self.read(2))[0]

    def put_short(self, value):
        self.write(struct.pack('<h', value))

    def get_float(self):
        return struct.unpack('<f', self.read(4))[0]

    def put_float(self, value):
        self.write(struct.pack('<f', value))

    def get_long(self):
        return struct.unpack('<l', self.read(4))[0]

    def put_long(self, value):
        self.write(struct.pack('<l', value))

    def get_long_long(self):
        return struct.unpack('<Q', self.read(8))[0]

    def put_long_long(self, value):
        self.write(struct.pack('<Q', value))

    # pylint: enable=missing-docstring

    def get_string(self):
        """Return new bytes from stream.
        """
        # TODO: find a more pythonic way doing this
        value = []
        while True:
            char = self.read(1)
            if char == b'\x00':
                break
            else:
                value.append(char)
        return ''.join([chr(ord(char)) for char in value])

    def put_string(self, value):
        """Write utf-8 strng into packet buffer.
        """
        self.write(bytearray('{0}\x00'.format(value), 'utf-8'))


