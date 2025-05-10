import os
import json
import atexit
import sys
import warnings

warnings.warn(
    "config.py is deprecated and will be removed in a future version. "
    "Please use settings_manager.py instead.",
    DeprecationWarning,
    stacklevel=2
)

# Forward all calls to settings_manager
from src.utils.settings_manager import get_config as _get_config
from src.utils.settings_manager import save_config as _save_config
from src.utils.settings_manager import save_all_settings as _save_all_settings

def load_config():
    warnings.warn("Use get_config from settings_manager instead", DeprecationWarning, stacklevel=2)
    return _get_config()

def save_config(config):
    warnings.warn("Use save_config from settings_manager instead", DeprecationWarning, stacklevel=2)
    return _save_config(config)

def save_all_settings():
    warnings.warn("Use save_all_settings from settings_manager instead", DeprecationWarning, stacklevel=2)
    return _save_all_settings()