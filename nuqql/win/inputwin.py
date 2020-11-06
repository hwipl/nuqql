"""
Nuqql UI Input Windows
"""

import curses
import logging
import unicodedata

from typing import TYPE_CHECKING, Any

from .win import Win, MAIN_WINS

if TYPE_CHECKING:   # imports for typing
    # pylint: disable=cyclic-import
    from nuqql.config import WinConfig  # noqa
    from nuqql.conversation import Conversation  # noqa

logger = logging.getLogger(__name__)


class InputWin(Win):
    """
    Class for Input Windows
    """

    def __init__(self, config: "WinConfig", conversation: "Conversation",
                 title: str) -> None:
        Win.__init__(self, config, conversation, title)

        # input message
        self.msg = ""

    def redraw_pad(self) -> None:
        # if terminal size is invalid, stop here
        if not self.config.is_terminal_valid():
            return

        pos_y, pos_x = self.config.get_pos()
        win_size_y, win_size_x = self.config.get_size()

        self._move_pad()
        self._check_borders()
        self.pad.refresh(self.state.pad_y, self.state.pad_x,
                         pos_y + 1, pos_x + 1,
                         pos_y + win_size_y - 2,
                         pos_x + win_size_x - 2)

    def _cursor_up(self, *args: Any) -> None:
        segment = args[0]
        if self.state.cur_y > 0:
            logger.debug("moving cursor up")
            self.pad.move(self.state.cur_y - 1,
                          min(self.state.cur_x,
                              len(segment[self.state.cur_y - 1])))

        # display changes in the pad
        self.redraw_pad()

    def _cursor_down(self, *args: Any) -> None:
        # pad properties
        pad_y_max, unused_pad_x_max = self.pad.getmaxyx()

        segment = args[0]
        if self.state.cur_y < pad_y_max and \
           self.state.cur_y < len(segment) - 1:
            logger.debug("moving cursor down")
            self.pad.move(self.state.cur_y + 1,
                          min(self.state.cur_x,
                              len(segment[self.state.cur_y + 1])))

        # display changes in the pad
        self.redraw_pad()

    def _cursor_left(self, *args: Any) -> None:
        if self.state.cur_x > 0:
            logger.debug("moving cursor left")
            self.pad.move(self.state.cur_y, self.state.cur_x - 1)

        # display changes in the pad
        self.redraw_pad()

    def _cursor_right(self, *args: Any) -> None:
        # pad properties
        unused_pad_y_max, pad_x_max = self.pad.getmaxyx()

        segment = args[0]
        if self.state.cur_x < pad_x_max and \
           self.state.cur_x < len(segment[self.state.cur_y]):
            logger.debug("moving cursor right")
            self.pad.move(self.state.cur_y, self.state.cur_x + 1)

        # display changes in the pad
        self.redraw_pad()

    def _cursor_line_start(self, *args: Any) -> None:
        if self.state.cur_x > 0:
            logger.debug("moving cursor to start of line")
            self.pad.move(self.state.cur_y, 0)

        # display changes in the pad
        self.redraw_pad()

    def _cursor_line_end(self, *args: Any) -> None:
        # pad properties
        unused_pad_y_max, pad_x_max = self.pad.getmaxyx()

        segment = args[0]
        if self.state.cur_x < pad_x_max and \
           self.state.cur_x < len(segment[self.state.cur_y]):
            logger.debug("moving cursor to end of line")
            self.pad.move(self.state.cur_y, len(segment[self.state.cur_y]))

        # display changes in the pad
        self.redraw_pad()

    def _cursor_msg_start(self, *args: Any) -> None:
        if self.state.cur_y > 0 or self.state.cur_x > 0:
            logger.debug("moving cursor to start of message")
            self.pad.move(0, 0)

        # display changes in the pad
        self.redraw_pad()

    def _cursor_msg_end(self, *args: Any) -> None:
        segment = args[0]
        if self.state.cur_y < len(segment) - 1 or \
           self.state.cur_x < len(segment[-1]):
            logger.debug("moving cursor to end of message")
            self.pad.move(len(segment) - 1, len(segment[-1]))

        # display changes in the pad
        self.redraw_pad()

    def _send_msg(self, *args: Any) -> None:
        # do not send empty messages
        if self.msg == "":
            return

        logger.debug("sending message %s", self.msg)

        # let conversation actually send the message
        self.conversation.send_msg(self.msg)

        # reset input
        self.msg = ""
        self.pad.erase()

        # reset pad size
        win_size_y, win_size_x = self.win.getmaxyx()
        self.pad.resize(win_size_y - 2, win_size_x - 2)

        # display changes in the pad
        self.redraw_pad()

    def _delete_char(self, *args: Any) -> None:
        segment = args[0]
        if self.state.cur_x > 0:
            # delete charater within a line
            logger.debug("deleting character")
            segment[self.state.cur_y] = \
                segment[self.state.cur_y][:self.state.cur_x - 1] +\
                segment[self.state.cur_y][self.state.cur_x:]
        elif self.state.cur_y > 0:
            # delete newline
            logger.debug("deleting newline character")
            old_prev_len = len(segment[self.state.cur_y - 1])
            segment[self.state.cur_y - 1] = segment[self.state.cur_y - 1] +\
                segment[self.state.cur_y]
            segment = segment[:self.state.cur_y] + \
                segment[self.state.cur_y + 1:]
            # resize pad if concatenated line is longer than pad
            pad_size_y, pad_size_x = self.pad.getmaxyx()
            if len(segment[self.state.cur_y - 1]) + 2 > pad_size_x:
                pad_size_x = len(segment[self.state.cur_y - 1]) + 2
                self.pad.resize(pad_size_y, pad_size_x)
        else:
            # at top left, do nothing
            return

        # reconstruct and display message
        self.msg = "\n".join(segment)
        self.pad.erase()
        self.pad.addstr(self.msg)
        # move cursor to new position
        if self.state.cur_x > 0:
            self.pad.move(self.state.cur_y, self.state.cur_x - 1)
        elif self.state.cur_y > 0:
            self.pad.move(self.state.cur_y - 1, old_prev_len)

        # display changes in the pad
        self.redraw_pad()

    def _delete_char_right(self, *args: Any) -> None:
        # argument is segemented message, i.e. lines of the message
        segment = args[0]

        # delete character
        if self.state.cur_x < len(segment[self.state.cur_y]):
            # delete charater within a line
            logger.debug("deleting right character")
            segment[self.state.cur_y] = \
                segment[self.state.cur_y][:self.state.cur_x] +\
                segment[self.state.cur_y][self.state.cur_x + 1:]
        elif self.state.cur_y < len(segment) - 1:
            # delete newline
            logger.debug("deleting right newline character")
            segment[self.state.cur_y] = segment[self.state.cur_y] +\
                segment[self.state.cur_y + 1]
            del segment[self.state.cur_y + 1]
            # resize pad if concatenated line is longer than pad
            pad_size_y, pad_size_x = self.pad.getmaxyx()
            if len(segment[self.state.cur_y]) + 2 > pad_size_x:
                pad_size_x = len(segment[self.state.cur_y]) + 2
                self.pad.resize(pad_size_y, pad_size_x)
        else:
            # at bottom right, do nothing
            return

        # reconstruct and display message
        self.msg = "\n".join(segment)
        self.pad.erase()
        self.pad.addstr(self.msg)

        # move cursor to new position
        self.pad.move(self.state.cur_y, self.state.cur_x)

        # display changes in the pad
        self.redraw_pad()

    def _delete_line_end(self, *args: Any) -> None:
        segment = args[0]

        # delete from cursor to end of line
        logger.debug("deleting from cursor to end of line")
        segment[self.state.cur_y] = \
            segment[self.state.cur_y][:self.state.cur_x]

        # reconstruct message
        self.msg = "\n".join(segment)
        self.pad.erase()
        self.pad.addstr(self.msg)

        # display changes in the pad
        self.redraw_pad()

    def _delete_line(self, *args: Any) -> None:
        segment = args[0]

        # delete the current line
        logger.debug("deleting current line")
        del segment[self.state.cur_y]

        # reconstruct message
        self.msg = "\n".join(segment)
        self.pad.erase()
        self.pad.addstr(self.msg)

        # move cursor to new position
        if len(segment) <= self.state.cur_y:
            self.state.cur_y = max(0, len(segment) - 1)
        if not segment:
            self.state.cur_x = 0
        elif len(segment[self.state.cur_y]) < self.state.cur_x:
            self.state.cur_x = len(segment[self.state.cur_y])
        self.pad.move(self.state.cur_y, self.state.cur_x)

        # display changes in the pad
        self.redraw_pad()

    def go_back(self, *_args: Any) -> None:
        """
        Close conversation windows
        """

        logger.debug("leaving input window")
        self.state.active = False
        self.conversation.wins.log_win.state.active = False

        # disable cursor
        curses.curs_set(0)

        # redraw main windows
        MAIN_WINS["log"].redraw()

        # assume user read all messages and set lastread to last message
        self.conversation.set_lastread()

    def _go_log(self, *args: Any) -> None:
        """
        Jump to log
        """

        logger.debug("jumping to log")
        self.state.active = False
        self.conversation.wins.log_win.state.active = True
        self.conversation.wins.log_win.zoom_win()

    def _go_log_search_url(self, *args: Any) -> None:
        """
        Jump to log and search for next url
        """

        logger.debug("jumping to log and starting url search")
        self._go_log()
        self.conversation.wins.log_win.search_text = "http"
        self.conversation.wins.log_win.search_next()

    def _go_next(self, *args: Any) -> None:
        """
        Jump to a conversation with new messages or more recently used
        conversation
        """

        logger.debug("jumping to next conversation")

        # find next new conversation
        set_last_used = True
        conv = self.conversation.get_new()
        if not conv:
            # no new messages, try to go to next conversation
            logger.debug("conversation with new messages not found")
            conv = self.conversation.get_next()
            set_last_used = False
        if not conv:
            # nothing found, return
            logger.debug("next conversation not found")
            return

        # deactivate this and switch to other conversation
        self.go_back()
        conv.wins.list_win.jump_to_conv(conv, set_last_used=set_last_used)

    def _go_prev(self, *args: Any) -> None:
        """
        Jump to a previously used conversation
        """

        prev = self.conversation.get_prev()
        if not prev:
            return

        # deactivate this and switch to other conversation
        logger.debug("jumping to previous conversation")
        self.go_back()
        prev.wins.list_win.jump_to_conv(prev, set_last_used=False)

    def _go_conv(self, *args: Any) -> None:
        """
        Go to a specific conversation
        """

        # deactivate this and switch to filter mode in list window
        logger.debug("jumping to specific conversation")
        self.go_back()
        self.conversation.wins.list_win.go_conv()

    def _tab(self, *args: Any) -> None:
        # convert tab to spaces
        for _i in range(4):
            self.process_input(" ")

    def process_input(self, char: str) -> None:
        """
        Process user input (character)
        """

        segments = self.msg.split("\n")
        self.state.cur_y, self.state.cur_x = self.pad.getyx()
        pad_size_y, pad_size_x = self.pad.getmaxyx()

        # look for special key mappings in keymap or process as text
        if not self.handle_keybinds(char, segments):
            # insert new character into segments
            if not isinstance(char, str):
                return
            if char != "\n" and unicodedata.category(char)[0] == "C":
                return
            # make sure new char fits in the pad
            if len(segments) == pad_size_y - 1 and char == "\n":
                pad_size_y += 1
                self.pad.resize(pad_size_y, pad_size_x)
            if len(segments[self.state.cur_y]) == pad_size_x - 1 and \
               char != "\n":
                pad_size_x += 1
                self.pad.resize(pad_size_y, pad_size_x)

            segments[self.state.cur_y] = \
                segments[self.state.cur_y][:self.state.cur_x] + char +\
                segments[self.state.cur_y][self.state.cur_x:]
            # reconstruct orginal message for output in pad
            self.msg = "\n".join(segments)
            # reconstruct segments in case newline character was entered
            segments = self.msg.split("\n")
            # output new message in pad
            self.pad.erase()
            self.pad.addstr(self.msg)
            # move cursor to new position
            if char == "\n":
                self.pad.move(self.state.cur_y + 1, 0)
            else:
                self.pad.move(self.state.cur_y, self.state.cur_x + 1)
            # display changes in the pad
            self.redraw_pad()
