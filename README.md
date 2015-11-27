# pyMagicBlue
Python script and library to control Magic Blue bulbs over bluetooth.

The Magic Bulb is, as far as I know, the cheapest bluetooth RGB light bulb on the market : you can get it for as low as ~8€/9$ on sites like [Gearbest](http://www.gearbest.com/smart-light-bulb/pp_230349.html). It works pretty good and comes with mobile apps.

Unfortunattely I haven't found any API or documentation for it, which is why I started this project.

You can get more details by checking the [Wiki pages](https://github.com/Betree/pyMagicBlue/wiki).

I haven't fully retro-engineered the protocol yet so it's not complete but
[Characteristics list page](https://github.com/Betree/pyMagicBlue/wiki/Characteristics-list) and
[How to use manually with Gatttool page](https://github.com/Betree/pyMagicBlue/wiki/How-to-use-manually-with-Gatttool)
should give you enough details to start working on your own implementation if you need to port this for another
language / platform.
On the [research/bluetooth branch](https://github.com/Betree/pyMagicBlue/tree/research/bluetooth) you'll also find capture of bluetooth packets exchanged between Android and the bulb (open hci_capture.log with Wireshark).

Tested on Linux only. I'll be happy to get your feedback on other platforms !

## Installation
### Manual
#### Linux
You must use python 3+

    sudo apt-get install libbluetooth-dev
    pip install pybluez
    pip install gattlib

## Usage

    from magicblue import MagicBlue
    
    bulb_mac_address = 'XX:XX:XX:XX:XX:XX'
    bulb = MagicBlue(bulb_mac_address)
    bulb.connect()
    bulb.set_color([255, 0, 0])         # Set red
    bulb.set_random_color()             # Set random
    bulb.turn_off()                     # Turn off the light
    bulb.turn_on()                      # Set white light
