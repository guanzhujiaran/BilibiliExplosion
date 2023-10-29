# -*- coding: utf-8 -*-
import os

_global_dict = {}


def _init():
    global _global_dict
    if _global_dict == {}:
        _global_dict = {}


def set_value(key, value):
    _global_dict[key] = value


def get_value(key, defValue=None):
    defValue = ''
    try:
        return _global_dict[key]
    except KeyError:
        return defValue


