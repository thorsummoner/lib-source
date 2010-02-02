#!/usr/bin/python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------------
# SourceQuery - Python class for querying info from Source Dedicated Servers
# Copyright (c) 2010 Andreas Klauer <Andreas.Klauer@metamorpher.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#------------------------------------------------------------------------------

"""http://developer.valvesoftware.com/wiki/Server_Queries"""

#
# TODO:  Implement split packet handling once TF2 SRCDS is fixed by Valve.
# TODO:: (Currently TF2 sends incomplete packets instead of splitting them.)
#

import socket, struct, time
import StringIO

PACKETSIZE=1400

WHOLE=-1

# A2A_PING
A2A_PING = ord('i')
A2A_PING_REPLY = ord('j')
A2A_PING_REPLY_STRING = '00000000000000'

# A2S_INFO
A2S_INFO = ord('T')
A2S_INFO_STRING = 'Source Engine Query'
A2S_INFO_REPLY = ord('I')

# A2S_PLAYER
A2S_PLAYER = ord('U')
A2S_PLAYER_REPLY = ord('D')

# A2S_RULES
A2S_RULES = ord('V')
A2S_RULES_REPLY = ord('E')

# S2C_CHALLENGE
CHALLENGE = -1
S2C_CHALLENGE = ord('A')

class SourceQueryPacket(StringIO.StringIO):
    # putting and getting values
    def putByte(self, val):
        self.write(struct.pack('<B', val))

    def getByte(self):
        return struct.unpack('<B', self.read(1))[0]

    def putShort(self, val):
        self.write(struct.pack('<h', val))

    def getShort(self):
        return struct.unpack('<h', self.read(2))[0]

    def putLong(self, val):
        self.write(struct.pack('<l', val))

    def getLong(self):
        return struct.unpack('<l', self.read(4))[0]

    def putFloat(self, val):
        self.write(struct.pack('<f', val))

    def getFloat(self):
        return struct.unpack('<f', self.read(4))[0]

    def putString(self, val):
        self.write(val + '\x00')

    def getString(self):
        val = self.getvalue()
        start = self.tell()
        end = val.index('\0', start)
        val = val[start:end]
        self.seek(end+1)
        return val

class SourceQuery(object):
    """Example usage:

       import SourceQuery
       server = SourceQuery.SourceQuery('1.2.3.4', 27015)
       print server.ping()
       print server.info()
       print server.player()
       print server.rules()
    """

    def __init__(self, host, port=27015, timeout=1.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.udp = False

    def disconnect(self):
        if self.udp:
            self.udp.close()
            self.udp = False

    def connect(self, challenge=False):
        self.disconnect()
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.settimeout(self.timeout)
        self.udp.connect((self.host, self.port))

        if challenge:
            return self.challenge()

    def challenge(self):
        # use A2S_PLAYER to obtain a challenge
        packet = SourceQueryPacket()
        packet.putLong(WHOLE)
        packet.putByte(A2S_PLAYER)
        packet.putLong(CHALLENGE)

        self.udp.send(packet.getvalue())
        packet = SourceQueryPacket(self.udp.recv(PACKETSIZE))

        # this is our challenge packet
        if packet.getLong() == WHOLE \
                and packet.getByte() == S2C_CHALLENGE:
            challenge = packet.getLong()
            return challenge

    def ping(self):
        self.connect()

        packet = SourceQueryPacket()
        packet.putLong(WHOLE)
        packet.putByte(A2A_PING)

        before = time.time()

        self.udp.send(packet.getvalue())
        packet = SourceQueryPacket(self.udp.recv(PACKETSIZE))

        after = time.time()

        if packet.getLong() == WHOLE \
                and packet.getByte() == A2A_PING_REPLY \
                and packet.getString() == A2A_PING_REPLY_STRING:
            return after - before

    def info(self):
        self.connect()

        packet = SourceQueryPacket()
        packet.putLong(WHOLE)
        packet.putByte(A2S_INFO)
        packet.putString(A2S_INFO_STRING)

        self.udp.send(packet.getvalue())
        packet = SourceQueryPacket(self.udp.recv(PACKETSIZE))

        if packet.getLong() == WHOLE \
                and packet.getByte() == A2S_INFO_REPLY:
            result = {}

            result['version'] = packet.getByte()
            result['hostname'] = packet.getString()
            result['map'] = packet.getString()
            result['gamedir'] = packet.getString()
            result['gamedesc'] = packet.getString()
            result['appid'] = packet.getShort()
            result['numplayers'] = packet.getByte()
            result['maxplayers'] = packet.getByte()
            result['numbots'] = packet.getByte()
            result['dedicated'] = chr(packet.getByte())
            result['os'] = chr(packet.getByte())
            result['passworded'] = packet.getByte()
            result['secure'] = packet.getByte()
            result['version'] = packet.getString()
            edf = packet.getByte()

            if edf & 0x80:
                result['port'] = packet.getShort()
            if edf & 0x40:
                result['specport'] = packet.getShort()
                result['specname'] = packet.getString()
            if edf & 0x20:
                result['tag'] = packet.getString()

            return result

    def player(self):
        challenge = self.connect(True)

        # now obtain the actual player info
        packet = SourceQueryPacket()
        packet.putLong(WHOLE)
        packet.putByte(A2S_PLAYER)
        packet.putLong(challenge)

        self.udp.send(packet.getvalue())
        packet = SourceQueryPacket(self.udp.recv(PACKETSIZE*4))

        # this is our player info
        if packet.getLong() == WHOLE \
                and packet.getByte() == A2S_PLAYER_REPLY:
            numplayers = packet.getByte()

            result = []

            # TF2 32player servers may send an incomplete reply
            try:
                for x in xrange(numplayers):
                    player = {}
                    player['index'] = packet.getByte()
                    player['name'] = packet.getString()
                    player['kills'] = packet.getLong()
                    player['time'] = packet.getFloat()
                    result.append(player)

            except:
                pass

            return result

    def rules(self):
        challenge = self.connect(True)

        # now obtain the actual rules
        packet = SourceQueryPacket()
        packet.putLong(WHOLE)
        packet.putByte(A2S_RULES)
        packet.putLong(challenge)

        self.udp.send(packet.getvalue())
        packet = SourceQueryPacket(self.udp.recv(PACKETSIZE))
        print len(packet.getvalue())

        # this is our rules
        if packet.getLong() == WHOLE \
                and packet.getByte() == A2S_RULES_REPLY:
            rules = {}
            numrules = packet.getShort()

            # TF2 sends incomplete packets, so we have to ignore numrules
            while 1:
                try:
                    key = packet.getString()
                    rules[key] = packet.getString()
                except:
                    break

            return rules
