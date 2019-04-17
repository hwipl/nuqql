"""
Nuqql UI Windows
"""

import curses
import math

# screen and main windows
MAIN_WINS = {}


class Win:
    """
    Base class for Windows
    """

    def __init__(self, config, conversation, title):
        # configuration
        self.config = config

        # is window active?
        self.active = False

        # get window properties
        max_y, max_x = MAIN_WINS["screen"].getmaxyx()
        size_y, size_x = self.config.get_size(max_y, max_x)
        pos_y, pos_x = self.config.get_pos(max_y, max_x)

        # new window
        self.win = curses.newwin(size_y, size_x, pos_y, pos_x)

        # new pad
        self.pad_y = 0
        self.pad_x = 0
        self.pad = curses.newpad(max_y - 2, max_x - 2)

        # cursor positions
        self.cur_y = 0
        self.cur_x = 0

        # input message
        self.msg = ""

        # list entries/message log
        self.list = []

        # keymaps/bindings
        self.keyfunc = {}
        self.init_keyfunc()

        # conversation
        self.conversation = conversation

        # window title
        # TODO: use conversation.name instead?
        self.title = " " + title + " "

    def redraw_win(self):
        """
        Redraw entire window
        """

        # screen/window properties
        max_y, max_x = MAIN_WINS["screen"].getmaxyx()
        unused_win_size_y, win_size_x = self.config.get_size(max_y, max_x)
        self.win.clear()

        # color settings on
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        self.win.attron(curses.color_pair(1) | curses.A_BOLD)

        # window border
        self.win.border()

        # window title
        max_title_len = min(len(self.title), win_size_x - 3)
        title = self.title[:max_title_len]
        if title != "":
            title = title[:-1] + " "
        self.win.addstr(0, 2, title)

        # color settings off
        self.win.attroff(curses.color_pair(1) | curses.A_BOLD)

        self.win.refresh()

    def move_pad(self):
        """
        Move the pad
        """

        # get window size
        win_size_y, win_size_x = self.win.getmaxyx()

        # get current cursor positions
        self.cur_y, self.cur_x = self.pad.getyx()

        # move pad right, if cursor leaves window area on the right
        if self.cur_x > self.pad_x + (win_size_x - 3):
            self.pad_x = self.cur_x - (win_size_x - 3)

        # move pad left, if cursor leaves current pad position on the left
        if self.cur_x < self.pad_x:
            self.pad_x = self.cur_x

        # move pad down, if cursor leaves window area at the bottom
        if self.cur_y > self.pad_y + (win_size_y - 3):
            self.pad_y = self.cur_y - (win_size_y - 3)

        # move pad up, if cursor leaves current pad position at the top
        if self.cur_y < self.pad_y:
            self.pad_y = self.cur_y

    def check_borders(self):
        """
        Check borders
        """

        # get sizes
        win_size_y, win_size_x = self.win.getmaxyx()
        pad_size_y, pad_size_x = self.pad.getmaxyx()

        # do not move visible area too far to the left
        if self.pad_x < 0:
            self.pad_x = 0

        # do not move visible area too far to the right
        if self.pad_x + (win_size_x - 3) > pad_size_x:
            self.pad_x = pad_size_x - (win_size_x - 3)

        # do not move visible area too far up
        if self.pad_y < 0:
            self.pad_y = 0

        # do not move visible area too far down
        if self.pad_y + (win_size_y - 3) > pad_size_y:
            self.pad_y = pad_size_y - (win_size_y - 3)

    def redraw_pad(self):
        """
        Redraw pad in window
        """

        # implemented in other classes

    def redraw(self):
        """
        Redraw the window
        """

        self.redraw_win()
        self.redraw_pad()

    def add(self, entry):
        """
        Add entry to internal list
        """

        # add entry to own list
        self.list.append(entry)

        # if this window belongs to an active conversation, redraw it
        if self.conversation.is_active():
            self.redraw()
        elif self is MAIN_WINS["log"]:
            # if this is the main log, display it anyway if there is nothing
            # else active
            if self.conversation.is_any_active():
                return
            self.redraw()

    def resize_win(self, win_y_max, win_x_max):
        """
        Resize window
        """

        # TODO: change function parameters?
        self.win.resize(win_y_max, win_x_max)

    def move_win(self, pos_y, pos_x):
        """
        Move window
        """

        self.win.mvwin(pos_y, pos_x)

    def go_back(self, *args):
        """
        User input: go back
        """

        # implemented in sub classes

    def cursor_right(self, *args):
        """
        User input: cursor right
        """

        # implemented in sub classes

    def cursor_left(self, *args):
        """
        User input: cursor left
        """

        # implemented in sub classes

    def cursor_down(self, *args):
        """
        User input: cursor down
        """

        # implemented in sub classes

    def cursor_up(self, *args):
        """
        User input: cursor up
        """

        # implemented in sub classes

    def send_msg(self, *args):
        """
        User input: send message
        """

        # implemented in sub classes

    def delete_char(self, *args):
        """
        User input: delete character
        """

        # implemented in sub classes

    def cursor_msg_start(self, *args):
        """
        User input: move cursor to message start
        """

        # implemented in sub classes

    def cursor_msg_end(self, *args):
        """
        User input: move cursor to message end
        """

        # implemented in sub classes

    def cursor_line_start(self, *args):
        """
        User input: move cursor to line start
        """

        # implemented in sub classes

    def cursor_line_end(self, *args):
        """
        User input: move cursor to line end
        """

        # implemented in sub classes

    def delete_line_end(self, *args):
        """
        User input: delete from cursor to end of current line
        """

        # implemented in sub classes

    def delete_line(self, *args):
        """
        User input: delete current line
        """

        # implemented in sub classes

    def init_keyfunc(self):
        """
        Initialize key to function mapping
        """

        self.keyfunc = {
            "GO_BACK": self.go_back,
            "CURSOR_RIGHT": self.cursor_right,
            "CURSOR_LEFT": self.cursor_left,
            "CURSOR_DOWN": self.cursor_down,
            "CURSOR_UP": self.cursor_up,
            "SEND_MSG": self.send_msg,
            "DEL_CHAR": self.delete_char,
            "CURSOR_MSG_START": self.cursor_msg_start,
            "CURSOR_MSG_END": self.cursor_msg_end,
            "CURSOR_LINE_START": self.cursor_line_start,
            "CURSOR_LINE_END": self.cursor_line_end,
            "DEL_LINE_END": self.delete_line_end,
            "DEL_LINE": self.delete_line,
        }


class ListWin(Win):
    """
    Class for List Windows
    """

    def redraw_pad(self):
        """
        Redraw pad in window
        """

        # screen/pad properties
        max_y, max_x = MAIN_WINS["screen"].getmaxyx()
        pos_y, pos_x = self.config.get_pos(max_y, max_x)
        win_size_y, win_size_x = self.win.getmaxyx()
        pad_size_y, pad_size_x = self.pad.getmaxyx()
        self.cur_y, self.cur_x = self.pad.getyx()
        self.pad.clear()

        # set colors
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        self.pad.attron(curses.color_pair(2))

        # sort list
        self.list.sort()

        # make sure all names fit into pad
        if len(self.list) > pad_size_y - 1:
            self.pad.resize(len(self.list) + 1, pad_size_x)

        # if there is an active conversation, move cursor to it
        for index, conv in enumerate(self.list):
            if conv.is_active():
                self.cur_y = index

        # print names in list window
        for index, conv in enumerate(self.list):
            # get name of element; cut if it's too long
            name = conv.get_name()
            name = name[:pad_size_x-1] + "\n"

            # print name
            if index == self.cur_y:
                # cursor is on conversation, highlight it in list
                self.pad.addstr(name, curses.A_REVERSE)
            else:
                # just show the conversation in list
                self.pad.addstr(name)

        # reset colors
        self.pad.attroff(curses.color_pair(2))

        # move cursor back to original or active conversation's position
        self.pad.move(self.cur_y, self.cur_x)

        # check if visible part of pad needs to be moved and display it
        self.move_pad()
        self.check_borders()
        self.pad.refresh(self.pad_y, self.pad_x,
                         pos_y + 1, pos_x + 1,
                         pos_y + win_size_y - 2,
                         pos_x + win_size_x - 2)

    def cursor_line_start(self, *args):
        # TODO: use other method and keybind with more fitting name?
        # move cursor up one page until first entry in log
        win_size_y, unused_win_size_x = self.win.getmaxyx()

        if self.cur_y > 0:
            if self.cur_y - (win_size_y - 2) >= 0:
                self.pad.move(self.cur_y - (win_size_y - 2), self.cur_x)
            else:
                self.pad.move(0, self.cur_x)

    def cursor_line_end(self, *args):
        # TODO: use other method and keybind with more fitting name?
        # move cursor down one page until last entry in log
        win_size_y, unused_win_size_x = self.win.getmaxyx()

        lines = len(self.list)
        if self.cur_y < lines:
            if self.cur_y + win_size_y - 2 < lines:
                self.pad.move(self.cur_y + win_size_y - 2, self.cur_x)
            else:
                self.pad.move(lines - 1, self.cur_x)

    def cursor_up(self, *args):
        # move cursor up until first entry in list
        if self.cur_y > 0:
            self.pad.move(self.cur_y - 1, self.cur_x)

    def cursor_down(self, *args):
        # move cursor down until end of list
        if self.cur_y < len(self.list) - 1:
            self.pad.move(self.cur_y + 1, self.cur_x)

    def process_input(self, char):
        """
        Process input from user (character)
        """

        self.cur_y, self.cur_x = self.pad.getyx()

        # look for special key mappings in keymap or process as text
        if char in self.config.keymap:
            func = self.keyfunc[self.config.keybinds[self.config.keymap[char]]]
            func()
        elif char == "q":
            self.active = False
            return  # Exit the while loop
        elif char == "\n":
            # create windows, if they do not exists
            if not self.list[self.cur_y].has_windows():
                self.list[self.cur_y].create_windows()
            # activate conversation
            self.list[self.cur_y].activate()
        elif char == "h":
            # create windows, if they do not exists
            if not self.list[self.cur_y].has_windows():
                self.list[self.cur_y].create_windows()
            # activate conversation's history
            self.list[self.cur_y].activate_log()
        # display changes in the pad
        self.redraw_pad()


class LogWin(Win):
    """
    Class for Log Windows
    """

    def redraw_pad(self):
        # screen/pad properties
        max_y, max_x = MAIN_WINS["screen"].getmaxyx()
        pos_y, pos_x = self.config.get_pos(max_y, max_x)
        win_size_y, win_size_x = self.win.getmaxyx()
        pad_size_y, pad_size_x = self.pad.getmaxyx()

        self.pad.clear()
        # if window was resized, resize pad x size according to new window size
        # pad y size will be sorted out in the message loop below
        if pad_size_x != win_size_x - 2:
            pad_size_x = win_size_x - 2
            self.pad.resize(pad_size_y, pad_size_x)

        # dump log messages and resize pad according to new lines added
        lines = 0
        for msg in self.list:
            # define colors for own and buddy's messages
            # TODO: move all color definitions to config part?
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)

            # set colors and attributes for message:
            # * unread messages are bold
            # * read messages are normal
            if not msg.own:
                # message from buddy
                if msg.is_read:
                    # old message
                    self.pad.attroff(curses.A_BOLD)
                    self.pad.attron(curses.color_pair(3) | curses.A_NORMAL)
                else:
                    # new message
                    self.pad.attroff(curses.A_NORMAL)
                    self.pad.attron(curses.color_pair(3) | curses.A_BOLD)
            else:
                # message from you
                if msg.is_read:
                    # old message
                    self.pad.attroff(curses.A_BOLD)
                    self.pad.attron(curses.color_pair(4) | curses.A_NORMAL)
                else:
                    # new message
                    self.pad.attroff(curses.A_NORMAL)
                    self.pad.attron(curses.color_pair(4) | curses.A_BOLD)

            # make sure new line fits into pad
            parts = msg.read().split("\n")
            lines += len(parts)
            for part in parts:
                if len(part) > pad_size_x:
                    lines += math.floor(len(part) / pad_size_x)

            if lines >= pad_size_y:
                self.pad.resize(lines + 1, pad_size_x)
            # output message
            self.pad.addstr(msg.read())

        # check if visible part of pad needs to be moved and display it
        self.cur_y, self.cur_x = self.pad.getyx()
        self.move_pad()
        self.check_borders()
        self.pad.refresh(self.pad_y, self.pad_x,
                         pos_y + 1, pos_x + 1,
                         pos_y + win_size_y - 2,
                         pos_x + win_size_x - 2)

    def cursor_line_start(self, *args):
        # TODO: use other method and keybind with more fitting name?
        # move cursor up one page until first entry in log
        max_y, max_x = MAIN_WINS["screen"].getmaxyx()
        pos_y, pos_x = self.config.get_pos(max_y, max_x)
        win_size_y, win_size_x = self.win.getmaxyx()

        if self.cur_y > 0:
            if self.cur_y - (win_size_y - 2) >= 0:
                self.pad.move(self.cur_y - (win_size_y - 2), self.cur_x)
            else:
                self.pad.move(0, self.cur_x)
            self.move_pad()
            self.check_borders()
            self.pad.refresh(self.pad_y, self.pad_x,
                             pos_y + 1, pos_x + 1,
                             pos_y + win_size_y - 2,
                             pos_x + win_size_x - 2)

    def cursor_line_end(self, *args):
        # TODO: use other method and keybind with more fitting name?
        # move cursor down one page until last entry in log
        max_y, max_x = MAIN_WINS["screen"].getmaxyx()
        pos_y, pos_x = self.config.get_pos(max_y, max_x)
        win_size_y, win_size_x = self.win.getmaxyx()
        unused_pad_size_y, pad_size_x = self.pad.getmaxyx()

        lines = 0
        for msg in self.list:
            parts = msg.read().split("\n")
            lines += len(parts) - 1
            for part in parts:
                if len(part) > pad_size_x:
                    lines += math.floor(len(part) / pad_size_x)
        if self.cur_y < lines:
            if self.cur_y + win_size_y - 2 < lines:
                self.pad.move(self.cur_y + win_size_y - 2, self.cur_x)
            else:
                self.pad.move(lines, self.cur_x)
            self.move_pad()
            self.check_borders()
            self.pad.refresh(self.pad_y, self.pad_x,
                             pos_y + 1, pos_x + 1,
                             pos_y + win_size_y - 2,
                             pos_x + win_size_x - 2)

    def cursor_up(self, *args):
        # move cursor up until first entry in list
        max_y, max_x = MAIN_WINS["screen"].getmaxyx()
        pos_y, pos_x = self.config.get_pos(max_y, max_x)
        win_size_y, win_size_x = self.win.getmaxyx()
        if self.cur_y > 0:
            self.pad.move(self.cur_y - 1, self.cur_x)
            self.cur_y, self.cur_x = self.pad.getyx()
            self.move_pad()
            self.check_borders()
            self.pad.refresh(self.pad_y, self.pad_x,
                             pos_y + 1, pos_x + 1,
                             pos_y + win_size_y - 2,
                             pos_x + win_size_x - 2)

    def cursor_down(self, *args):
        # move cursor down until end of list
        max_y, max_x = MAIN_WINS["screen"].getmaxyx()
        pos_y, pos_x = self.config.get_pos(max_y, max_x)
        win_size_y, win_size_x = self.win.getmaxyx()
        unused_pad_size_y, pad_size_x = self.pad.getmaxyx()
        lines = 0
        for msg in self.list:
            parts = msg.read().split("\n")
            lines += len(parts) - 1
            for part in parts:
                if len(part) > pad_size_x:
                    lines += math.floor(len(part) / pad_size_x)
        if self.cur_y < lines:
            self.pad.move(self.cur_y + 1, self.cur_x)
            self.cur_y, self.cur_x = self.pad.getyx()
            self.move_pad()
            self.check_borders()
            self.pad.refresh(self.pad_y, self.pad_x,
                             pos_y + 1, pos_x + 1,
                             pos_y + win_size_y - 2,
                             pos_x + win_size_x - 2)

    def go_back(self, *args):
        self.active = True
        self.conversation.input_win.active = True

    def process_input(self, char):
        """
        Process user input
        """

        self.cur_y, self.cur_x = self.pad.getyx()

        # look for special key mappings in keymap or process as text
        if char in self.config.keymap:
            func = self.keyfunc[self.config.keybinds[self.config.keymap[char]]]
            func()

        # display changes in the pad
        # self.redraw_pad()


class InputWin(Win):
    """
    Class for Input Windows
    """

    def redraw_pad(self):
        max_y, max_x = MAIN_WINS["screen"].getmaxyx()
        pos_y, pos_x = self.config.get_pos(max_y, max_x)
        win_size_y, win_size_x = self.config.get_size(max_y, max_x)

        self.move_pad()
        self.check_borders()
        self.pad.refresh(self.pad_y, self.pad_x,
                         pos_y + 1, pos_x + 1,
                         pos_y + win_size_y - 2,
                         pos_x + win_size_x - 2)

    def cursor_up(self, *args):
        segment = args[0]
        if self.cur_y > 0:
            self.pad.move(self.cur_y - 1,
                          min(self.cur_x, len(segment[self.cur_y - 1])))

    def cursor_down(self, *args):
        # pad properties
        pad_y_max, unused_pad_x_max = self.pad.getmaxyx()

        segment = args[0]
        if self.cur_y < pad_y_max and self.cur_y < len(segment) - 1:
            self.pad.move(self.cur_y + 1,
                          min(self.cur_x, len(segment[self.cur_y + 1])))

    def cursor_left(self, *args):
        if self.cur_x > 0:
            self.pad.move(self.cur_y, self.cur_x - 1)

    def cursor_right(self, *args):
        # pad properties
        unused_pad_y_max, pad_x_max = self.pad.getmaxyx()

        segment = args[0]
        if self.cur_x < pad_x_max and \
           self.cur_x < len(segment[self.cur_y]):
            self.pad.move(self.cur_y, self.cur_x + 1)

    def cursor_line_start(self, *args):
        if self.cur_x > 0:
            self.pad.move(self.cur_y, 0)

    def cursor_line_end(self, *args):
        # pad properties
        unused_pad_y_max, pad_x_max = self.pad.getmaxyx()

        segment = args[0]
        if self.cur_x < pad_x_max and \
           self.cur_x < len(segment[self.cur_y]):
            self.pad.move(self.cur_y, len(segment[self.cur_y]))

    def cursor_msg_start(self, *args):
        if self.cur_y > 0 or self.cur_x > 0:
            self.pad.move(0, 0)

    def cursor_msg_end(self, *args):
        segment = args[0]
        if self.cur_y < len(segment) - 1 or self.cur_x < len(segment[-1]):
            self.pad.move(len(segment) - 1, len(segment[-1]))

    def send_msg(self, *args):
        # do not send empty messages
        if self.msg == "":
            return

        # let conversation actually send the message
        self.conversation.send_msg(self.msg)

        # reset input
        self.msg = ""
        self.pad.clear()

        # reset pad size
        win_size_y, win_size_x = self.win.getmaxyx()
        self.pad.resize(win_size_y - 2, win_size_x - 2)

    def delete_char(self, *args):
        segment = args[0]
        if self.cur_x > 0:
            # delete charater within a line
            segment[self.cur_y] = segment[self.cur_y][:self.cur_x - 1] +\
                segment[self.cur_y][self.cur_x:]
        elif self.cur_y > 0:
            # delete newline
            old_prev_len = len(segment[self.cur_y - 1])
            segment[self.cur_y - 1] = segment[self.cur_y - 1] +\
                segment[self.cur_y]
            segment = segment[:self.cur_y] + segment[self.cur_y + 1:]
        # reconstruct and display message
        self.msg = "\n".join(segment)
        self.pad.erase()
        self.pad.addstr(self.msg)
        # move cursor to new position
        if self.cur_x > 0:
            self.pad.move(self.cur_y, self.cur_x - 1)
        elif self.cur_y > 0:
            self.pad.move(self.cur_y - 1, old_prev_len)

    def delete_line_end(self, *args):
        segment = args[0]

        # delete from cursor to end of line
        segment[self.cur_y] = segment[self.cur_y][:self.cur_x]

        # reconstruct message
        self.msg = "\n".join(segment)
        self.pad.erase()
        self.pad.addstr(self.msg)

    def delete_line(self, *args):
        segment = args[0]

        # delete the current line
        del segment[self.cur_y]

        # reconstruct message
        self.msg = "\n".join(segment)
        self.pad.erase()
        self.pad.addstr(self.msg)

        # move cursor to new position
        if len(segment) <= self.cur_y:
            self.cur_y = max(0, len(segment) - 1)
        if not segment:
            self.cur_x = 0
        elif len(segment[self.cur_y]) < self.cur_x:
            self.cur_x = len(segment[self.cur_y])
        self.pad.move(self.cur_y, self.cur_x)

    def go_back(self, *args):
        self.active = False
        self.conversation.log_win.active = False

        # assume user read all messages and set lastread to last message
        self.conversation.set_lastread()

    def go_log(self):
        """
        Jump to log
        """

        self.active = False
        self.conversation.log_win.active = True

    def process_input(self, char):
        """
        Process user input (character)
        """

        segments = self.msg.split("\n")
        self.cur_y, self.cur_x = self.pad.getyx()
        pad_size_y, pad_size_x = self.pad.getmaxyx()

        # look for special key mappings in keymap or process as text
        if char in self.config.keymap:
            func = self.keyfunc[self.config.keybinds[self.config.keymap[char]]]
            func(segments)
        elif char == curses.ascii.ctrl("o"):
            self.go_log()
        else:
            # insert new character into segments
            if not isinstance(char, str):
                return
            # make sure new char fits in the pad
            if len(segments) == pad_size_y - 1 and char == "\n":
                pad_size_y += 1
                self.pad.resize(pad_size_y, pad_size_x)
            if len(segments[self.cur_y]) == pad_size_x - 2 and char != "\n":
                pad_size_x += 1
                self.pad.resize(pad_size_y, pad_size_x)

            segments[self.cur_y] = segments[self.cur_y][:self.cur_x] + char +\
                segments[self.cur_y][self.cur_x:]
            # reconstruct orginal message for output in pad
            self.msg = "\n".join(segments)
            # reconstruct segments in case newline character was entered
            segments = self.msg.split("\n")
            # output new message in pad
            self.pad.erase()
            self.pad.addstr(self.msg)
            # move cursor to new position
            if char == "\n":
                self.pad.move(self.cur_y + 1, 0)
            else:
                self.pad.move(self.cur_y, self.cur_x + 1)
        # display changes in the pad
        self.redraw_pad()
