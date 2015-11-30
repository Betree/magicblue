#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ========================================================================================
# title           : magicblue.py
# description     : Python tool to control Magic Blue bulbs over Bluetooth
# author          : Benjamin Piouffle
# date            : 23/11/2015
# usage           : python magicblue.py
# python_version  : 3.4
# ========================================================================================

import os
import sys
import time
import webcolors
from sys import platform as _platform
from gattlib import DiscoveryService
from magicbluelib import MagicBlue


__version__ = 0.1


class InteractiveShellCommands:
    def __init__(self):
        self.available_cmds = [
            {'cmd': 'help', 'func': self._cmd_help, 'params': '', 'help': 'Show this help', 'con_required': False},
            {'cmd': 'list_devices', 'func': self._cmd_list_devices, 'params': '', 'help': 'List Bluetooth LE devices in range', 'con_required': False},
            {'cmd': 'connect', 'func': self._cmd_connect, 'params': 'mac_address', 'help': 'Connect to light bulb', 'con_required': False},
            {'cmd': 'disconnect', 'func': self._cmd_disconnect, 'params': '', 'help': 'Disconnect from current light bulb', 'con_required': True},
            {'cmd': 'set_color', 'func': self._cmd_set_color, 'params': 'name|hexvalue', 'help': "Change bulb's color", 'con_required': True},
            {'cmd': 'turn', 'func': self._cmd_turn, 'params': 'on|off', 'help': "Turn on / off the bulb", 'con_required': True},
            {'cmd': 'exit', 'func': self._cmd_exit, 'params': '', 'help': 'Exit the script', 'con_required': False}
        ]
        self._magic_blue = None

    def start(self):
        print('Magic Blue interactive shell v{}'.format(__version__))
        print('Type "help" to see what you can do')

        try:
            str_cmd = input('> ')
            while str_cmd != 'exit':
                cmd = self._get_command(str_cmd)
                if cmd is not None:
                    if cmd['con_required'] and not (self._magic_blue and self._magic_blue.is_connected()):
                        print('You must be connected to magic blue bulb to run this command')
                    else:
                        if self._check_args(str_cmd, cmd):
                            cmd['func'](str_cmd.split()[1:])
                else:
                    print('Command "{}" is not available. Type "help" to see what you can do'.format(str_cmd.split()[0]))
                str_cmd = input('> ')
        except EOFError:  # Catch CTRL+D
            self._cmd_exit()

    def print_usage(self, str_cmd):
        cmd = self._get_command(str_cmd)
        if cmd is not None:
            print('Usage: {} {}'.format(cmd['cmd'], cmd['params']))
        else:
            print('Unknow command {}'.format(str_cmd))
        return False

    def _check_args(self, str_cmd, cmd):
        expected_nb_args = len(cmd['params'].split())
        args = str_cmd.split()[1:]
        if len(args) != expected_nb_args:
            self.print_usage(str_cmd.split()[0])
            return False
        return True

    def _cmd_list_devices(self, *args):
        print('Listing Bluetooth LE devices in range. Press CTRL+C to stop searching.')
        service = DiscoveryService()

        print('{: <12} {: <12}'.format('Name', 'Mac address'))
        print('{: <12} {: <12}'.format('----', '-----------'))

        try:
            while 42:
                for device_mac, device_name in service.discover(2).items():
                    print('{: <12} {: <12}'.format(device_name, device_mac))
                print('---------------')
                time.sleep(1)
        except KeyboardInterrupt:
            print('\n')

    def _cmd_connect(self, *args):
        self._magic_blue = MagicBlue(args[0][0])
        self._magic_blue.connect()

    def _cmd_disconnect(self, *args):
        self._magic_blue.disconnect()
        self._magic_blue = None

    def _cmd_turn(self, *args):
        if args[0][0] == 'on':
            self._magic_blue.turn_on()
        else:
            self._magic_blue.turn_off()

    def _cmd_set_color(self, *args):
        color = args[0][0]
        try:
            if color.startswith('#'):
                self._magic_blue.set_color(webcolors.hex_to_rgb(color))
            else:
                self._magic_blue.set_color(webcolors.name_to_rgb(color))
        except ValueError as e:
            print('Invalid color value : {}'.format(str(e)))
            self.print_usage('set_color')

    def _cmd_help(self, *args):
        print(' ----------------------------')
        print('| List of available commands |')
        print(' ----------------------------')
        print('{: <16}{: <25}{}'.format('COMMAND', 'PARAMETERS', 'DETAILS'))
        print('{: <16}{: <25}{}'.format('-------', '----------', '-------'))
        print('\n'.join(['{: <16}{: <25}{}'.format(command['cmd'], command['params'], command['help']) for command in self.available_cmds]))

    def _cmd_exit(self, *args):
        print('Bye !')

    def _get_command(self, str_cmd):
        str_cmd = str_cmd.split()[0]
        return next((item for item in self.available_cmds if item['cmd'] == str_cmd), None)


def main():
    # TODO : Get cmd line option -m 'mac_address', -c 'command'

    # Ask Root on Linux
    if _platform == "linux" or _platform == "linux2":
        if os.geteuid() != 0:
            print("Script must be run as root")
            args = ['sudo', sys.executable] + sys.argv + [os.environ]
            os.execlpe('sudo', *args)

    shell = InteractiveShellCommands()
    shell.start()
    return 0


if __name__ == '__main__':
    sys.exit(main())
