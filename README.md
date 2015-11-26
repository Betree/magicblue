# pyMagicBlue
Python script and library to control Magic Blue bulbs over bluetooth

You can get more details by checking the [Wiki pages](https://github.com/Betree/pyMagicBlue/wiki).

I haven't fully retro-engineered the protocol yet so it's not complete but
[Characteristics list page](https://github.com/Betree/pyMagicBlue/wiki/Characteristics-list) and
[How to use manually with Gatttool page](https://github.com/Betree/pyMagicBlue/wiki/How-to-use-manually-with-Gatttool)
should give you enough details to start working on your own implementation if you need to port this for another
language / platform

Tested on Linux only. I'll be happy to get your feedback on other platforms !

## Installation
### Manual
#### Linux
You must use python 3+

sudo apt-get install libbluetooth-dev

pip install pybluez

pip install gattlib

### Automatic
TODO

## Usage
### Using it as a tool
Script must be run as root. You also need to set your device MAC address in magicblue.py MAGIC_BLUE_MAC constant (this
will be automatised in a future version)

### Using it as an API
    from magicblue import MagicBlue
    
    bulb_mac_address = 'XX:XX:XX:XX:XX:XX'
    bulb = MagicBlue(bulb_mac_address)
    bulb.connect()
    bulb.set_color([255, 0, 0])         # Set red
    bulb.set_random_color([255, 0, 0])  # Set random
    bulb.turn_off()                     # Turn off the light
    bulb.turn_on()                      # Set white light
