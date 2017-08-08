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
from enum import Enum

from bluepy import btle


__all__ = ['MagicBlue', 'Effect']


logger = logging.getLogger(__name__)


UUID_CHARACTERISTIC_RECV = btle.UUID('ffe4')
UUID_CHARACTERISTIC_WRITE = btle.UUID('ffe9')
UUID_CHARACTERISTIC_DEVICE_NAME = btle.UUID('2a00')


def connection_required(func):
    """Raise an exception before calling the actual function if the device is
    not connection.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._connection is None:
            raise Exception("Not connected")

        return func(self, *args, **kwargs)

    return wrapper


def _figure_addr_type(mac_address=None, version=None, addr_type=None):
    # addr_type rules all
    if addr_type is not None:
        return addr_type

    # prefer version
    if version == 9 or version == 10:
        return btle.ADDR_TYPE_PUBLIC

    if version == 8:
        return btle.ADDR_TYPE_RANDOM
    
    # try using mac_address
    if mac_address is not None:
        mac_address_num = int(mac_address.replace(':', ''), 16)
        if mac_address_num & 0xF00000000000 == 0xF00000000000:
            return btle.ADDR_TYPE_PUBLIC

    return btle.ADDR_TYPE_RANDOM


class Effect(Enum):
    """
    Effect
    """
    seven_color_cross_fade = 0x25
    red_gradual_change = 0x26
    green_gradual_change = 0x27
    blue_gradual_change = 0x28
    yellow_gradual_change = 0x29
    cyan_gradual_change = 0x2a
    purple_gradual_change = 0x2b
    white_gradual_change = 0x2c
    red_green_cross_fade = 0x2d
    red_blue_cross_fade = 0x2e
    green_blue_cross_fade = 0x2f
    seven_color_stobe_flash = 0x30
    red_strobe_flash = 0x31
    green_strobe_flash = 0x32
    blue_strobe_flash = 0x33
    yellow_strobe_flash = 0x34
    cyan_strobe_flash = 0x35
    purple_strobe_flash = 0x36
    white_strobe_flash = 0x37
    seven_color_jumping_change = 0x38


class MagicBlue:
    """
    Class to interface with Magic Blue light
    """

    def __init__(self, mac_address, version=7, addr_type=None):
        """
        :param mac_address: device MAC address as a string
        :param version: bulb version as displayed in official app (integer)
        :return:
        """
        self._connection = None

        self.mac_address = mac_address
        self.version = version
        self._addr_type = _figure_addr_type(mac_address, version, addr_type)

        self._device_info = {}
        self._date_time = None

    def connect(self, bluetooth_adapter_nr=0):
        """
        Connect to device
        :param  bluetooth_adapter_nr: bluetooth adapter name as shown by
                "hciconfig" command. Default : 0 for (hci0)
        :return: True if connection succeed, False otherwise
        """
        logger.debug("Connecting...")

        try:
            connection = btle.Peripheral(self.mac_address, self._addr_type,
                                         bluetooth_adapter_nr)
            self._connection = connection.withDelegate(self)
            self._subscribe_to_recv_characteristic()
        except RuntimeError as e:
            logger.error('Connection failed : {}'.format(e))
            return False

        return True

    def disconnect(self):
        """
        Disconnect from device
        """
        logger.debug("Disconnecting...")

        try:
            self._connection.disconnect()
        except btle.BTLEException:
            pass

        self._connection = None

    def is_connected(self):
        """
        :return: True if connected
        """
        return self._connection is not None  # and self.test_connection()

    def test_connection(self):
        """
        Test if the connection is still alive
        """
        if not self.is_connected():
            return False

        # send test message, read bulb name
        try:
            self.get_device_name()
        except btle.BTLEException:
            self.disconnect()
            return False
        except BrokenPipeError:
            # bluepy-helper died
            self._connection = None
            return False

        return True

    @connection_required
    def get_device_name(self):
        """
        :return: Device name
        """
        buffer = self._device_name_characteristic.read()
        buffer = buffer.replace(b'\x00', b'')
        return buffer.decode('ascii')

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
        self._send_characteristic.write(msg)

    @connection_required
    def set_color(self, rgb_color):
        """
        Change bulb's color
        :param rgb_color: color as a list of 3 values between 0 and 255
        """
        msg = Protocol.encode_set_rgb(*rgb_color)
        self._send_characteristic.write(msg)

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
        self._send_characteristic.write(msg)

    @connection_required
    def turn_on(self, brightness=None):
        """
        Set white color on the light
        :param brightness:  a float value between 0.0 and 1.0 defining the
                            brightness
        """
        msg = Protocol.encode_turn_on()
        self._send_characteristic.write(msg)

        if brightness is not None:
            self.set_warm_light(brightness)

    @connection_required
    def get_device_info(self):
        """
        Retrieve device info
        """
        msg = Protocol.encode_request_device_info()
        self._send_characteristic.write(msg, True)
        return self._device_info

    @connection_required
    def set_date_time(self, datetime_):
        """
        Set date/time in bulb
        :param datetime_:  datetime to set
        """
        msg = Protocol.encode_set_date_time(datetime_)
        self._send_characteristic.write(msg)

    @connection_required
    def get_date_time(self):
        """
        Retrieve date/time from bulb
        """
        msg = Protocol.encode_request_date_time()
        self._send_characteristic.write(msg, True)
        return self._date_time

    @connection_required
    def set_effect(self, effect, effect_speed):
        """
        Set an effect, with effect_speed as speed
        :param effect: magicblue.Effect
        :param effect_speed: integer (range: 1..20), where
          each unit represents around 200ms
        """
        effect_no = effect.value
        msg = Protocol.encode_set_effect(effect_no, effect_speed)
        self._send_characteristic.write(msg)

    def handleNotification(self, handle, buffer):
        logger.debug("Got notification, handle: {}, buffer: {}".format(handle,
                                                                       buffer))

        if len(buffer) >= 11 and buffer[0] == 0x66 and buffer[11] == 0x99:
            self._device_info = Protocol.decode_device_info(buffer)

        if len(buffer) >= 10 and buffer[0] == 0x13 and buffer[10] == 0x31:
            self._date_time = Protocol.decode_date_time(buffer)

    def __str__(self):
        return "<MagicBlue({}, {})>".format(self.mac_address, self.version)

    @property
    def _send_characteristic(self):
        """Get BTLE characteristic for sending commands"""
        characteristics = self._connection.getCharacteristics(
                uuid=UUID_CHARACTERISTIC_WRITE)
        if not characteristics:
            return None
        return characteristics[0]

    @property
    def _recv_characteristic(self):
        """Get BTLE characteristic for receiving data"""
        characteristics = self._connection.getCharacteristics(
                uuid=UUID_CHARACTERISTIC_RECV)
        if not characteristics:
            return None
        return characteristics[0]

    @property
    def _device_name_characteristic(self):
        """Get BTLE characteristic for reading device name"""
        characteristics = self._connection.getCharacteristics(
                uuid=UUID_CHARACTERISTIC_DEVICE_NAME)
        if not characteristics:
            return None
        return characteristics[0]

    def _subscribe_to_recv_characteristic(self):
        char = self._recv_characteristic
        handle = char.valHandle + 1
        msg = bytearray([0x01, 0x00])
        self._connection.writeCharacteristic(handle, msg)


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
        year = datetime_.year - 2000
        return bytearray([0x10, 0x14,
                          year, datetime_.month, datetime_.day,
                          datetime_.hour, datetime_.minute, datetime_.second,
                          day_of_week,
                          0x00, 0x01])

    @staticmethod
    def encode_set_effect(effect_no, effect_speed):
        """
        Construct a message to set effect
        """
        return bytearray([0xBB, effect_no, effect_speed, 0x44])

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
            'device_type':  buffer[1],
            'on':           buffer[2] == 0x23,
            'effect_no':    buffer[3],
            'effect':       None,
            'effect_speed': buffer[5],
            'r':            buffer[6],
            'g':            buffer[7],
            'b':            buffer[8],
            'brightness':   buffer[9],
            'version':      buffer[10],
        }
        try:
            effect_no = info['effect_no']
            info['effect'] = Effect(effect_no)
        except ValueError:
            pass
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
