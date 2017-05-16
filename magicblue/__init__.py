#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Unofficial Python API to control Magic Blue bulbs over Bluetooth
"""

__version__ = "0.3.1"

try:
    from magicblue.magicbluelib import MagicBlue
except ImportError:
    from magicbluelib import MagicBlue

