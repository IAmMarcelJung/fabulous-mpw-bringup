"""
config_loader.py

Generalized dynamic loader for configuration modules.
Supports multiple naming conventions like:
- gpio_config_io_<SHUTTLE>.py
- gpio_config_def_part_<PART>_<VOLTAGE>.py
"""

import importlib.util
import os
from enum import Enum


# === Environment Variable Names ===


class EnvVar:
    SHUTTLE = "SHUTTLE"
    PART = "PART"
    VOLTAGE = "VOLTAGE"


# === Error Messages ===


class ErrorMsg:
    MISSING_SHUTTLE = "Missing 'shuttle' parameter or SHUTTLE environment variable."
    MISSING_PART_VOLTAGE = "Missing 'part' or 'voltage' parameter for gpio_def config."
    UNKNOWN_KIND = "Unsupported config kind: {}"
    FILE_NOT_FOUND = "Config file '{}' not found."
    LOAD_SPEC_FAILED = "Could not load spec for {}"


# === Param Keys ===


class ParamKey:
    SHUTTLE = "shuttle"
    PART = "part"
    VOLTAGE = "voltage"


# === Config Kind Enum ===


class ConfigKind(Enum):
    GPIO_IO = "gpio_io"
    GPIO_DEF = "gpio_def"

    @property
    def filename_pattern(self):
        if self == ConfigKind.GPIO_IO:
            return "gpio_config_io_{shuttle}.py"
        if self == ConfigKind.GPIO_DEF:
            return "../nucleo_firmware/gpio_config_files/part_{part}/gpio_config_def_part_{part}_{voltage}.py"
        raise ValueError(ErrorMsg.UNKNOWN_KIND.format(self))


# === Loader Class ===


class ConfigLoader:
    def __init__(self, kind: ConfigKind, **kwargs):
        """
        Initializes the loader for a specific config type.

        Args:
            kind (ConfigKind): Type of config to load.
            kwargs: Parameters for dynamic file resolution, e.g.
                    shuttle, part, voltage.
        """
        if not isinstance(kind, ConfigKind):
            raise ValueError(f"Invalid kind: {kind}")
        self._kind = kind
        self._params = kwargs
        self._filename = self._construct_filename()
        self._module = self._load_module()

    def _construct_filename(self):
        """
        Constructs the filename based on the kind and parameters.

        Returns:
            str: The constructed filename.

        Raises:
            ValueError: If required parameters are missing.
        """
        if self._kind == ConfigKind.GPIO_IO:
            shuttle = self._params.get(ParamKey.SHUTTLE) or os.environ.get(
                EnvVar.SHUTTLE
            )
            if not shuttle:
                raise ValueError(ErrorMsg.MISSING_SHUTTLE)
            self._params[ParamKey.SHUTTLE] = shuttle

        if self._kind == ConfigKind.GPIO_DEF:
            part = self._params.get(ParamKey.PART) or os.environ.get(EnvVar.PART)
            voltage = self._params.get(ParamKey.VOLTAGE) or os.environ.get(
                EnvVar.VOLTAGE
            )
            voltage_str = str(voltage).replace(".", "_") + "_V"
            if not part or not voltage:
                raise ValueError(ErrorMsg.MISSING_PART_VOLTAGE)
            self._params[ParamKey.PART] = part
            self._params[ParamKey.VOLTAGE] = voltage_str

        return self._kind.filename_pattern.format(**self._params)

    def _load_module(self):
        """
        Dynamically loads the specified config module from the file.

        Returns:
            module: The imported module.

        Raises:
            FileNotFoundError: If the file is missing.
            ImportError: If the module cannot be loaded.
        """
        if not os.path.exists(self._filename):
            raise FileNotFoundError(ErrorMsg.FILE_NOT_FOUND.format(self._filename))

        spec = importlib.util.spec_from_file_location("dynamic_config", self._filename)
        if spec is None or spec.loader is None:
            raise ImportError(ErrorMsg.LOAD_SPEC_FAILED.format(self._filename))

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def get_module(self):
        """
        Returns the loaded configuration module.

        Returns:
            module: Loaded module object.
        """
        return self._module
