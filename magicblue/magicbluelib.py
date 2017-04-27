#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# =============================================================================
# title           : magicbluelib.py
# description     : Python library to control Magic Blue bulbs over Bluetooth
# author          : Benjamin Piouffle
# date            : 23/11/2015
# python_version  : 3.4
# =============================================================================
import logging
import random

import pygatt


__all__ = ['MagicBlue']


logger = logging.getLogger(__name__)

# Magics
MAGIC_CHANGE_COLOR = 0x56


class MagicBlue:
    def __init__(self, mac_address, version=7):
        """
        :param mac_address: device MAC address as a string
        :param version: bulb version as displayed in official app (integer)
        :return:
        """
        self.mac_address = mac_address
        self._adapter = None
        self._device = None

        if version == 9 or version == 10:
            self._addr_type = pygatt.BLEAddressType.public
            self._handle_change_color = 0x0b
        else:
            self._addr_type = pygatt.BLEAddressType.random
            self._handle_change_color = 0x0c

    def connect(self, bluetooth_adapter_nr=0):
        """
        Connect to device
        :param  bluetooth_adapter_nr: bluetooth adapter name as shown by
                "hciconfig" command. Default : 0 for (hci0)
        :return: True if connection succeed, False otherwise
        """
        hci_device = 'hci{}'.format(bluetooth_adapter_nr)

        try:
            self._adapter = pygatt.GATTToolBackend(hci_device=hci_device)
            self._adapter.start()

            self._device = self._adapter.connect(
                    self.mac_address, address_type=self._addr_type)
        except RuntimeError as e:
            logger.error('Connection failed : {}'.format(e))
            return False
        return True

    def disconnect(self):
        """
        Disconnect from device
        """
        self._device.disconnect()
        self._device = None

        self._adapter.stop()
        self._adapter = None

    def is_connected(self):
        """
        :return: True if connected
        """
        return self._device is not None

    def set_warm_light(self, intensity=1.0):
        """
        Equivalent of what they call the "Warm light" property in the app that
        is a strong wight / yellow color, stronger that any value you may get
        by setting rgb color.
        :param intensity: the intensity between 0.0 and 1.0

        """
        msg = bytearray([MAGIC_CHANGE_COLOR, 0, 0, 0,
                         int(intensity * 255), 0x0f, 0xaa, 0x09])
        self._device.char_write_handle(self._handle_change_color, msg)

    def set_color(self, rgb_color):
        """
        Change bulb's color
        :param rgb_color: color as a list of 3 values between 0 and 255
        """
        msg = bytearray([MAGIC_CHANGE_COLOR] + list(rgb_color) +
                        [0x00, 0xf0, 0xaa])
        self._device.char_write_handle(self._handle_change_color, msg)

    def set_random_color(self):
        """
        Change bulb's color with a random color
        """
        self.set_color([random.randint(1, 255) for i in range(3)])

    def turn_off(self):
        """
        Turn off the light
        """
        msg = bytearray([0xCC, 0x24, 0x33])
        self._device.char_write_handle(self._handle_change_color, msg)

    def turn_on(self, brightness=None):
        """
        Set white color on the light
        :param brightness:  a float value between 0.0 and 1.0 defining the
                            brightness
        """
        if brightness is None:
            msg = bytearray([0xCC, 0x23, 0x33])
            self._device.char_write_handle(self._handle_change_color, msg)
        else:
            self.set_color([int(255 * brightness) for i in range(3)])
