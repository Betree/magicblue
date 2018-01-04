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
from datetime import datetime
from pprint import pformat
from sys import platform as _platform

from webcolors import hex_to_rgb, name_to_rgb
from bluepy.btle import Scanner, DefaultDelegate
try:
    from magicblue.magicbluelib import MagicBlue, Effect
    from magicblue import __version__
except ImportError:
    from magicbluelib import MagicBlue, Effect
    from __init__ import __version__

logger = logging.getLogger(__name__)


class MagicBlueShell:
    class Cmd:
        def __init__(self, cmd_str, func, conn_required, help='', params=None,
                     aliases=None, opt_params=None):
            self.cmd_str = cmd_str
            self.func = func
            self.conn_required = conn_required
            self.help = help
            self.params = params or []
            self.aliases = aliases or []
            self.opt_params = opt_params or []

    def __init__(self, bluetooth_adapter, bulb_version=7):
        # List available commands and their usage. 'con_required' define if
        # we need to be connected to a device for the command to run
        self.available_cmds = [
            MagicBlueShell.Cmd('help', self.list_commands, False,
                               help='Show this help'),
            MagicBlueShell.Cmd('list_devices', self.cmd_list_devices, False,
                               help='List Bluetooth LE devices in range',
                               aliases=['ls']),
            MagicBlueShell.Cmd('list_effects', self.cmd_list_effects, False,
                               help='List available effects',),
            MagicBlueShell.Cmd('connect', self.cmd_connect, False,
                               help='Connect to light bulb',
                               params=['mac_address||ID'],
                               aliases=['c'],
                               opt_params=['bulb version (default 7)']),
            MagicBlueShell.Cmd('disconnect', self.cmd_disconnect, True,
                               help='Disconnect from current light bulb'),
            MagicBlueShell.Cmd('set_color', self.cmd_set_color, True,
                               help="Change bulb's color",
                               params=['name or hexadecimal value']),
            MagicBlueShell.Cmd('set_warm_light', self.cmd_set_warm_light, True,
                               help='Set warm light',
                               params=['intensity[0.0-1.0]']),
            MagicBlueShell.Cmd('set_effect', self.cmd_set_effect, True,
                               help='Set an effect',
                               params=['effect_name', 'speed[1-20]']),
            MagicBlueShell.Cmd('set_date_time', self.cmd_set_date_time, True,
                               help='Set current date/time'),
            MagicBlueShell.Cmd('turn', self.cmd_turn, True,
                               help='Turn on / off the bulb',
                               params=['on|off']),
            MagicBlueShell.Cmd('read', self.cmd_read, True,
                               help='Read device_info/datetime from the bulb',
                               params=['name|device_info|' +
                                       'date_time|time_schedule']),
            MagicBlueShell.Cmd('exit', self.cmd_exit, False,
                               help='Exit the script'),
            MagicBlueShell.Cmd('debug', self.cmd_debug, False,
                               help='Enable/disable debug messages from lib',
                               params=['on|off']),
        ]

        self.bluetooth_adapter = bluetooth_adapter
        self._bulb_version = bulb_version
        self._bulbs = []
        self._devices = []
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
        args = str_cmd.split()[1:]
        if cmd is not None:
            if cmd.conn_required and not (len(self._bulbs) > 0):
                logger.error('You must be connected to run this command')
            elif self._check_args(cmd, args):
                cmd.func(args)
        else:
            logger.error('"{}" is not a valid command.'
                         'Type "help" to see what you can do'
                         .format(str_cmd.split()[0]))

    def print_usage(self, str_cmd):
        cmd = self._get_command(str_cmd)
        if cmd is not None:
            params = ' '.join(cmd.params)
            opt_params = ' '.join('[{}]'.format(p) for p in cmd.opt_params)
            print('Usage: {} {} {}'.format(cmd.cmd_str, params, opt_params))
        else:
            logger.error('Unknown command {}'.format(str_cmd))
        return False

    def cmd_list_devices(self, args):
        scan_time = 300
        try:
            self.last_scan = ScanDelegate()
            scanner = Scanner().withDelegate(self.last_scan)

            print('Listing Bluetooth LE devices in range for {} seconds. '
                  'Press CTRL+C to abort searching.'.format(scan_time))
            print('{: <5} {: <30} {: <12}'.format('ID', 'Name', 'Mac address'))
            print('{: <5} {: <30} {: <12}'.format('--', '----', '-----------'))

            scanner.scan(scan_time)
        except KeyboardInterrupt:
            print('\n')
        except RuntimeError as e:
            logger.error('Problem with the Bluetooth adapter : {}'.format(e))
            return False

    def cmd_list_effects(self, args):
        for e in Effect.__members__.keys():
            print(e)

    def cmd_connect(self, args):
        bulb_version = args[1] if len(args) > 1 else self._bulb_version
        # Use can enter either a mac address or the device ID from the list
        if len(args[0]) < 4 and self.last_scan:
            try:
                dev_id = int(args[0]) - 1
                entry = self.last_scan.devices[dev_id]
                mac_address = entry.addr
                addr_type = entry.addrType
            except Exception:
                logger.error('Bad ID / MAC address : {}'.format(args[0]))
                return False
        else:
            addr_type = None
            mac_address = args[0]
        magic_blue = MagicBlue(mac_address,
                               version=bulb_version,
                               addr_type=addr_type)
        magic_blue.connect(self.bluetooth_adapter)
        self._bulbs.append(magic_blue)
        logger.info('Connected')

    def cmd_disconnect(self, *args):
        for bulb in self._bulbs:
            bulb.disconnect()
        self._bulbs = []

    def cmd_turn(self, args):
        if args[0] == 'on':
            [bulb.turn_on() for bulb in self._bulbs]
        else:
            [bulb.turn_off() for bulb in self._bulbs]

    def cmd_debug(self, args):
        logging.basicConfig(level=logging.DEBUG)
        lib_logger = logging.getLogger('magicblue.magicbluelib')
        if args[0] == 'on':
            lib_logger.setLevel(logging.DEBUG)
        else:
            lib_logger.setLevel(logging.OFF)

    def cmd_read(self, args):
        for bulb in self._bulbs:
            logger.info('-------------------')
            if args[0] == 'name':
                name = bulb.get_device_name()
                logger.info('Received name: {}'.format(name))
            elif args[0] == 'device_info':
                device_info = bulb.get_device_info()
                logger.info('Received device_info: {}'.format(device_info))
            elif args[0] == 'date_time':
                datetime_ = bulb.get_date_time()
                logger.info('Received datetime: {}'.format(datetime_))
            elif args[0] == 'time_schedule':
                timer_schedule = bulb.get_time_schedule()

                logger.info('Time schedule:')
                for timer in timer_schedule:
                    logger.info('Timer: {}'.format(pformat(timer)))

    def cmd_set_color(self, args):
        color = args[0]
        try:
            if color.startswith('#'):
                [b.set_color(hex_to_rgb(color)) for b in self._bulbs]
            else:
                [b.set_color(name_to_rgb(color)) for b in self._bulbs]
        except ValueError as e:
            logger.error('Invalid color value : {}'.format(str(e)))
            self.print_usage('set_color')

    def cmd_set_warm_light(self, *args):
        try:
            [bulb.set_warm_light(float(args[0][0])) for bulb in self._bulbs]
        except ValueError as e:
            logger.error('Invalid intensity value : {}'.format(str(e)))
            self.print_usage('set_color')

    def cmd_set_effect(self, *args):
        try:
            [effect, speed] = args[0]
            effect = Effect[effect]
            speed = int(speed)
        except KeyError as key:
            logger.error('Unknown effect {}'.format(key))
        except ValueError:
            self.print_usage('set_effect')
        else:
            [bulb.set_effect(effect, speed) for bulb in self._bulbs]

    def cmd_set_date_time(self, *args):
        now = datetime.now()
        for bulb in self._bulbs:
            bulb.set_date_time(now)

    def list_commands(self, *args):
        print(' ----------------------------')
        print('| List of available commands |')
        print(' ----------------------------')
        print('{: <16}{: <48}{}'.format('COMMAND', 'PARAMETERS', 'DETAILS'))
        print('{: <16}{: <48}{}'.format('-------', '----------', '-------'))
        for command in self.available_cmds:
            print('{: <16}{: <48}{}'.format(
                    command.cmd_str, ' '.join(command.params), command.help))
            for alias in command.aliases:
                print('{: <16}{: <48}{}'.format(alias, '//', '//'))

    def cmd_exit(self, *args):
        print('Bye !')

    def _check_args(self, cmd, args):
        min_expected_nb_args = len(cmd.params)
        max_expected_nb_args = min_expected_nb_args + len(cmd.opt_params)
        if min_expected_nb_args <= len(args) <= max_expected_nb_args:
            return True
        self.print_usage(cmd.cmd_str)
        return False

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
            raw_name = dev.getValueText(9)
            dev_name = raw_name.split('\x00')[0] if raw_name else "NO_NAME"
            print('{: <5} {: <30} {: <12}'.format(len(self.devices),
                                                  dev_name,
                                                  dev.addr))


def get_params():
    parser = argparse.ArgumentParser(description='Python tool to control Magic'
                                                 'Blue bulbs over Bluetooth')
    parser.add_argument('-l', '--list_commands',
                        dest='list_commands',
                        help='List available commands',
                        action='store_true')
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
                        help='Bulb version (currently support 7, 8, 9 and 10)')
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
