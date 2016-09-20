#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ========================================================================================
# title           : magicblueshell.py
# description     : Python tool to control Magic Blue bulbs over Bluetooth
# author          : Benjamin Piouffle
# date            : 23/11/2015
# usage           : python magicblue.py
# python_version  : 3.4
# ========================================================================================

import argparse
import logging
import os
import sys
import webcolors
from bluepy.btle import Scanner, DefaultDelegate
from sys import platform as _platform
from magicblue.magicbluelib import MagicBlue
from magicblue import __version__

logger = logging.getLogger(__name__)


class MagicBlueShell:
    def __init__(self, bluetooth_adapter):
        # List available commands and their usage. 'con_required' define if we need to be connected to a device for
        # the command to run
        self.available_cmds = [
            {'cmd': 'help', 'func': self.list_commands, 'params': '', 'help': 'Show this help', 'con_required': False},
            {'cmd': 'list_devices', 'func': self.cmd_list_devices, 'params': '', 'help': 'List Bluetooth LE devices in range', 'con_required': False},
            {'cmd': 'ls', 'func': self.cmd_list_devices, 'params': '', 'help': 'Alias for list_devices', 'con_required': False},
            {'cmd': 'connect', 'func': self.cmd_connect, 'params': 'mac_address', 'help': 'Connect to light bulb', 'con_required': False},
            {'cmd': 'disconnect', 'func': self.cmd_disconnect, 'params': '', 'help': 'Disconnect from current light bulb', 'con_required': True},
            {'cmd': 'set_color', 'func': self.cmd_set_color, 'params': 'name|hexvalue', 'help': "Change bulb's color", 'con_required': True},
            {'cmd': 'set_warm_light', 'func': self.cmd_set_warm_light, 'params': 'intensity[0.0-1.0]', 'help': "Set warm light", 'con_required': True},
            {'cmd': 'turn', 'func': self.cmd_turn, 'params': 'on|off', 'help': "Turn on / off the bulb", 'con_required': True},
            {'cmd': 'exit', 'func': self.cmd_exit, 'params': '', 'help': 'Exit the script', 'con_required': False}
        ]
        self.bluetooth_adapter = bluetooth_adapter
        self._magic_blue = None

    def start_interactive_mode(self):
        print('Magic Blue interactive shell v{}'.format(__version__))
        print('Type "help" for a list of available commands')

        str_cmd = ''
        while str_cmd != 'exit':
            try:
                str_cmd = input('> ').strip()
                if str_cmd:
                    self.exec_cmd(str_cmd)
            except (EOFError, KeyboardInterrupt):  # Catch Ctrl+D / Ctrl+C
                self.cmd_exit()
                return
            except Exception as e:
                logger.error('Unexpected error with command "{}": {}'.format(str_cmd, str(e)))

    def exec_cmd(self, str_cmd):
        cmd = self._get_command(str_cmd)
        if cmd is not None:
            if cmd['con_required'] and not (self._magic_blue and self._magic_blue.is_connected()):
                logger.error('You must be connected to magic blue bulb to run this command')
            else:
                if self._check_args(str_cmd, cmd):
                    cmd['func'](str_cmd.split()[1:])
        else:
            logger.error('Command "{}" is not available. Type "help" to see what you can do'.format(str_cmd.split()[0]))

    def print_usage(self, str_cmd):
        cmd = self._get_command(str_cmd)
        if cmd is not None:
            print('Usage: {} {}'.format(cmd['cmd'], cmd['params']))
        else:
            logger.error('Unknow command {}'.format(str_cmd))
        return False

    def cmd_list_devices(self, *args):
        try:
            scanner = Scanner().withDelegate(ScanDelegate())
            print('Listing Bluetooth LE devices in range for 5 minutes. Press CTRL+C to stop searching.')
            print('{: <12} {: <12}'.format('Name', 'Mac address'))
            print('{: <12} {: <12}'.format('----', '-----------'))
            scanner.scan(350)
        except KeyboardInterrupt:
            print('\n')
        except RuntimeError as e:
            logger.error('Problem with the Bluetooth adapter : {}'.format(e))
            return False

    def cmd_connect(self, *args):
        self._magic_blue = MagicBlue(args[0][0])
        self._magic_blue.connect(self.bluetooth_adapter)
        logger.info('Connected')

    def cmd_disconnect(self, *args):
        self._magic_blue.disconnect()
        self._magic_blue = None

    def cmd_turn(self, *args):
        if args[0][0] == 'on':
            self._magic_blue.turn_on()
        else:
            self._magic_blue.turn_off()

    def cmd_set_color(self, *args):
        color = args[0][0]
        try:
            if color.startswith('#'):
                self._magic_blue.set_color(webcolors.hex_to_rgb(color))
            else:
                self._magic_blue.set_color(webcolors.name_to_rgb(color))
        except ValueError as e:
            logger.error('Invalid color value : {}'.format(str(e)))
            self.print_usage('set_color')

    def cmd_set_warm_light(self, *args):
        try:
            self._magic_blue.set_warm_light(float(args[0][0]))
        except ValueError as e:
            logger.error('Invalid intensity value : {}'.format(str(e)))
            self.print_usage('set_color')

    def list_commands(self, *args):
        print(' ----------------------------')
        print('| List of available commands |')
        print(' ----------------------------')
        print('{: <16}{: <25}{}'.format('COMMAND', 'PARAMETERS', 'DETAILS'))
        print('{: <16}{: <25}{}'.format('-------', '----------', '-------'))
        print('\n'.join(['{: <16}{: <25}{}'.format(command['cmd'], command['params'], command['help']) for command in self.available_cmds]))

    def cmd_exit(self, *args):
        print('Bye !')

    def _check_args(self, str_cmd, cmd):
        expected_nb_args = len(cmd['params'].split())
        args = str_cmd.split()[1:]
        if len(args) != expected_nb_args:
            self.print_usage(str_cmd.split()[0])
            return False
        return True

    def _get_command(self, str_cmd):
        str_cmd = str_cmd.split()[0]
        return next((item for item in self.available_cmds if item['cmd'] == str_cmd), None)


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, is_new_device, is_new_data):
        if is_new_device:
            dev_name = dev.getValueText(9).split('\x00')[0]
            print('{: <12} {: <12}'.format(dev_name, dev.addr))

def get_params():
    parser = argparse.ArgumentParser(description='Python tool to control Magic Blue bulbs over Bluetooth')
    parser.add_argument('-l', '--list_commands', dest='list_commands', help='List available commands')
    parser.add_argument('-c', '--command', dest='command', help='Command to execute')
    parser.add_argument('-m', '--mac_address', dest='mac_address', help='Device mac address. Must be set if command given in -c needs you to be connected')
    parser.add_argument('-a', '--bluetooth_adapter', default='hci0', dest='bluetooth_adapter', help='Bluetooth adapter name as listed by hciconfig command')
    return parser.parse_args()


def main():
    # Exit if not root
    if (_platform == "linux" or _platform == "linux2") and os.geteuid() != 0:
        logger.error("Script must be run as root")
        return 1

    params = get_params()
    shell = MagicBlueShell(params.bluetooth_adapter)
    if params.list_commands:
        shell.list_commands()
    elif params.command:
        logging.basicConfig(level=logging.WARNING)
        if params.mac_address:
            shell.cmd_connect([params.mac_address])
        shell.exec_cmd(params.command)
    else:
        logging.basicConfig(level=logging.INFO)
        shell.start_interactive_mode()
    return 0


if __name__ == '__main__':
    sys.exit(main())
