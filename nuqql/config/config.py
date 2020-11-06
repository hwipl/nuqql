"""
Nuqql's User Interface configuration
"""

import argparse
import logging
import os
import stat

from pathlib import Path
from typing import Any, Dict

from nuqql import VERSION
from .configs import CONFIGS, get, read_from_file, write_to_file
from .winconfig import WinConfig

logger = logging.getLogger(__name__)

# default conversation settings
DEFAULT_CONVERSATION_CONFIG = {
    "sort_key": "last_send",
}


def init_win(screen: Any) -> None:
    """
    Initialize window configurations
    """

    list_win = WinConfig("list_win")
    log_win = WinConfig("log_win")
    log_win_main = WinConfig("log_win_main")
    input_win = WinConfig("input_win")

    list_win.init_layout()
    log_win.init_layout()
    log_win_main.init_layout()
    input_win.init_layout()

    list_win.init_window_settings()
    log_win.init_window_settings()
    log_win_main.init_window_settings()
    input_win.init_window_settings()

    list_win.init_colors()
    log_win.init_colors()
    log_win_main.init_colors()
    input_win.init_colors()

    list_win.init_keymap()
    log_win.init_keymap()
    log_win_main.init_keymap()
    input_win.init_keymap()

    list_win.init_keybinds()
    log_win.init_keybinds()
    log_win_main.init_keybinds()
    input_win.init_keybinds()

    CONFIGS["list_win"] = list_win
    CONFIGS["log_win"] = log_win
    CONFIGS["log_win_main"] = log_win_main
    CONFIGS["input_win"] = input_win

    # special "config" for main screen/window
    CONFIGS["screen"] = screen

    logger.debug("initialized window configurations")


def _get_conversation_config() -> Dict[str, str]:
    """
    Initialize/get conversation configuration
    """

    # init configuration from defaults
    conversation_config = DEFAULT_CONVERSATION_CONFIG

    # parse config read from file
    config = read_from_file()
    for section in config.sections():
        if section == "conversations":
            # overwrite default keymap config entries
            for key in config["conversations"]:
                if key in conversation_config:
                    conversation_config[key] = config["conversations"][key]

    # write (updated) config to file again
    config["conversations"] = conversation_config
    write_to_file(config)

    # return config
    return conversation_config


def init_conversation_settings() -> None:
    """
    Initialize conversation settings
    """

    settings = _get_conversation_config()
    CONFIGS["conversations"] = settings
    logger.debug("initialized conversation settings")


def init_path() -> None:
    """
    Initialize configuration path. Make sure config directories exist.
    """

    config_path = Path.home() / ".config/nuqql"
    Path(config_path).mkdir(parents=True, exist_ok=True)
    logger.debug("initialized config path %s", config_path)


def init(screen: Any) -> None:
    """
    Initialize configurations
    """

    logger.debug("initializing config with screen %s", screen)
    init_path()
    init_win(screen)
    init_conversation_settings()


def init_logging() -> None:
    """
    Initialize logging
    """

    # does not go to the log file
    logger.debug("initializing logging")

    init_path()

    # map loglevel
    loglevel_map = {
        "":         logging.WARNING,    # default loglevel
        "debug":    logging.DEBUG,
        "info":     logging.INFO,
        "warn":     logging.WARNING,
        "error":    logging.ERROR,
    }
    loglevel = loglevel_map[get("loglevel")]

    # configure logging
    fmt = "%(asctime)s - %(levelname)-5.5s - %(name)s - %(message)s"
    formatter = logging.Formatter(fmt=fmt)

    file_name = Path.home() / ".config/nuqql" / "nuqql.log"
    fileh = logging.FileHandler(file_name)
    fileh.setLevel(loglevel)
    fileh.setFormatter(formatter)

    main_logger = logging.getLogger("nuqql")
    main_logger.propagate = False
    main_logger.setLevel(loglevel)
    main_logger.addHandler(fileh)

    # restrict log file access
    os.chmod(file_name, stat.S_IRUSR | stat.S_IWUSR)

    # log debug message
    main_logger.debug("logging initialized")


def parse_args() -> None:
    """
    Parse command line arguments.
    """

    # does not go to the log file
    logger.debug("parsing command line arguments")

    # if we add more, consider moving it to config or somewhere else
    parser = argparse.ArgumentParser(
        description="Run nuqql command line instant messenger.")
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("--loglevel", choices=["debug", "info", "warn",
                                               "error"],
                        help="Logging level")
    args = parser.parse_args()

    # configure loglevel and logging
    CONFIGS["loglevel"] = ""
    if args.loglevel:
        CONFIGS["loglevel"] = args.loglevel
    init_logging()
