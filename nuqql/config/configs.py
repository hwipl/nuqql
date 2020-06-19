"""
nuqql configurations
"""

import configparser
import logging

from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# configurations
CONFIGS: Dict[str, Any] = {}


def read_from_file() -> configparser.ConfigParser:
    """
    Read configuration from config file
    """
    config_file = Path.home() / ".config/nuqql/config.ini"
    config = configparser.ConfigParser()
    config.optionxform = lambda option: option  # type: ignore
    config.read(config_file)

    return config


def write_to_file(config: configparser.ConfigParser) -> None:
    """
    Write configuration to config file
    """

    config_file = Path.home() / ".config/nuqql/config.ini"
    with open(config_file, "w+") as configfile:
        config.write(configfile)


def get(name: str) -> Any:
    """
    Get configuration identified by name
    """

    return CONFIGS[name]
