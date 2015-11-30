#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ========================================================================================
# title           : magicbluelib.py
# description     : Python library to control Magic Blue bulbs over Bluetooth
# author          : Benjamin Piouffle
# date            : 23/11/2015
# python_version  : 3.4
# ========================================================================================

import time
import random
from gattlib import GATTRequester, DiscoveryService

# Handles
HANDLE_CHANGE_COLOR = 0x0c

# Magics
MAGIC_CHANGE_COLOR = 0x56


class MagicBlue:
    def __init__(self, mac_address):
        self.mac_address = mac_address
        self._connection = None

    def connect(self):
        self._connection = GATTRequester(self.mac_address, False)
        self._connection.connect(True, "random")
        print('Connected : {}'.format(self.is_connected()))

    def disconnect(self):
        self._connection.disconnect()

    def is_connected(self):
        return self._connection.is_connected()

    def set_color(self, rgb_color):
        """
        Change bulb's color
        :param rgb_color: color as a list of 3 values between 0 and 255
        """
        self._connection.write_by_handle(HANDLE_CHANGE_COLOR, bytes(bytearray([MAGIC_CHANGE_COLOR] + list(rgb_color))))

    def set_random_color(self):
        self.set_color([random.randint(1, 255) for i in range(3)])

    def turn_off(self):
        self.set_color([0, 0, 0])

    def turn_on(self, brightness=1.0):
        """
        Set white color on the light
        :param brightness: a float value between 0.0 and 1.0 defining the brightness
        """
        self.set_color([int(255 * brightness) for i in range(3)])


# def search_magic_blue(timeout):
#     service = DiscoveryService()
#
#     # Search for Magic Blue
#     print('Searching for Magic Blue bulb...')
#     while timeout >= 0:
#         devices = service.discover(2)
#         # TODO: Find another way to recognize than MAC
#         magic_blue_mac_address = next((address for address, name in devices.items() if address == MAGIC_BLUE_MAC), None)
#         if magic_blue_mac_address is not None:
#             return magic_blue_mac_address
#         time.sleep(1)
#         timeout -= 1
#
#     raise RuntimeError('Magic blue not found !')
