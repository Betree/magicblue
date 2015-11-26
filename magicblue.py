#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ========================================================================================
# title           : magicblue.py
# description     : Python script and library to control Magic Blue bulbs over Bluetooth
# author          : Benjamin Piouffle
# date            : 23/11/2015
# usage           : python magicblue.py
# python_version  : 3.4
# ========================================================================================

import argparse
import os
import random
import sys
import time
from gattlib import GATTRequester, DiscoveryService
from sys import platform as _platform

__version__ = 0.1

MAGIC_BLUE_MAC = 'C7:17:1D:43:39:03'

# Handles
HANDLE_CHANGE_COLOR = 0x0c


class MagicBlue:
    def __init__(self, mac_address):
        self.mac_address = mac_address
        self.connection = None

    def connect(self):
        self.connection = GATTRequester(self.mac_address, False)
        self.connection.connect(True, "random")
        print('Connected : {}'.format(self.connection.is_connected()))

    def disconnect(self):
        self.connection.disconnect()

    def set_color(self, rgb_color):
        """
        Change bulb's color
        :param rgb_color: color as a list of 3 values between 0 and 255
        """
        self.connection.write_by_handle(HANDLE_CHANGE_COLOR, bytes(bytearray([0x56] + rgb_color)))

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


def parse_cmd():
    parser = argparse.ArgumentParser(description='Utility to manage a Magic Blue bulb over Bluetooth LE')
    parser.add_argument('-t', '--timeout', default=10, help='Number of seconds before devices search timeout')
    return parser.parse_args()


def search_magic_blue(timeout):
    service = DiscoveryService()

    # Search for Magic Blue
    print('Searching for Magic Blue bulb...')
    while timeout >= 0:
        devices = service.discover(2)
        # TODO: Find another way to recognize than MAC
        magic_blue_mac_address = next((address for address, name in devices.items() if address == MAGIC_BLUE_MAC), None)
        if magic_blue_mac_address is not None:
            return magic_blue_mac_address
        time.sleep(1)
        timeout -= 1

    raise RuntimeError('Magic blue not found !')


def main():
    # Ask Root on Linux
    if _platform == "linux" or _platform == "linux2":
        if os.geteuid() != 0:
            print("Script must be run as root")
            args = ['sudo', sys.executable] + sys.argv + [os.environ]
            os.execlpe('sudo', *args)

    # cmd_options = parse_cmd()
    # Get bluetooth interface
    # mac_address = search_magic_blue(service, cmd_options.timeout)
    mac_address = MAGIC_BLUE_MAC

    magic_blue = MagicBlue(mac_address)
    magic_blue.connect()
    return 0


if __name__ == '__main__':
    sys.exit(main())
