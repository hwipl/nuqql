"""
Nuqql's User Interface configuration
"""

import configparser
import curses.ascii
import curses
import sys

from pathlib import Path

#############
# UI Config #
#############

# default keymap for special keys
DEFAULT_KEYMAP = {
    "KEY_ESC":          curses.ascii.ESC,
    "KEY_RIGHT":        curses.KEY_RIGHT,
    "KEY_LEFT":         curses.KEY_LEFT,
    "KEY_DOWN":         curses.KEY_DOWN,
    "KEY_UP":           curses.KEY_UP,
    "KEY_H":            ord("h"),
    "KEY_J":            ord("j"),
    "KEY_K":            ord("k"),
    "KEY_L":            ord("l"),
    "KEY_CTRL_A":       ord(curses.ascii.ctrl("a")),
    "KEY_CTRL_B":       ord(curses.ascii.ctrl("b")),
    "KEY_CTRL_E":       ord(curses.ascii.ctrl("e")),
    "KEY_CTRL_K":       ord(curses.ascii.ctrl("k")),
    "KEY_CTRL_N":       ord(curses.ascii.ctrl("n")),
    "KEY_CTRL_U":       ord(curses.ascii.ctrl("u")),
    "KEY_CTRL_V":       ord(curses.ascii.ctrl("v")),
    "KEY_CTRL_X":       ord(curses.ascii.ctrl("x")),
    "KEY_DEL":          curses.ascii.DEL,
    "KEY_DC":           curses.KEY_DC,
    "KEY_HOME":         curses.KEY_HOME,
    "KEY_END":          curses.KEY_END,
    "KEY_PAGE_UP":      curses.KEY_PPAGE,
    "KEY_PAGE_DOWN":    curses.KEY_NPAGE,
    "KEY_F9":           curses.KEY_F9,
    "KEY_F10":          curses.KEY_F10,
    "KEY_/":            ord("/"),
}

# default key bindings for input windows
DEFAULT_INPUT_WIN_KEYBINDS = {
    "CURSOR_RIGHT":         "KEY_RIGHT",
    "CURSOR_LEFT":          "KEY_LEFT",
    "CURSOR_DOWN":          "KEY_DOWN",
    "CURSOR_UP":            "KEY_UP",
    "CURSOR_LINE_START":    "KEY_PAGE_UP",
    "CURSOR_LINE_END":      "KEY_PAGE_DOWN",
    "CURSOR_MSG_START":     "KEY_HOME, KEY_CTRL_A",
    "CURSOR_MSG_END":       "KEY_END, KEY_CTRL_E",
    "DEL_CHAR":             "KEY_DEL",
    "DEL_CHAR_RIGHT":       "KEY_DC",
    "DEL_LINE_END":         "KEY_CTRL_K",
    "DEL_LINE":             "KEY_CTRL_U",
    "GO_BACK":              "KEY_ESC",
    "GO_NEXT":              "KEY_CTRL_N",
    "GO_PREV":              "KEY_CTRL_B",
    "GO_CONV":              "KEY_CTRL_V",
    "SEND_MSG":             "KEY_CTRL_X",
    "WIN_ZOOM":             "KEY_F9",
    "WIN_ZOOM_URL":         "KEY_F10",
}

# default key bindings for log windows
DEFAULT_LOG_WIN_KEYBINDS = dict(DEFAULT_INPUT_WIN_KEYBINDS)
DEFAULT_LOG_WIN_KEYBINDS["CURSOR_LEFT"] = "KEY_LEFT, KEY_H"
DEFAULT_LOG_WIN_KEYBINDS["CURSOR_DOWN"] = "KEY_DOWN, KEY_J"
DEFAULT_LOG_WIN_KEYBINDS["CURSOR_UP"] = "KEY_UP, KEY_K"
DEFAULT_LOG_WIN_KEYBINDS["CURSOR_RIGHT"] = "KEY_RIGHT, KEY_L"

# default key bindings for list window (Buddy List)
DEFAULT_LIST_WIN_KEYBINDS = {
    "CURSOR_DOWN":          "KEY_DOWN, KEY_J",
    "CURSOR_UP":            "KEY_UP, KEY_K",
    "CURSOR_TOP":           "KEY_HOME, KEY_CTRL_A",
    "CURSOR_BOTTOM":        "KEY_END, KEY_CTRL_E",
    "CURSOR_PAGE_UP":       "KEY_PAGE_UP",
    "CURSOR_PAGE_DOWN":     "KEY_PAGE_DOWN",
    "GO_BACK":              "KEY_ESC",
    "GO_NEXT":              "KEY_CTRL_N",
    "GO_PREV":              "KEY_CTRL_B",
    "GO_CONV":              "KEY_CTRL_V, KEY_/",
}

# default_list_win_keybinds = {
#   ...
#    #"q"             : "GO_BACK", # TODO: do we want something like that?
#    #"\n"            : "DO_SOMETHING", # TODO: do we want something like that?
#   ...
# }

# default ui layout
DEFAULT_LAYOUT = {
    # window x and y sizes in percent
    "LIST_WIN_Y_PER":   100,
    "LIST_WIN_X_PER":   20,
    "LOG_WIN_Y_PER":    80,
    "LOG_WIN_X_PER":    80,
    "INPUT_WIN_Y_PER":  20,
    "INPUT_WIN_X_PER":  80,
}

# window default colors and attributes
DEFAULT_COLORS = {
    "background": "default",
    "win_border": "blue",
    "list_win_text_default": "yellow",
    "list_win_text_slixmppd": "green",
    "list_win_text_matrixd": "red",
    "list_win_text_purpled": "magenta",
    "list_win_text_based": "white",
    "log_win_text_peer_old": "yellow",
    "log_win_text_peer_new": "yellow",
    "log_win_text_self_old": "cyan",
    "log_win_text_self_new": "cyan",
}

DEFAULT_ATTRIBS = {
    "win_border": "bold",
    "list_win_text_default": "normal",
    "list_win_text_slixmppd": "normal",
    "list_win_text_matrixd": "normal",
    "list_win_text_purpled": "normal",
    "list_win_text_based": "normal",
    "log_win_text_peer_old": "normal",
    "log_win_text_peer_new": "bold",
    "log_win_text_self_old": "normal",
    "log_win_text_self_new": "bold",
}

# default conversation settings
DEFAULT_CONVERSATION_CONFIG = {
    "sort_key": "last_send",
}

# default window settings
DEFAULT_LIST_WIN_CONFIG = {
    "show_title": True,
}

DEFAULT_LOG_WIN_CONFIG = DEFAULT_LIST_WIN_CONFIG
DEFAULT_INPUT_WIN_CONFIG = DEFAULT_LIST_WIN_CONFIG

# configurations
CONFIGS = {}


class WinConfig:
    """
    Class for window configuration
    """

    def __init__(self, wtype):
        self.type = wtype
        self.rel_y = 0
        self.rel_x = 0
        self.keymap = None
        self.keybinds = None
        self.attr = {}  # window colors/attributes
        self.settings = {}  # window settings

    @staticmethod
    def _get_layout_config():
        """
        Initialize/get layout configuration
        """

        # init configuration from defaults
        layout_config = DEFAULT_LAYOUT

        # read config file if it exists
        config_file = Path.home() / ".config/nuqql/config.ini"
        config = configparser.ConfigParser()
        config.optionxform = lambda option: option
        config.read(config_file)

        # parse config read from file
        for section in config.sections():
            if section == "layout":
                # overwrite default color config entries
                for key in config["layout"]:
                    if key in layout_config:
                        layout_config[key] = float(config["layout"][key])

        # write (updated) config to file again
        config["layout"] = layout_config
        with open(config_file, "w+") as configfile:
            config.write(configfile)

        # create and return internally used layout configuration
        layout = {}
        for key, value in layout_config.items():
            layout[key] = value / 100
        return layout

    def init_layout(self):
        """
        Init UI/Window layout
        """

        # get layout
        layout = self._get_layout_config()

        # set window layout
        if self.type == "list_win":
            self.rel_y = layout["LIST_WIN_Y_PER"]
            self.rel_x = layout["LIST_WIN_X_PER"]
        if self.type == "log_win":
            self.rel_y = layout["LOG_WIN_Y_PER"]
            self.rel_x = layout["LOG_WIN_X_PER"]
        if self.type == "input_win":
            self.rel_y = layout["INPUT_WIN_Y_PER"]
            self.rel_x = layout["INPUT_WIN_X_PER"]

    @staticmethod
    def _get_window_config():
        """
        Initialize/get window configuration
        """

        # init configuration from defaults
        win_config = {}
        win_config["list_win"] = DEFAULT_LIST_WIN_CONFIG
        win_config["log_win"] = DEFAULT_LOG_WIN_CONFIG
        win_config["input_win"] = DEFAULT_INPUT_WIN_CONFIG

        # read config file if it exists
        config_file = Path.home() / ".config/nuqql/config.ini"
        config = configparser.ConfigParser()
        config.optionxform = lambda option: option
        config.read(config_file)

        # parse config read from file
        for section in config.sections():
            if section in ("list_win", "log_win", "input_win"):
                # overwrite default config entries
                for key in config[section]:
                    if key in win_config[section]:
                        try:
                            # try to read setting as bool
                            win_config[section][key] = \
                                    config[section].getboolean(key)
                        except ValueError:
                            win_config[section][key] = config[section][key]

        # write (updated) config to file again
        for win_type in ("list_win", "log_win", "input_win"):
            config[win_type] = win_config[win_type]
        with open(config_file, "w+") as configfile:
            config.write(configfile)

        return win_config

    def init_window_settings(self):
        """
        Init window specific settings
        """

        # get window configurations
        win_config = self._get_window_config()

        # use settings depending on window type
        self.settings = win_config[self.type]

    @staticmethod
    def _get_color_config():
        """
        Initialize/get color configuration
        """

        # init configuration from defaults
        color_config = DEFAULT_COLORS
        attrib_config = DEFAULT_ATTRIBS

        # read config file if it exists
        config_file = Path.home() / ".config/nuqql/config.ini"
        config = configparser.ConfigParser()
        config.read(config_file)

        # parse config read from file
        for section in config.sections():
            if section == "colors":
                # overwrite default color config entries
                for key in config["colors"]:
                    if key in color_config:
                        color_config[key] = config["colors"][key]
            if section == "attributes":
                # overwrite default attribute config entries
                for key in config["attributes"]:
                    if key in attrib_config:
                        attrib_config[key] = config["attributes"][key]

        # write (updated) config to file again
        config["colors"] = color_config
        config["attributes"] = attrib_config
        with open(config_file, "w+") as configfile:
            config.write(configfile)

        return color_config, attrib_config

    def init_colors(self):
        """
        Initialize colors
        """

        # get color and attrib configuration
        color_config, attrib_config = self._get_color_config()

        # configure background color
        background = color_config["background"]
        bg_colors = {
            "default":  int(-1),
            "black":    curses.COLOR_BLACK,
            "blue":     curses.COLOR_BLUE,
            "cyan":     curses.COLOR_CYAN,
            "green":    curses.COLOR_GREEN,
            "magenta":  curses.COLOR_MAGENTA,
            "red":      curses.COLOR_RED,
            "white":    curses.COLOR_WHITE,
            "yellow":   curses.COLOR_YELLOW,
        }
        # allow definition of color numbers
        for i in range(0, 16):
            bg_colors["color{}".format(i)] = i

        # allow usage of default colors and initialize color pairs
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, bg_colors[background])
        curses.init_pair(2, curses.COLOR_BLUE, bg_colors[background])
        curses.init_pair(3, curses.COLOR_CYAN, bg_colors[background])
        curses.init_pair(4, curses.COLOR_GREEN, bg_colors[background])
        curses.init_pair(5, curses.COLOR_MAGENTA, bg_colors[background])
        curses.init_pair(6, curses.COLOR_RED, bg_colors[background])
        curses.init_pair(7, curses.COLOR_WHITE, bg_colors[background])
        curses.init_pair(8, curses.COLOR_YELLOW, bg_colors[background])
        # allow definition of additional (unnamed) colors
        for i in range(8, 16):
            curses.init_pair(i + 1, i, bg_colors[background])

        # mapping from color names to color pairs
        colors = {
            "default":  curses.color_pair(0),
            "black":    curses.color_pair(1),
            "blue":     curses.color_pair(2),
            "cyan":     curses.color_pair(3),
            "green":    curses.color_pair(4),
            "magenta":  curses.color_pair(5),
            "red":      curses.color_pair(6),
            "white":    curses.color_pair(7),
            "yellow":   curses.color_pair(8),
        }
        # allow definition of color numbers
        for i in range(0, 16):
            colors["color{}".format(i)] = curses.color_pair(i + 1)

        # text attributes
        attrib_italic = curses.A_NORMAL     # italic was added in python 3.7
        if sys.version_info >= (3, 7):
            attrib_italic = curses.A_ITALIC
        attribs = {
            "alt":          curses.A_ALTCHARSET,
            "blink":        curses.A_BLINK,
            "bold":         curses.A_BOLD,
            "dim":          curses.A_DIM,
            "invisible":    curses.A_INVIS,
            "italic":       attrib_italic,  # italic was added in python 3.7
            "normal":       curses.A_NORMAL,
            "protect":      curses.A_PROTECT,
            "reverse":      curses.A_REVERSE,
            "standout":     curses.A_STANDOUT,
            "underline":    curses.A_UNDERLINE,
            "horizontal":   curses.A_HORIZONTAL,
            "left":         curses.A_LEFT,
            "low":          curses.A_LOW,
            "right":        curses.A_RIGHT,
            "top":          curses.A_TOP,
            "vertical":     curses.A_VERTICAL,
        }

        # actually create color/attrib config for later use
        self.attr = {}
        self.attr["list_win_text"] = {}

        for key, value in color_config.items():
            # read attribute if it exists (e.g., background only has a color)
            attrib = 0
            if key in attrib_config:
                attrib = attribs[attrib_config[key]]

            # list_win_text needs special handling
            if key.startswith("list_win_text_"):
                self.attr["list_win_text"][key[14:]] = \
                    colors[value] | attrib
                # skip to next key
                continue

            # set color and attrib in configuration
            self.attr[key] = colors[value] | attrib

    @staticmethod
    def _get_keymap_config():
        """
        Initialize/get keymap configuration
        """

        # init configuration from defaults
        keymap_config = DEFAULT_KEYMAP

        # read config file if it exists
        config_file = Path.home() / ".config/nuqql/config.ini"
        config = configparser.ConfigParser()
        config.optionxform = lambda option: option
        config.read(config_file)

        # parse config read from file
        for section in config.sections():
            if section == "keymap":
                # overwrite default keymap config entries
                for key in config["keymap"]:
                    if key in keymap_config:
                        try:
                            keymap_config[key] = int(config["keymap"][key])
                        except ValueError:
                            keymap_config[key] = config["keymap"][key]

        # write (updated) config to file again
        config["keymap"] = keymap_config
        with open(config_file, "w+") as configfile:
            config.write(configfile)

        # create and return internally used keymap
        keymap = {}
        for key, value in keymap_config.items():
            keymap[value] = key
        return keymap

    def init_keymap(self):
        """
        Initialzize keymap
        """

        self.keymap = self._get_keymap_config()

    @staticmethod
    def _get_keybinds_config():
        """
        Initialize/get keybind configuration
        """

        # init configuration from defaults
        keybinds_config = {}
        keybinds_config["list_win_keybinds"] = DEFAULT_LIST_WIN_KEYBINDS
        keybinds_config["log_win_keybinds"] = DEFAULT_LOG_WIN_KEYBINDS
        keybinds_config["input_win_keybinds"] = DEFAULT_INPUT_WIN_KEYBINDS

        # read config file if it exists
        config_file = Path.home() / ".config/nuqql/config.ini"
        config = configparser.ConfigParser()
        config.optionxform = lambda option: option
        config.read(config_file)

        # parse config read from file
        for section in config.sections():
            if section in ("list_win_keybinds", "log_win_keybinds",
                           "input_win_keybinds"):
                # overwrite default keymap config entries
                for key in config[section]:
                    if key in keybinds_config[section]:
                        keybinds_config[key] = config[section][key]

        # write (updated) config to file again
        for win_binds in ("list_win_keybinds", "log_win_keybinds",
                          "input_win_keybinds"):
            config[win_binds] = keybinds_config[win_binds]
        with open(config_file, "w+") as configfile:
            config.write(configfile)

        # create and return internally used keymap
        # swap keys and values in config dictionaries
        tmp_keybinds = {}
        for win_binds in ("list_win_keybinds", "log_win_keybinds",
                          "input_win_keybinds"):
            tmp_keybinds[win_binds] = {}
            for key, value in keybinds_config[win_binds].items():
                # might be comma separated list of keys bound to same function
                for entry in value.split(","):
                    tmp_keybinds[win_binds][entry.strip()] = key

        # construct keybinds as used later
        keybinds = {}
        keybinds["list_win"] = tmp_keybinds["list_win_keybinds"]
        keybinds["log_win"] = tmp_keybinds["log_win_keybinds"]
        keybinds["input_win"] = tmp_keybinds["input_win_keybinds"]

        return keybinds

    def init_keybinds(self):
        """
        Initialize keybindings depending on window type
        """

        keybinds = self._get_keybinds_config()
        self.keybinds = keybinds[self.type]

    def get_win_size(self, max_y, max_x):
        """
        Get size of the window, depending on max_y and max_x as well as
        window's y_per and x_per. If window size is smaller than minimum size,
        return minimum size.
        """

        abs_y = max(int(max_y * self.rel_y), 3)
        abs_x = max(int(max_x * self.rel_x), 3)
        return abs_y, abs_x

    def get_size(self):
        """
        Return window size depending on max screen size and
        other windows' sizes.
        """

        # get (minimum) size of all windows
        max_y, max_x = get("screen").getmaxyx()
        list_y, list_x = get("list_win").get_win_size(max_y, max_x)
        log_y, log_x = get("log_win").get_win_size(max_y, max_x)
        input_y, input_x = get("input_win").get_win_size(max_y, max_x)

        # make sure input and log win use all available space
        if input_y + log_y < max_y:
            log_y += max_y - input_y

        # reduce log window height if necessary
        if input_y + log_y > max_y:
            log_y = max(max_y - input_y, 3)

        # reduce log and input window width if necessary
        if list_x + log_x > max_x:
            log_x = max(max_x - list_x, 3)
            input_x = max(max_x - list_x, 3)

        # return height and width of this window
        if self.type == "log_win":
            return log_y, log_x
        if self.type == "input_win":
            return input_y, input_x
        if self.type == "list_win":
            return list_y, list_x

        # should not be reached
        return -1, -1

    def get_pos(self):
        """
        Get position of the window, depending on type and window sizes
        """

        max_y, max_x = get("screen").getmaxyx()
        size_y, size_x = self.get_size()

        if self.type == "list_win":
            return 0, 0
        if self.type == "log_win":
            return 0, max_x - size_x
        if self.type == "input_win":
            return max_y - size_y, max_x - size_x

        # should not be reached
        return -1, -1

    @staticmethod
    def is_terminal_valid():
        """
        Helper that checks if terminal size is still valid (after resize)
        """

        # height and width of screen should not get below minimum size
        max_y, max_x = get("screen").getmaxyx()
        if max_y < 6 or max_x < 6:
            return False

        # everything seems to be ok
        return True


def get(name):
    """
    Get configuration identified by name
    """

    return CONFIGS[name]


def init_win(screen):
    """
    Initialize window configurations
    """

    list_win = WinConfig("list_win")
    log_win = WinConfig("log_win")
    input_win = WinConfig("input_win")

    list_win.init_layout()
    log_win.init_layout()
    input_win.init_layout()

    list_win.init_window_settings()
    log_win.init_window_settings()
    input_win.init_window_settings()

    list_win.init_colors()
    log_win.init_colors()
    input_win.init_colors()

    list_win.init_keymap()
    log_win.init_keymap()
    input_win.init_keymap()

    list_win.init_keybinds()
    log_win.init_keybinds()
    input_win.init_keybinds()

    CONFIGS["list_win"] = list_win
    CONFIGS["log_win"] = log_win
    CONFIGS["input_win"] = input_win

    # special "config" for main screen/window
    CONFIGS["screen"] = screen


def _get_conversation_config():
    """
    Initialize/get conversation configuration
    """

    # init configuration from defaults
    conversation_config = DEFAULT_CONVERSATION_CONFIG

    # read config file if it exists
    config_file = Path.home() / ".config/nuqql/config.ini"
    config = configparser.ConfigParser()
    config.optionxform = lambda option: option
    config.read(config_file)

    # parse config read from file
    for section in config.sections():
        if section == "conversations":
            # overwrite default keymap config entries
            for key in config["conversations"]:
                if key in conversation_config:
                    conversation_config[key] = config["conversations"][key]

    # write (updated) config to file again
    config["conversations"] = conversation_config
    with open(config_file, "w+") as configfile:
        config.write(configfile)

    # return config
    return conversation_config


def init_conversation_settings():
    """
    Initialize conversation settings
    """

    settings = _get_conversation_config()
    CONFIGS["conversations"] = settings


def init(screen):
    """
    Initialize configurations
    """

    init_win(screen)
    init_conversation_settings()
