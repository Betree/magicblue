#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ==============================================================================
# title           : magicblue.py
# description     : Python script and library to control Magic Blue bulbs over Bluetooth
# author          : Benjamin Piouffle
# date            : 23/11/2015
# usage           : python magicblue.py
# python_version  : 3.4
# ==============================================================================

import os
import sys
from bluetooth.ble import DiscoveryService
from sys import platform as _platform


__version__ = 0.1


def main():
    # Ask sudo on Linux
    if _platform == "linux" or _platform == "linux2":
        if os.geteuid() != 0:
            print("Script must be run as root")
            args = ['sudo', sys.executable] + sys.argv + [os.environ]
            os.execlpe('sudo', *args)
        else:
            print('Ok !')

    service = DiscoveryService()
    devices = service.discover(2)

    for address, name in devices.items():
        print("name: {}, address: {}".format(name, address))
    return 0


if __name__ == '__main__':
    sys.exit(main())
