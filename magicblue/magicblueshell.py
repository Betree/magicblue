#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# =============================================================================
# title           : magicblueshell.py
# description     : Python tool to control Magic Blue bulbs over Bluetooth
# author          : Benjamin Piouffle
# date            : 23/11/2015
# usage           : python magicblue.py
# python_version  : 3.4
# =============================================================================

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
    class Cmd:
        def __init__(self, cmd_str, func, conn_required, help='', params=None,
                     aliases=None):
            self.cmd_str = cmd_str
            self.func = func
            self.conn_required = conn_required
            self.help = help
            self.params = params or []
            self.aliases = aliases or []

    def __init__(self, bluetooth_adapter, bulb_version=7):
        # List available commands and their usage. 'con_required' define if
        # we need to be connected to a device for the command to run
        self.available_cmds = [
            MagicBlueShell.Cmd('help', self.list_commands, False,
                               help='Show this help'),
            MagicBlueShell.Cmd('list_devices', self.cmd_list_devices, False,
                               help='List Bluetooth LE devices in range',
                               aliases=['ls']),
            MagicBlueShell.Cmd('connect', self.cmd_connect, False,
                               help='Connect to light bulb',
                               params=['mac_address or ID']),
            MagicBlueShell.Cmd('disconnect', self.cmd_disconnect, True,
                               help='Disconnect from current light bulb'),
            MagicBlueShell.Cmd('set_color', self.cmd_set_color, True,
                               help="Change bulb's color",
                               params=['name or hexadecimal value']),
            MagicBlueShell.Cmd('set_warm_light', self.cmd_set_warm_light, True,
                               help='Set warm light',
                               params=['intensity[0.0-1.0]']),
            MagicBlueShell.Cmd('turn', self.cmd_turn, True,
                               help='Turn on / off the bulb',
                               params=['on|off']),
            MagicBlueShell.Cmd('exit', self.cmd_exit, False,
                               help='Exit the script')
        ]

        self.bluetooth_adapter = bluetooth_adapter
        self._bulb_version = bulb_version
        self._magic_blue = None
        self.last_scan = None

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
                logger.error('Unexpected error with command "{}": {}'
                             .format(str_cmd, str(e)))

    def exec_cmd(self, str_cmd):
        cmd = self._get_command(str_cmd)
        if cmd is not None:
            if cmd.conn_required and not (self._magic_blue and
                                          self._magic_blue.is_connected()):
                logger.error('You must be connected to run this command')
            elif self._check_args(str_cmd, cmd):
                cmd.func(str_cmd.split()[1:])
        else:
            logger.error('"{}" is not a valid command.'
                         'Type "help" to see what you can do'
                         .format(str_cmd.split()[0]))

    def print_usage(self, str_cmd):
        cmd = self._get_command(str_cmd)
        if cmd is not None:
            print('Usage: {} {}'.format(cmd.cmd_str, ' '.join(cmd.params)))
        else:
            logger.error('Unknown command {}'.format(str_cmd))
        return False

    def cmd_list_devices(self, *args):
        try:
            self.last_scan = ScanDelegate()
            scanner = Scanner().withDelegate(self.last_scan)
            print('Listing Bluetooth LE devices in range for 5 minutes.'
                  'Press CTRL+C to stop searching.')
            print('{: <5} {: <30} {: <12}'.format('ID', 'Name', 'Mac address'))
            print('{: <5} {: <30} {: <12}'.format('--', '----', '-----------'))
            scanner.scan(350)
        except KeyboardInterrupt:
            print('\n')
        except RuntimeError as e:
            logger.error('Problem with the Bluetooth adapter : {}'.format(e))
            return False

    def cmd_connect(self, *args):
        # Use can enter either a mac address or the device ID from the list
        if len(args[0][0]) < 4 and self.last_scan:
            try:
                dev_id = int(args[0][0]) - 1
                mac_address = self.last_scan.devices[dev_id].addr
            except Exception:
                logger.error('Bad ID / MAC address : {}'.format(args[0][0]))
                return False
        else:
            mac_address = args[0][0]
        self._magic_blue = MagicBlue(mac_address, self._bulb_version)
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
        print('{: <16}{: <30}{}'.format('COMMAND', 'PARAMETERS', 'DETAILS'))
        print('{: <16}{: <30}{}'.format('-------', '----------', '-------'))
        for command in self.available_cmds:
            print('{: <16}{: <30}{}'.format(
                    command.cmd_str, ' '.join(command.params), command.help))
            for alias in command.aliases:
                print('{: <16}{: <30}{}'.format(alias, '//', '//'))

    def cmd_exit(self, *args):
        print('Bye !')

    def _check_args(self, str_cmd, cmd):
        expected_nb_args = len(cmd.params)
        args = str_cmd.split()[1:]
        if len(args) != expected_nb_args:
            self.print_usage(str_cmd.split()[0])
            return False
        return True

    def _get_command(self, str_cmd):
        str_cmd = str_cmd.split()[0]
        return next((item for item in self.available_cmds
                     if item.cmd_str == str_cmd or str_cmd in item.aliases
                     ), None)


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.devices = []

    def handleDiscovery(self, dev, is_new_device, is_new_data):
        if is_new_device:
            self.devices.append(dev)
            dev_name = dev.getValueText(9).split('\x00')[0]
            print('{: <5} {: <30} {: <12}'.format(len(self.devices),
                                                  dev_name, dev.addr))


def get_params():
    parser = argparse.ArgumentParser(description='Python tool to control Magic'
                                                 'Blue bulbs over Bluetooth')
    parser.add_argument('-l', '--list_commands',
                        dest='list_commands',
                        help='List available commands')
    parser.add_argument('-c', '--command',
                        dest='command',
                        help='Command to execute')
    parser.add_argument('-m', '--mac_address',
                        dest='mac_address',
                        help='Device mac address. Must be set if command given'
                             ' in -c needs you to be connected')
    parser.add_argument('-a', '--bluetooth_adapter',
                        default='hci0',
                        dest='bluetooth_adapter',
                        help='Bluetooth adapter name as listed by hciconfig')
    parser.add_argument('-b', '--bulb-version',
                        default='7',
                        dest='bulb_version',
                        type=int,
                        help='Bulb version as displayed in the official app')
    return parser.parse_args()


def main():
    params = get_params()

    # Exit if not root
    if (_platform == "linux" or _platform == "linux2") and os.geteuid() != 0:
        logger.error("Script must be run as root")
        return 1

    shell = MagicBlueShell(params.bluetooth_adapter, params.bulb_version)
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
