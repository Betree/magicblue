![MagicBlue Bulb](https://lut.im/xpaCaUNTaU/k6WRbc71KMMSFIln.jpg)

# MagicBlue - Control your Magic Blue bulbs over bluetooth

The Magic Bulb is, as far as I know, the cheapest bluetooth RGB light bulb on the market : you can get it for as low as ~8€/9$ on sites like
[Gearbest](http://www.gearbest.com/smart-light-bulb/pp_230349.html). It works pretty good and comes with mobile apps.

Unfortunately I haven't found any API or documentation for it, which is why I started this project.

I haven't fully retro-engineered the protocol yet so it's not complete but
[Characteristics list page](https://github.com/Betree/pyMagicBlue/wiki/Characteristics-list) and
[How to use manually with Gatttool page](https://github.com/Betree/pyMagicBlue/wiki/How-to-use-manually-with-Gatttool)
should give you enough details to start working on your own implementation if you need to port this for another
language / platform.
On the [research/bluetooth branch](https://github.com/Betree/pyMagicBlue/tree/research/bluetooth) you'll also find capture of bluetooth packets exchanged between Android and the bulb (open hci_capture.log with Wireshark).

Tested on Linux and Raspberry Pi. I'll be happy to get your feedback on other platforms !

There are multiple versions of the bulb, some of them may need development to be compatible with this project. If you have a different bulb version you can try to sniff bluetooth communications. Reverse-engeeniring information and pull requests are more than welcome 😺

<table>
  <tr>
    <th>Bulb Version<br></th>
    <th>v6</th>
    <th>v7</th>
    <th>v8</th>
    <th>v9</th>
    <th>v10</th>
  </tr>
  <tr>
    <td>Status</td>
    <td>☑️</td>
    <td>☑️</td>
    <td>☑️<br></td>
    <td>☑️</td>
    <td>☑️</td>
  </tr>
</table>

## Installation
### HomeAssistant
If you want to use this project with [HomeAssistant](https://home-assistant.io/) you'll need to install `magicblue` as described below then use the component available here : https://github.com/xiaohuim/homeassistant-magicblue

### Linux
You must use python 3+ and have a proper Bluetooth 4.0 interface installed on your machine.

* Prerequisite

  - Debian: `sudo apt-get install libglib2.0-dev`
  - Fedora: `sudo dnf install glib2-devel`

* Install

    > sudo pip3 install magicblue

    ⚠️ If you get an error like
    `No such file or directory: '/usr/local/lib/python3.4/dist-packages/bluepy/bluepy-helper'`
    or
    `ERROR:magicblue.magicblueshell:Unexpected error with command "ls": Helper exited`
    checkout details below.
    <details>
        This is a known bug in bluepy that sometimes doesn't get compiled
        when installed from Pypi.
        You can fix it by compiling the helper yourself :
        Go to the lib folder (usually `/usr/local/lib/python3.5/dist-packages/bluepy-1.1.2-py3.5.egg/bluepy/`
        but could be different, especially if you're using a virtual env) and
        run `sudo make` (`make` should be enought for a virtual env)

        More info: https://github.com/IanHarvey/bluepy/issues/158
    </details>

* Raspberry Pi specifics

Follow the Debian procedure. If it doesn't work (unstable devices listing, commands have no effect)
but you're sure that your bulb has a correct version (check the official app for that)
then try updating bluez to the latest version. You can follow
[this post](https://community.home-assistant.io/t/xiaomi-mi-plants-monitor-flower/3388/135)
for more info.

## Usage

**Library needs elevated permissions to use Bluetooth features. You can either run as root (required for magicblueshell), or give `hcitool` special capabilities (see next section.)**

If you run into problems during devices listing or connect, try to follow this procedure to ensure your Bluetooth interface works correctly : [How to use manually with Gatttool page](https://github.com/Betree/pyMagicBlue/wiki/How-to-use-manually-with-Gatttool)

### Giving hcitool capabilities

You can give `hcitool` capabilities by installing and using the libcap library/commands.

* On most Debian systems, including Raspbian/Raspberry Pi

```
sudo apt-get install libcap2-bin
sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hcitool`
```

* Fedora

```
sudo dnf install libcap
sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hcitool`
```

### Using it as an API

```
>>> from magicblue import MagicBlue

>>> bulb_mac_address = 'XX:XX:XX:XX:XX:XX'
>>> bulb = MagicBlue(bulb_mac_address, 9) # Replace 9 by whatever your version is (default: 7)
>>> bulb.connect()
>>> bulb.set_color([255, 0, 0])         # Set red
>>> bulb.set_random_color()             # Set random
>>> bulb.turn_off()                     # Turn off the light
>>> bulb.turn_on()                      # Set white light
```

### Using it as a tool
Script must be run as root.

You can always specify which bluetooth adapter (default: hci0) you want to use by specifying it with the -a option.

Also **don't forget to specify your bulb version with `-b` if it's something else than 7**. Example :
`sudo magicblueshell -b 10` to run with version 10


#### Using the interactive shell
Just launch magicblueshell as root user :

```
$ sudo magicblueshell
Magic Blue interactive shell v0.3.0
Type "help" for a list of available commands
> help
 ----------------------------
| List of available commands |
 ----------------------------
COMMAND         PARAMETERS                    DETAILS
-------         ----------                    -------
help                                          Show this help
list_devices                                  List Bluetooth LE devices in range
ls              //                            //
list_effects                                  List available effects
connect         mac_address or ID             Connect to light bulb
disconnect                                    Disconnect from current light bulb
set_color       name or hexadecimal value     Change bulb's color
set_warm_light  intensity[0.0-1.0]            Set warm light
set_effect      effect_name speed[1-20]       Set an effect
turn            on|off                        Turn on / off the bulb
read            name|device_info|date_time    Read device_info/datetime from the bulb
exit                                          Exit the script
> ls
Listing Bluetooth LE devices in range for 5 minutes.Press CTRL+C to stop searching.
ID    Name                           Mac address 
--    ----                           ----------- 
1     LEDBLE-1D433903                c7:17:1d:43:39:03
^C

> connect 1
INFO:magicblue.magicblueshell:Connected
> set_color red
> exit
Bye !
```

#### Passing command as an option
Script can also be used by command line (for example to include it in custom shell scripts)
Usage is defined as follow :

```
usage: magicblueshell [-h] [-l LIST_COMMANDS] [-c COMMAND] [-m MAC_ADDRESS]
                      [-a BLUETOOTH_ADAPTER] [-b BULB_VERSION]

Python tool to control MagicBlue bulbs over Bluetooth

optional arguments:
  -h, --help            show this help message and exit
  -l LIST_COMMANDS, --list_commands LIST_COMMANDS
                        List available commands
  -c COMMAND, --command COMMAND
                        Command to execute
  -m MAC_ADDRESS, --mac_address MAC_ADDRESS
                        Device mac address. Must be set if command given in -c
                        needs you to be connected
  -a BLUETOOTH_ADAPTER, --bluetooth_adapter BLUETOOTH_ADAPTER
                        Bluetooth adapter name as listed by hciconfig
  -b BULB_VERSION, --bulb-version BULB_VERSION
                        Bulb version as displayed in the official app

```
                     
So if you want to change the color of bulb with mac address "C7:17:1D:43:39:03", just run :
    
> sudo magicblueshell -c 'set_color red' -m C7:17:1D:43:39:03
