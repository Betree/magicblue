#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ========================================================================================
# title           : magicbluelib.py
# description     : Python library to control Magic Blue bulbs over Bluetooth
# author          : Benjamin Piouffle
# date            : 23/11/2015
# python_version  : 3.4
# ========================================================================================
import logging
import random
from gattlib import GATTRequester

__all__ = ['MagicBlue']

logger = logging.getLogger(__name__)

# Handles
HANDLE_CHANGE_COLOR = 0x0c

# Magics
MAGIC_CHANGE_COLOR = 0x56


class MagicBlue:
    def __init__(self, mac_address):
        self.mac_address = mac_address
        self._connection = None

    def connect(self, bluetooth_adapter='hci0'):
        """
        Connect to device
        :param bluetooth_adapter: bluetooth adapter name as shown by "hciconfig" command. Default : "hci0"
        :return: True if connection succeed, False otherwise
        """
        try:
            self._connection = GATTRequester(self.mac_address, False, bluetooth_adapter)
            self._connection.connect(True, "random")
        except RuntimeError as e:
            logger.error('Connection failed : {}'.format(e))
            return False
        return True

    def disconnect(self):
        """
        Disconnect from device
        """
        self._connection.disconnect()

    def is_connected(self):
        """
        :return: True if connection succeed, False otherwise
        """
        return self._connection.is_connected()

    def set_warm_light(self, intensity=1.0):
        """
        Equivalent of what they call the "Warm light" property in the app that is a strong wight / yellow color, stronger that any value you may get by
        setting rgb color.
        :param intensity: the intensity between 0.0 and 1.0

        """
        self._connection.write_by_handle(HANDLE_CHANGE_COLOR, bytes(bytearray([MAGIC_CHANGE_COLOR, 0, 0, 0, int(intensity * 255)])))

    def set_color(self, rgb_color):
        """
        Change bulb's color
        :param rgb_color: color as a list of 3 values between 0 and 255
        """
        self._connection.write_by_handle(HANDLE_CHANGE_COLOR, bytes(bytearray([MAGIC_CHANGE_COLOR] + list(rgb_color) + [0x00, 0xf0, 0xaa])))

    def set_random_color(self):
        """
        Change bulb's color with a random color
        """
        self.set_color([random.randint(1, 255) for i in range(3)])

    def turn_off(self):
        """
        Turn off the light by setting color to black (rgb(0,0,0))
        """
        self.set_color([0, 0, 0])

    def turn_on(self, brightness=1.0):
        """
        Set white color on the light
        :param brightness: a float value between 0.0 and 1.0 defining the brightness
        """
        self.set_color([int(255 * brightness) for i in range(3)])
