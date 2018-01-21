.. MagicBlue documentation master file, created by
   sphinx-quickstart on Sun Jan 21 11:34:32 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

MagicBlue
=========

This is the reference for MagicBlue's API. To get information about
how to install it or to use magicblueshell, please refer to this link:
https://github.com/Betree/magicblue/blob/master/README.md

License
-------

The project is licensed under the MIT license.

Contribute
----------

- Issue Tracker: https://github.com/Betree/magicblue/issues
- Source Code: https://github.com/Betree/magicblue

Basic usage
-----------

.. code-block:: python

    from magicblue import MagicBlue

    bulb_mac_address = 'XX:XX:XX:XX:XX:XX'
    bulb = MagicBlue(bulb_mac_address, 9) # Replace 9 by whatever your version is (default: 7)
    bulb.connect()
    bulb.set_color([255, 0, 0])         # Set red
    bulb.set_random_color()             # Set random
    bulb.turn_off()                     # Turn off the light
    bulb.turn_on()                      # Set white light

----------------------------------------------------------------------

MagicBlue API reference
=======================

.. automodule:: magicbluelib

MagicBlue
---------

.. autoclass:: MagicBlue
   :members:

Effect
------

.. autoclass:: Effect
   :members:



