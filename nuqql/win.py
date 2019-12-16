"""
Nuqql UI Windows
"""

import curses

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, Callable, Dict, List

if TYPE_CHECKING:   # imports for typing
    from nuqql.config import WinConfig
    from nuqql.conversation import Conversation

# screen and main windows
MAIN_WINS: Dict[str, Any] = {}


class Win:
    """
    Base class for Windows
    """

    def __init__(self, config: "WinConfig", conversation: "Conversation",
                 title: str) -> None:
        # configuration
        self.config = config

        # conversation
        self.conversation = conversation

        # window title
        self.title = " " + title + " "

        # create new window and new pad
        size_y, size_x = self.config.get_size()
        pos_y, pos_x = self.config.get_pos()
        self.win = curses.newwin(size_y, size_x, pos_y, pos_x)
        self.pad = curses.newpad(size_y - 2, size_x - 2)

        # window state
        self.state = SimpleNamespace(
            # is window active?
            active=False,
            # position inside pad
            pad_y=0,
            pad_x=0,
            # cursor positions
            cur_y=0,
            cur_x=0
        )

        # keymaps/bindings
        self.keyfunc: Dict[str, Callable] = {}
        self._init_keyfunc()

    def list_add(self, internal_list: List, entry: Any) -> None:
        """
        Add entry to internal list
        """

        # add entry to own list
        internal_list.append(entry)

        # if terminal size is invalid, stop here
        if not self.config.is_terminal_valid():
            return

        # if this window belongs to an active conversation, redraw it
        if self.conversation.is_active():
            self.redraw()
        elif self is MAIN_WINS["log"]:
            # if this is the main log, display it anyway if there is nothing
            # else active
            if self.conversation.is_any_active():
                return
            self.redraw()

    def _redraw_win(self) -> None:
        """
        Redraw entire window
        """

        # if terminal size is invalid, stop here
        if not self.config.is_terminal_valid():
            return

        # screen/window properties
        win_size_y, win_size_x = self.win.getmaxyx()
        self.win.erase()

        # color settings on
        self.win.attrset(self.config.attr["win_border"])

        # window border
        max_y, max_x = MAIN_WINS["screen"].getmaxyx()
        if not win_size_y == max_y or not win_size_x == max_x:
            self.win.border()

        # window title
        max_title_len = min(len(self.title), win_size_x - 3)
        title = self.title[:max_title_len]
        if title != "":
            title = title[:-1] + " "
        if self.config.settings["show_title"]:
            self.win.addstr(0, 2, title)

        self.win.refresh()

    def _move_pad(self) -> None:
        """
        Move the pad
        """

        # get window size
        win_size_y, win_size_x = self.win.getmaxyx()

        # get current cursor positions
        self.state.cur_y, self.state.cur_x = self.pad.getyx()

        # move pad right, if cursor leaves window area on the right
        if self.state.cur_x > self.state.pad_x + (win_size_x - 3):
            self.state.pad_x = self.state.cur_x - (win_size_x - 3)

        # move pad left, if cursor leaves current pad position on the left
        if self.state.cur_x < self.state.pad_x:
            self.state.pad_x = self.state.cur_x

        # move pad down, if cursor leaves window area at the bottom
        if self.state.cur_y > self.state.pad_y + (win_size_y - 3):
            self.state.pad_y = self.state.cur_y - (win_size_y - 3)

        # move pad up, if cursor leaves current pad position at the top
        if self.state.cur_y < self.state.pad_y:
            self.state.pad_y = self.state.cur_y

    def _check_borders(self) -> None:
        """
        Check borders
        """

        # get sizes
        win_size_y, win_size_x = self.win.getmaxyx()
        pad_size_y, pad_size_x = self.pad.getmaxyx()

        # do not move visible area too far to the left
        if self.state.pad_x < 0:
            self.state.pad_x = 0

        # do not move visible area too far to the right
        if self.state.pad_x + (win_size_x - 3) > pad_size_x:
            self.state.pad_x = pad_size_x - (win_size_x - 3)

        # do not move visible area too far up
        if self.state.pad_y < 0:
            self.state.pad_y = 0

        # do not move visible area too far down
        if self.state.pad_y + (win_size_y - 3) > pad_size_y:
            self.state.pad_y = pad_size_y - (win_size_y - 3)

    def redraw_pad(self) -> None:
        """
        Redraw pad in window
        """

        # implemented in other classes

    def redraw(self) -> None:
        """
        Redraw the window
        """

        self._redraw_win()
        self.redraw_pad()

    def resize_win(self, win_y_max: int, win_x_max: int) -> None:
        """
        Resize window
        """

        # if terminal size is invalid, stop here
        if not self.config.is_terminal_valid():
            return

        # TODO: change function parameters?
        self.win.resize(win_y_max, win_x_max)

    def move_win(self, pos_y: int, pos_x: int) -> None:
        """
        Move window
        """

        # if terminal size is invalid, stop here
        if not self.config.is_terminal_valid():
            return

        self.win.mvwin(pos_y, pos_x)

    def _go_back(self, *args: Any) -> None:
        """
        User input: go back
        """

        # implemented in sub classes

    def _cursor_right(self, *args: Any) -> None:
        """
        User input: cursor right
        """

        # implemented in sub classes

    def _cursor_left(self, *args: Any) -> None:
        """
        User input: cursor left
        """

        # implemented in sub classes

    def _cursor_down(self, *args: Any) -> None:
        """
        User input: cursor down
        """

        # implemented in sub classes

    def _cursor_up(self, *args: Any) -> None:
        """
        User input: cursor up
        """

        # implemented in sub classes

    def _cursor_top(self, *args: Any) -> None:
        """
        User input: cursor top
        """

        # implemented in sub classes

    def _cursor_bottom(self, *args: Any) -> None:
        """
        User input: cursor bottom
        """

        # implemented in sub classes

    def _cursor_page_up(self, *args: Any) -> None:
        """
        User input: cursor page up
        """

        # implemented in sub classes

    def _cursor_page_down(self, *args: Any) -> None:
        """
        User input: cursor page down
        """

        # implemented in sub classes

    def _send_msg(self, *args: Any) -> None:
        """
        User input: send message
        """

        # implemented in sub classes

    def _delete_char(self, *args: Any) -> None:
        """
        User input: delete character
        """

        # implemented in sub classes

    def _delete_char_right(self, *args: Any) -> None:
        """
        User input: delete character on the right of current cursor position
        """

        # implemented in sub classes

    def _cursor_msg_start(self, *args: Any) -> None:
        """
        User input: move cursor to message start
        """

        # implemented in sub classes

    def _cursor_msg_end(self, *args: Any) -> None:
        """
        User input: move cursor to message end
        """

        # implemented in sub classes

    def _cursor_line_start(self, *args: Any) -> None:
        """
        User input: move cursor to line start
        """

        # implemented in sub classes

    def _cursor_line_end(self, *args: Any) -> None:
        """
        User input: move cursor to line end
        """

        # implemented in sub classes

    def _delete_line_end(self, *args: Any) -> None:
        """
        User input: delete from cursor to end of current line
        """

        # implemented in sub classes

    def _delete_line(self, *args: Any) -> None:
        """
        User input: delete current line
        """

        # implemented in sub classes

    def _zoom_win(self, *args: Any) -> None:
        """
        User input: zoom current window
        """

        # implemented in sub classes

    def _zoom_win_url(self, *args: Any) -> None:
        """
        User input: zoom current window
        """

        # implemented in sub classes

    def _go_log(self, *args: Any) -> None:
        """
        User input: go to the conversations log/history
        """

        # implemented in sub classes

    def _go_next(self, *args: Any) -> None:
        """
        User input: go to conversation with new messages or more recently used
        conversation
        """

        # implemented in sub classes

    def _go_prev(self, *args: Any) -> None:
        """
        User input: go to previously used conversation
        """

        # implemented in sub classes

    def _go_conv(self, *args: Any) -> None:
        """
        User input: go to specific conversation
        """

        # implemented in sub classes

    def _search(self, *args: Any) -> None:
        """
        User input: search
        """

        # implemented in sub classes

    def _search_next(self, *args: Any) -> None:
        """
        User input: search for next match
        """

        # implemented in sub classes

    def _search_prev(self, *args: Any) -> None:
        """
        User input: search for previous match
        """

        # implemented in sub classes

    def _enter(self, *args: Any) -> None:
        """
        User input: enter
        """

        # implemented in sub classes

    def _tab(self, *args: Any) -> None:
        """
        User input: tab
        """

        # implemented in sub classes

    def _quit(self, *args: Any) -> None:
        """
        User input: quit nuqql
        """

        # implemented in sub classes

    def handle_keybinds(self, *args: Any, keybinds: Dict[str, str] = None,
                        keyfunc: Dict[str, Callable] = None) -> bool:
        """
        Handle special keys
        """

        # input character is first argument
        char = args[0]

        # set keybinds and keyfunc, if not in parameters
        if not keybinds:
            keybinds = self.config.keybinds
        if not keyfunc:
            keyfunc = self.keyfunc

        # look for special key mappings in keymap
        try:
            cint = ord(char)
        except (TypeError, ValueError):
            cint = char
        if cint in self.config.keymap and \
           self.config.keymap[cint] in keybinds:
            func = keyfunc[keybinds[self.config.keymap[cint]]]
            func(*args[1:])     # call function with remaining arguments
            return True         # handled a special key

        # no special key
        return False

    def _init_keyfunc(self) -> None:
        """
        Initialize key to function mapping
        """

        self.keyfunc = {
            "CURSOR_RIGHT": self._cursor_right,
            "CURSOR_LEFT": self._cursor_left,
            "CURSOR_DOWN": self._cursor_down,
            "CURSOR_UP": self._cursor_up,
            "CURSOR_TOP": self._cursor_top,
            "CURSOR_BOTTOM": self._cursor_bottom,
            "CURSOR_PAGE_UP": self._cursor_page_up,
            "CURSOR_PAGE_DOWN": self._cursor_page_down,
            "CURSOR_MSG_START": self._cursor_msg_start,
            "CURSOR_MSG_END": self._cursor_msg_end,
            "CURSOR_LINE_START": self._cursor_line_start,
            "CURSOR_LINE_END": self._cursor_line_end,
            "DEL_CHAR": self._delete_char,
            "DEL_CHAR_RIGHT": self._delete_char_right,
            "DEL_LINE_END": self._delete_line_end,
            "DEL_LINE": self._delete_line,
            "ENTER": self._enter,
            "GO_BACK": self._go_back,
            "GO_NEXT": self._go_next,
            "GO_PREV": self._go_prev,
            "GO_CONV": self._go_conv,
            "GO_LOG": self._go_log,
            "QUIT": self._quit,
            "SEARCH": self._search,
            "SEARCH_NEXT": self._search_next,
            "SEARCH_PREV": self._search_prev,
            "SEND_MSG": self._send_msg,
            "TAB": self._tab,
            "WIN_ZOOM": self._zoom_win,
            "WIN_ZOOM_URL": self._zoom_win_url,
        }
