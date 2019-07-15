"""
Nuqql's User Interface configuration
"""

import curses

#############
# UI Config #
#############

# default keymap for special keys
DEFAULT_KEYMAP = {
    chr(curses.ascii.ESC):  "KEY_ESC",
    curses.KEY_RIGHT:       "KEY_RIGHT",
    curses.KEY_LEFT:        "KEY_LEFT",
    curses.KEY_DOWN:        "KEY_DOWN",
    curses.KEY_UP:          "KEY_UP",
    curses.ascii.ctrl("a"): "KEY_CTRL_A",
    curses.ascii.ctrl("e"): "KEY_CTRL_E",
    curses.ascii.ctrl("k"): "KEY_CTRL_K",
    curses.ascii.ctrl("u"): "KEY_CTRL_U",
    curses.ascii.ctrl("x"): "KEY_CTRL_X",
    chr(curses.ascii.DEL):  "KEY_DEL",
    curses.KEY_DC:          "KEY_DEL",
    curses.KEY_HOME:        "KEY_HOME",
    curses.KEY_END:         "KEY_END",
    curses.KEY_PPAGE:       "KEY_PAGE_UP",
    curses.KEY_NPAGE:       "KEY_PAGE_DOWN",
    curses.KEY_F9:          "KEY_F9",
    curses.KEY_F10:         "KEY_F10",
}

# default key bindings for input windows
DEFAULT_INPUT_WIN_KEYBINDS = {
    "KEY_ESC":          "GO_BACK",
    "KEY_RIGHT":        "CURSOR_RIGHT",
    "KEY_LEFT":         "CURSOR_LEFT",
    "KEY_DOWN":         "CURSOR_DOWN",
    "KEY_UP":           "CURSOR_UP",
    "KEY_CTRL_A":       "CURSOR_MSG_START",
    "KEY_CTRL_E":       "CURSOR_MSG_END",
    "KEY_CTRL_K":       "DEL_LINE_END",
    "KEY_CTRL_U":       "DEL_LINE",
    "KEY_CTRL_X":       "SEND_MSG",
    "KEY_DEL":          "DEL_CHAR",
    "KEY_HOME":         "CURSOR_MSG_START",
    "KEY_END":          "CURSOR_MSG_END",
    "KEY_PAGE_UP":      "CURSOR_LINE_START",
    "KEY_PAGE_DOWN":    "CURSOR_LINE_END",
    "KEY_F9":           "WIN_ZOOM",
    "KEY_F10":          "WIN_ZOOM_URL",
}

# default key bindings for log windows
# TODO: not used so far... do it?
DEFAULT_LOG_WIN_KEYBINDS = DEFAULT_INPUT_WIN_KEYBINDS

# default key bindings for list window (Buddy List)
DEFAULT_LIST_WIN_KEYBINDS = DEFAULT_INPUT_WIN_KEYBINDS
# default_list_win_keybinds = {
#   ...
#    #"q"             : "GO_BACK", # TODO: do we want something like that?
#    #"\n"            : "DO_SOMETHING", # TODO: do we want something like that?
#   ...
# }

# window x and y sizes in percent
LIST_WIN_Y_PER = 1
LIST_WIN_X_PER = 0.2
LOG_WIN_Y_PER = 0.8
LOG_WIN_X_PER = 0.8
INPUT_WIN_Y_PER = 0.2
INPUT_WIN_X_PER = 0.8

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

# configurations
CONFIGS = {}


class WinConfig:
    """
    Class for window configuration
    """

    def __init__(self, wtype, rel_y, rel_x):
        self.type = wtype
        self.rel_y = rel_y
        self.rel_x = rel_x
        self.keymap = None
        self.keybinds = None
        self.attr = {}  # window colors/attributes

    @staticmethod
    def _get_color_config():
        """
        Initialize/get color configuration
        """

        return DEFAULT_COLORS, DEFAULT_ATTRIBS

    def init_colors(self):
        """
        Initialize colors
        """

        # configure background color
        background = DEFAULT_COLORS["background"]
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

        # text attributes
        attribs = {
            "bold":     curses.A_BOLD,
            "normal":   curses.A_NORMAL,
        }

        # get color and attrib configuration
        color_config, attrib_config = self._get_color_config()

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

    def init_keymap(self):
        """
        Initialzize keymap
        """

        self.keymap = DEFAULT_KEYMAP

    def init_keybinds(self):
        """
        Initialize keybindings depending on window type
        """

        if self.type == "log_win":
            self.keybinds = DEFAULT_LOG_WIN_KEYBINDS
        if self.type == "input_win":
            self.keybinds = DEFAULT_INPUT_WIN_KEYBINDS
        if self.type == "list_win":
            self.keybinds = DEFAULT_LIST_WIN_KEYBINDS

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

    list_win = WinConfig("list_win", LIST_WIN_Y_PER, LIST_WIN_X_PER)
    log_win = WinConfig("log_win", LOG_WIN_Y_PER, LOG_WIN_X_PER)
    input_win = WinConfig("input_win", INPUT_WIN_Y_PER, INPUT_WIN_X_PER)

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
