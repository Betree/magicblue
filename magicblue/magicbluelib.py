#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# =============================================================================
# title           : magicbluelib.py
# description     : Python library to control Magic Blue bulbs over Bluetooth
# author          : Benjamin Piouffle
# date            : 23/11/2015
# python_version  : 3.4
# =============================================================================
import functools
import logging
import random
from datetime import datetime, date, time

import pygatt
from pygatt.util import uuid16_to_uuid
from pygatt.exceptions import BLEError, NotConnectedError


__all__ = ['MagicBlue']


logger = logging.getLogger(__name__)


UUID_CHARACTERISTIC_RECV = uuid16_to_uuid(0xffe4)
UUID_CHARACTERISTIC_WRITE = uuid16_to_uuid(0xffe9)
UUID_CHARACTERISTIC_DEVICE_NAME = uuid16_to_uuid(0x2a00)


def connection_required(func):
    """Raise an exception before calling the actual function if the device is
    not connection.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self._device:
            raise NotConnectedError()

        return func(self, *args, **kwargs)

    return wrapper


def _figure_addr_type(mac_address=None, version=None):
    # prefer version
    if version == 9 or version == 10:
        return pygatt.BLEAddressType.public

    # try using mac_address
    if mac_address is not None:
        mac_address_num = int(mac_address.replace(':', ''), 16)
        if mac_address_num & 0xF00000000000 == 0xF00000000000:
            return pygatt.BLEAddressType.public

    return pygatt.BLEAddressType.random


class MagicBlue:
    """
    Class to interface with Magic Blue light
    """

    def __init__(self, mac_address, version=7):
        """
        :param mac_address: device MAC address as a string
        :param version: bulb version as displayed in official app (integer)
        :return:
        """
        self._adapter = None
        self._device = None

        self.mac_address = mac_address
        self.version = version

        self._device_info = {}
        self._date_time = None

    def connect(self, bluetooth_adapter_nr=0):
        """
        Connect to device
        :param  bluetooth_adapter_nr: bluetooth adapter name as shown by
                "hciconfig" command. Default : 0 for (hci0)
        :return: True if connection succeed, False otherwise
        """
        hci_device = 'hci{}'.format(bluetooth_adapter_nr)
        addr_type = _figure_addr_type(self.mac_address, self.version)

        try:
            self._adapter = pygatt.GATTToolBackend(hci_device=hci_device)
            self._adapter.start()

            self._device = self._adapter.connect(
                self.mac_address, address_type=addr_type)
            self._device.subscribe(
                UUID_CHARACTERISTIC_RECV, self._notification_handler)
        except RuntimeError as e:
            logger.error('Connection failed : {}'.format(e))
            return False

        return True

    def disconnect(self):
        """
        Disconnect from device
        """
        try:
            self._device.disconnect()
        except BLEError:
            pass
        self._device = None

        try:
            self._adapter.stop()
        except BLEError:
            pass
        self._adapter = None

    def is_connected(self):
        """
        :return: True if connected
        """
        return self._device is not None  # and self.test_connection()

    def test_connection(self):
        """
        Test if the connection is still alive
        """
        if not self.is_connected():
            return False

        # send test message, read bulb name
        try:
            self.get_device_name()
        except NotConnectedError:
            self.disconnect()
            return False

        return True

    @connection_required
    def get_device_name(self):
        """
        :return: Device name
        """
        # somehow, we have to read the handle and cannot read the UUID
        handle = self._device.get_handle(UUID_CHARACTERISTIC_DEVICE_NAME)
        return self._device.char_read_handle(handle)

    @connection_required
    def set_warm_light(self, intensity=1.0):
        """
        Equivalent of what they call the "Warm light" property in the app that
        is a strong white / yellow color, stronger that any value you may get
        by setting rgb color.
        :param intensity: the intensity between 0.0 and 1.0
        """
        brightness = int(intensity * 255)
        msg = Protocol.encode_set_brightness(brightness)
        self._device.char_write(UUID_CHARACTERISTIC_WRITE, msg)

    @connection_required
    def set_color(self, rgb_color):
        """
        Change bulb's color
        :param rgb_color: color as a list of 3 values between 0 and 255
        """
        msg = Protocol.encode_set_rgb(*rgb_color)
        self._device.char_write(UUID_CHARACTERISTIC_WRITE, msg)

    @connection_required
    def set_random_color(self):
        """
        Change bulb's color with a random color
        """
        self.set_color([random.randint(1, 255) for i in range(3)])

    @connection_required
    def turn_off(self):
        """
        Turn off the light
        """
        msg = Protocol.encode_turn_off()
        self._device.char_write(UUID_CHARACTERISTIC_WRITE, msg)

    @connection_required
    def turn_on(self, brightness=None):
        """
        Set white color on the light
        :param brightness:  a float value between 0.0 and 1.0 defining the
                            brightness
        """
        msg = Protocol.encode_turn_on()
        self._device.char_write(UUID_CHARACTERISTIC_WRITE, msg)

        if brightness is not None:
            self.set_warm_light(brightness)

    @connection_required
    def request_device_info(self):
        """
        Retrieve device info
        """
        msg = Protocol.encode_request_device_info()
        self._device.char_write(UUID_CHARACTERISTIC_WRITE, msg, True)
        return self._device_info

    @connection_required
    def set_date_time(self, datetime_):
        """
        Set date/time in bulb
        :param datetime_:  datetime to set
        """
        msg = Protocol.encode_set_date_time(datetime_)
        self._device.char_write(UUID_CHARACTERISTIC_WRITE, msg)

    @connection_required
    def request_date_time(self):
        """
        Retrieve date/time from bulb
        """
        msg = Protocol.encode_request_date_time()
        self._device.char_write(UUID_CHARACTERISTIC_WRITE, msg, True)
        return self._date_time

    def _notification_handler(self, handle, buffer):
        logger.debug("Got notification, handle: {}, buffer: {}".format(handle, buffer))

        if len(buffer) >= 11 and buffer[0] == 0x66 and buffer[11] == 0x99:
            self._device_info = Protocol.decode_device_info(buffer)

        if len(buffer) >= 10 and buffer[0] == 0x13 and buffer[10] == 0x31:
            self._date_time = Protocol.decode_date_time(buffer)

    def __str__(self):
        return "<MagicBlue({}, {})>".format(self.mac_address, self.version)


class Protocol:
    """
    Protocol encoding/decoding for the bulb
    """

    @staticmethod
    def encode_set_brightness(brightness):
        """
        Construct a message to set brightness
        """
        return bytearray([0x56, 0x00, 0x00, 0x00, brightness, 0x0F, 0xAA])

    @staticmethod
    def encode_set_rgb(red, green, blue):
        """
        Construct a message to set RGB
        """
        return bytearray([0x56, red, green, blue, 0x00, 0xF0, 0xAA])

    @staticmethod
    def encode_turn_on():
        """
        Construct a message to turn on
        """
        return bytearray([0xCC, 0x23, 0x33])

    @staticmethod
    def encode_turn_off():
        """
        Construct a message to turn off
        """
        return bytearray([0xCC, 0x24, 0x33])

    @staticmethod
    def encode_set_date_time(datetime_):
        """
        Construct a message to set date/time
        """
        # python: 1-7 --> monday-sunday
        # bulb:   1-7 --> sunday-saturday
        day_of_week = (datetime_.isoweekday() + 1) % 7 or 7
        year = datetime.year - 2000
        return bytearray([0x10, 0x14,
                          year, datetime_.month, datetime_.day,
                          datetime_.hour, datetime_.minute, datetime_.second,
                          day_of_week,
                          0x00, 0x01])

    @staticmethod
    def encode_request_device_info():
        """
        Construct a message to request device info
        """
        return bytearray([0xEF, 0x01, 0x77])

    @staticmethod
    def encode_request_date_time():
        """
        Construct a message to request date/time
        """
        return bytearray([0x12, 0x1A, 0x1B, 0x21])

    @staticmethod
    def decode_device_info(buffer):
        """
        Decode a message with device info
        """
        info = {
            'device_type': buffer[1],
            'power_on':    buffer[2] == 0x23,
            'r':           buffer[6],
            'g':           buffer[7],
            'b':           buffer[8],
            'brightness':  buffer[9],
            'version':     buffer[10],
        }
        return info

    @staticmethod
    def decode_date_time(buffer):
        """
        Decode a message with the date/time
        """
        year = buffer[2] + 2000
        month = buffer[3]
        day = buffer[4]
        date_ = date(year, month, day)

        hour = buffer[5]
        minute = buffer[6]
        second = buffer[7]
        time_ = time(hour, minute, second)

        return datetime.combine(date_, time_)
