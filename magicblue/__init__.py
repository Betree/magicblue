#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Unofficial Python API to control Magic Blue bulbs over Bluetooth
"""

__version__ = "0.5.0"

try:
    from magicblue.magicbluelib import MagicBlue, Effect
except ImportError:
    from magicbluelib import MagicBlue, Effect

