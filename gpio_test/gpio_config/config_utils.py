"""
config_utils.py

Convenience functions for loading GPIO config modules
using the ConfigLoader abstraction.
"""

from config_loader import ConfigLoader, ConfigKind


def load_gpio_configs():
    """
    Loads both the GPIO I/O and GPIO definition config modules.

    Returns:
        tuple: (gpio_config_io, gpio_config_def)
    """
    gpio_config_io = load_gpio_io_config()
    gpio_config_def = load_gpio_def_config()
    return gpio_config_io, gpio_config_def


def load_gpio_io_config():
    """
    Loads the GPIO I/O config module.

    Returns:
        module: The loaded gpio_config_io module.
    """
    loader = ConfigLoader(kind=ConfigKind.GPIO_IO)
    return loader.get_module()


def load_gpio_def_config():
    """
    Loads the GPIO definition config module.

    Returns:
        module: The loaded gpio_config_def module.
    """
    loader = ConfigLoader(kind=ConfigKind.GPIO_DEF)
    return loader.get_module()
