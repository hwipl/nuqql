"""
Nuqql UI Log Windows
"""

import logging

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, List

from .win import Win, MAIN_WINS

if TYPE_CHECKING:   # imports for typing
    # pylint: disable=cyclic-import
    from nuqql.config import WinConfig  # noqa
    from nuqql.conversation import Conversation  # noqa
    from nuqql.conversation.history import LogMessage  # noqa

logger = logging.getLogger(__name__)


class LogWin(Win):
    """
    Class for Log Windows
    """

    def __init__(self, config: "WinConfig", conversation: "Conversation",
                 title: str) -> None:
        Win.__init__(self, config, conversation, title)

        # list entries/message log
        self.list: List["LogMessage"] = []

        # string to search for
        self.search_input = ""
        self.search_text = ""
        self.search_keyfunc = {
            "DEL_CHAR":     self._process_search_input_del_char,
            "ENTER":        self._process_search_input_enter,
            "GO_BACK":      self._process_search_input_abort,
        }

        # user's view of the log
        self.view = SimpleNamespace(
            begin=-1,
            cur=-1
        )

    def add(self, entry: "LogMessage") -> None:
        """
        Add entry to internal list
        """

        # add entry to own list via base class function
        logger.debug("adding entry %s", entry)
        self.list_add(self.list, entry)

    def _get_log_view(self, props: SimpleNamespace) -> List["LogMessage"]:
        """
        Get a slice of the log in the current view of the pad
        """

        if self.view.begin == -1:
            start = len(self.list) - (props.win_size_y - props.pad_y_delta)
            start = max(start, 0)   # make sure it's >= 0
            end = len(self.list)
            self.view.cur = start
        else:
            start = self.view.begin
            end = props.win_size_y - props.pad_y_delta
            self.view.cur = start

        log_slice = []
        for index, msg in enumerate(self.list[start:]):
            if index > end:
                break
            log_slice.append(msg)

        return log_slice

    def _print_msg(self, msg: str, last: bool = False,
                   output: bool = True) -> int:
        """
        Print a single log message. Handle newlines in the log message and add
        additional line breaks for parts of the log message that are too long
        for the log window's pad width.
        """

        # get size of the pad
        max_y, max_x = self.pad.getmaxyx()

        # split the message at newlines and handle each line separately
        num_output = 0
        lines = msg.split("\n")
        for index, line in enumerate(lines):
            first = True
            while first or line:
                # always print the first part of a line, even if it's empty.
                first = False
                if output:
                    self.pad.insnstr(max_y - 1, 0, line, max_x)
                num_output += 1

                # drop all characters we printed from the current line
                line = line[max_x:]
                if not line and index == len(lines) - 1 and last:
                    # if we printed the last part of the last line of the last
                    # message, do not increase pad size and do not move cursor
                    break

                # there are more parts of the current line, more lines, or more
                # messages coming. Increase pad size and move cursor.
                if not output:
                    continue
                max_y += 1
                self.pad.resize(max_y, max_x)

        self.pad.move(max_y - 1, max_x - 1)
        return num_output

    def _print_log(self, props: SimpleNamespace) -> None:
        """
        dump log messages and resize pad according to new lines added
        """

        # get the current slice of the log and start with a fresh pad size
        log_slice = self._get_log_view(props)
        self.pad.resize(1, props.pad_size_x)

        for index, msg in enumerate(log_slice):
            # set colors and attributes for message:
            if not msg.own:
                # message from buddy
                if msg.is_read:
                    # old message
                    self.pad.attrset(self.config.attr["log_win_text_peer_old"])
                else:
                    # new message
                    self.pad.attrset(self.config.attr["log_win_text_peer_new"])
            else:
                # message from you
                if msg.is_read:
                    # old message
                    self.pad.attrset(self.config.attr["log_win_text_self_old"])
                else:
                    # new message
                    self.pad.attrset(self.config.attr["log_win_text_self_new"])

            # output message
            if index < len(log_slice) - 1:
                self._print_msg(msg.read())
            else:
                self._print_msg(msg.read(), last=True)

    def _get_properties(self) -> SimpleNamespace:
        """
        Get window/pad properties, depending on max size and zoom
        """

        props = SimpleNamespace()
        props.max_y, props.max_x = MAIN_WINS["screen"].getmaxyx()
        if self.state.zoomed:
            # window is currently zoomed
            props.pos_y, props.pos_x = 0, 0
            props.pos_y_off, props.pos_x_off = 1, 0
            props.win_size_y, props.win_size_x = props.max_y, props.max_x
            props.pad_size_y, props.pad_size_x = (props.max_y - 2, props.max_x)
            props.pad_y_delta, props.pad_x_delta = 2, 0
        else:
            # window is not zoomed
            props.pos_y, props.pos_x = self.config.get_pos()
            props.pos_y_off, props.pos_x_off = 1, 1
            props.win_size_y, props.win_size_x = self.config.get_size()
            # use actual pad size, it will be resized later if necessary
            props.pad_size_y, props.pad_size_x = self.pad.getmaxyx()
            props.pad_y_delta, props.pad_x_delta = 2, 2

        return props

    def _pad_refresh(self, props: SimpleNamespace) -> None:
        """
        Helper for running move_pad(), check_borders(), and pad.refresh()
        """
        self._move_pad()
        self._check_borders()
        self.pad.refresh(self.state.pad_y, self.state.pad_x,
                         props.pos_y + props.pos_y_off,
                         props.pos_x + props.pos_x_off,
                         props.pos_y + props.win_size_y - props.pad_y_delta,
                         props.pos_x + props.win_size_x - props.pad_x_delta)

    def redraw_pad(self) -> None:
        # if terminal size is invalid, stop here
        if not self.config.is_terminal_valid():
            return

        # screen/pad properties
        props = self._get_properties()

        # if window was resized, resize pad size according to new window size
        if props.pad_size_x != props.win_size_x - props.pad_x_delta:
            props.pad_size_x = props.win_size_x - props.pad_x_delta
            self.pad.resize(props.pad_size_y, props.pad_size_x)
        if props.pad_size_y != props.win_size_y - props.pad_y_delta:
            props.pad_size_y = props.win_size_y - props.pad_y_delta
            self.pad.resize(props.pad_size_y, props.pad_size_x)
            self.state.pad_y = 0  # reset pad position

        # print log
        self.pad.erase()
        self._print_log(props)

        # check if visible part of pad needs to be moved and display it
        self.state.cur_y, self.state.cur_x = self.pad.getyx()
        self._pad_refresh(props)

    def _cursor_top(self, *args: Any) -> None:
        # jump to first line in log
        logger.debug("move cursor to top of log")
        if self.view.cur > 0:
            # view is not at the top yet, so move it there
            self.view.begin = 0
            self.redraw_pad()

        # move cursor to top
        self.state.cur_y, self.state.cur_x = 0, 0
        self.pad.move(self.state.cur_y, self.state.cur_x)
        props = self._get_properties()
        self._pad_refresh(props)

    def _cursor_bottom(self, *args: Any) -> None:
        # jump to last line in log
        logger.debug("move cursor to bottom of log")
        props = self._get_properties()
        view_size = props.win_size_y - props.pad_y_delta

        if self.view.cur < len(self.list) - view_size:
            # view is not at the bottom yet, so move it there
            self.view.begin = len(self.list) - view_size
            self.redraw_pad()

        # move cursor to bottom
        self.state.cur_y, self.state.cur_x = self.pad.getmaxyx()[0] - 1, 0
        self.pad.move(self.state.cur_y, self.state.cur_x)
        props = self._get_properties()
        self._pad_refresh(props)

    def _cursor_page_up(self, *args: Any) -> None:
        # move cursor up one page until first entry in log
        logger.debug("move cursor up one page")
        props = self._get_properties()
        view_size = props.win_size_y - props.pad_y_delta

        cur_y, _cur_x = self.pad.getyx()
        lines_left = view_size - cur_y
        if lines_left <= 0:
            # we can stay in the current view
            self.state.cur_y = 0 - lines_left
            self.state.cur_x = 0
        else:
            # we need to get more messages
            while self.view.cur > 0:
                self.view.begin = self.view.cur - 1

                # get next message and see if we have enough lines
                log_slice = self._get_log_view(props)
                num_lines = self._print_msg(log_slice[0].read(), output=False)
                lines_left -= num_lines
                if lines_left <= 0:
                    # we got all missing lines
                    break

            # show updated log_view in pad and set cursor position
            self.redraw_pad()
            self.state.cur_y = max(0, 0 - lines_left)
            self.state.cur_x = 0

        # move cursor up to previously determined position
        self.pad.move(self.state.cur_y, self.state.cur_x)
        props = self._get_properties()
        self._pad_refresh(props)

    def _cursor_page_down(self, *args: Any) -> None:
        # move cursor down one page until last entry in log
        logger.debug("move cursor down one page")
        props = self._get_properties()
        view_size = props.win_size_y - props.pad_y_delta

        cur_y, _cur_x = self.pad.getyx()
        max_y, _max_x = self.pad.getmaxyx()
        lines_left = view_size - (max_y - 1 - cur_y)
        if lines_left <= 0:
            # we can stay in the current view
            self.state.cur_y = max_y - 1 + lines_left
            self.state.cur_x = 0
        else:
            # we need to get more messages
            while self.view.cur < len(self.list) - view_size:
                self.view.begin = self.view.cur + 1

                # get next message and see if we have enough lines
                log_slice = self._get_log_view(props)
                num_lines = self._print_msg(log_slice[-1].read(), output=False)
                lines_left -= num_lines
                if lines_left <= 0:
                    # we got all missing lines
                    break

            # show updated log_view in pad and set cursor position
            self.redraw_pad()
            self.state.pad_y = 0    # make sure we only show up to first line
            max_y, _max_x = self.pad.getmaxyx()
            self.state.cur_y = min(max_y - 1, max_y - 1 + lines_left)
            self.state.cur_x = 0

        # move cursor down to previously determined position
        self.pad.move(self.state.cur_y, self.state.cur_x)
        props = self._get_properties()
        self._pad_refresh(props)

    def _cursor_up(self, *args: Any) -> None:
        # move cursor up until first entry in list
        logger.debug("move cursor up")
        if self.state.cur_y > 0:
            # inside current view, simply move cursor up
            self.state.cur_y, self.state.cur_x = self.state.cur_y - 1, 0

        elif self.view.cur > 0:
            # at top of current view, move view up
            self.view.begin = self.view.cur - 1

            # if the previous message is multi line, only go to last line
            props = self._get_properties()
            log_slice = self._get_log_view(props)
            num_lines = self._print_msg(log_slice[0].read(), output=False)
            self.redraw_pad()
            self.state.cur_y, self.state.cur_x = num_lines - 1, 0

        # move cursor up
        self.pad.move(self.state.cur_y, self.state.cur_x)
        props = self._get_properties()
        self._pad_refresh(props)

    def _cursor_down(self, *args: Any) -> None:
        # move cursor down until end of list
        logger.debug("move cursor down")
        props = self._get_properties()
        lines = self.pad.getmaxyx()[0] - 1
        view_size = props.win_size_y - props.pad_y_delta

        if self.state.cur_y < lines:
            # inside current view, simply move cursor down
            self.state.cur_y, self.state.cur_x = self.state.cur_y + 1, 0

        elif self.view.cur < len(self.list) - view_size:
            # at bottom of current view, move view down
            self.view.begin = self.view.cur + 1

            # if the next message is multi line, only go to first line
            props = self._get_properties()
            log_slice = self._get_log_view(props)
            num_lines = self._print_msg(log_slice[-1].read(), output=False)
            self.redraw_pad()
            self.state.pad_y = 0    # make sure we only show up to first line
            self.state.cur_y, self.state.cur_x = \
                self.pad.getmaxyx()[0] - num_lines, 0

        # move cursor down
        self.pad.move(self.state.cur_y, self.state.cur_x)
        props = self._get_properties()
        self._pad_refresh(props)

    def zoom_win(self) -> None:
        """
        Zoom in and out of log window
        """

        # get positions and sizes for zoomed and normal mode
        if self.state.zoomed:
            logger.debug("zooming out")
            self.state.zoomed = False
        else:
            logger.debug("zooming in")
            self.state.zoomed = True
        props = self._get_properties()

        # resize window and pad
        self.resize_win(props.win_size_y, props.win_size_x)
        self.move_win(props.pos_y, props.pos_x)
        self.pad.resize(props.win_size_y - props.pad_y_delta,
                        props.win_size_x - props.pad_x_delta)
        self._move_pad()
        self._check_borders()

        # redraw everything
        if self.state.zoomed:
            # make list win and input win invisible
            self.conversation.wins.list_win.state.visible = False
            self.conversation.wins.input_win.state.visible = False

            # redraw window
            self.redraw()
        else:
            # make list win and input win visible
            self.conversation.wins.list_win.state.visible = True
            self.conversation.wins.input_win.state.visible = True

            # redraw everything
            MAIN_WINS["screen"].clear()
            MAIN_WINS["screen"].refresh()
            self.conversation.wins.list_win.redraw()
            self.conversation.wins.log_win.redraw()
            self.conversation.wins.input_win.redraw()

    def go_back(self, *_args: Any) -> None:
        """
        Go back to input win
        """

        logger.debug("leaving window")

        # if window was zoomed, switch back to normal view
        if self.state.zoomed:
            self.zoom_win()

        # reactivate input window
        self.state.active = True
        self.conversation.wins.input_win.state.active = True

        # show last messages
        self.view.begin = -1

        # redraw pad to display messages received in the meantime...
        self.redraw_pad()

        # ...and clear notifications for these messages
        self.conversation.clear_notifications()

    def _search(self, *args: Any) -> None:
        """
        Search: Start a new search dialog
        """

        logger.debug("starting search input mode")

        # enter search input mode
        self.search_input = "/"
        self._process_search_input_show()

    def _process_search_input_show(self) -> None:
        """
        Show current search string
        """

        if not self.search_input:
            # show window border again
            self.redraw()
            return

        # TODO: use config get_size or something?
        max_y, max_x = self.win.getmaxyx()
        show = self.search_input.ljust(max_x - 4, " ")
        self.win.addnstr(max_y - 1, 2, show, max_x - 4)
        self.win.refresh()

    def _process_search_input_del_char(self) -> None:
        """
        Delete char from search input field
        """

        if not self.search_input:
            return

        logger.debug("deleting char from search input")
        self.search_input = self.search_input[:-1]
        self._process_search_input_show()

    def _process_search_input_enter(self) -> None:
        """
        Search for string in search input field
        """

        if not self.search_input:
            return

        self.search_text = self.search_input[1:]
        logger.debug("starting search for %s", self.search_text)
        self.search_input = ""
        self._process_search_input_show()
        self._search_next()

    def _process_search_input_abort(self) -> None:
        """
        Abort search
        """

        logger.debug("leaving search input mode")
        self.search_input = ""
        self._process_search_input_show()

    def _search_next(self, *args: Any) -> None:
        """
        Search for next match
        """

        # skip this if we are not in search mode
        if self.search_text == "":
            return

        # init
        props = self._get_properties()

        # search views for text until first view
        while self.view.cur >= 0:
            # search current view for text until first line
            while self.state.cur_y >= 0:
                _cur_text = self.pad.instr(self.state.cur_y, 0)
                cur_text = _cur_text.decode()   # type: ignore
                cur_text = cur_text[:self.state.cur_x]
                index = cur_text.rfind(self.search_text)
                if index != -1:
                    # found it, stop here
                    self.pad.move(self.state.cur_y, index)
                    self.state.cur_y, self.state.cur_x = self.pad.getyx()

                    self._pad_refresh(props)
                    return

                # keep searching in next line
                self.state.cur_y -= 1
                self.state.cur_x = props.pad_size_x

            # reached end of view, move view further up
            if self.view.cur == 0:
                # reached top already
                break
            self._cursor_up()
            self.state.cur_x = self.pad.getmaxyx()[1] - 1

        # make sure current cursor position is visible even if nothing found
        self._pad_refresh(props)

    def search_next(self) -> None:
        """
        Helper for calling search from other windows
        """

        # make sure we find something on the current line
        logger.debug("searching for next match")
        self.state.cur_x = self.pad.getmaxyx()[1]
        self._search_next()

    def _search_prev(self, *args: Any) -> None:
        """
        Search for previous match
        """

        # skip this if we are not in search mode
        if self.search_text == "":
            return

        logger.debug("searching for previous match")

        # init
        props = self._get_properties()
        view_size = props.win_size_y - props.pad_y_delta

        # if we are already on a match, skip it
        _cur_text = self.pad.instr(self.state.cur_y, 0)
        cur_text = _cur_text.decode()   # type: ignore
        cur_text = cur_text[self.state.cur_x:]
        cur_text = cur_text[:len(self.search_text)]
        if cur_text == self.search_text:
            self.state.cur_x += len(self.search_text)

        # search views for text until last view
        while self.view.cur <= max(0, len(self.list) - view_size):
            # search current view for text until end of view
            while self.state.cur_y <= self.pad.getmaxyx()[0]:
                _cur_text = self.pad.instr(self.state.cur_y, 0)
                cur_text = _cur_text.decode()   # type: ignore
                cur_text = cur_text[self.state.cur_x:]
                index = cur_text.find(self.search_text)

                # found it, stop here
                if index != -1:
                    self.pad.move(self.state.cur_y, self.state.cur_x + index)
                    self.state.cur_y, self.state.cur_x = self.pad.getyx()

                    self._pad_refresh(props)
                    return

                # keep searching
                self.state.cur_y += 1
                self.state.cur_x = 0    # set it to first position in line

            # reached end of view, move view further down
            if self.view.cur == max(0, len(self.list) - view_size):
                # reached bottom already
                pad_size_y, pad_size_x = self.pad.getmaxyx()
                self.pad.move(pad_size_y - 1, pad_size_x - 1)
                self.state.cur_y, self.state.cur_x = self.pad.getyx()
                break
            self._cursor_down()

        # make sure current cursor position is visible even if nothing found
        self._pad_refresh(props)

    def process_input(self, char: str) -> None:
        """
        Process user input
        """

        self.state.cur_y, self.state.cur_x = self.pad.getyx()

        # check if we are in search input mode
        if self.search_input:
            # search input: look for special key mapping or process as text
            if not self.handle_keybinds(
                    char, keybinds=self.config.keybinds["__search__"],
                    keyfunc=self.search_keyfunc):
                # no special key, add character to search input field
                try:
                    self.search_input += char
                    self._process_search_input_show()
                except (ValueError, TypeError):
                    pass
        else:
            # look for special key mappings in keymap
            self.handle_keybinds(char)

        # display changes in the pad
        # TODO: switch this back on and remove redraw code from other methods?
        # self.redraw_pad()
