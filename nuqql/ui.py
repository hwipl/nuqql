"""
User Interface part of nuqql
"""

#######################
# USER INTERFACE PART #
#######################

import curses
import curses.ascii
import datetime
import math
import logging
import pathlib

import nuqql.config

# screen and main windows
MAIN_WINS = {}

# list of active conversations
CONVERSATIONS = []


class Conversation:
    """
    Class for conversations
    """

    def __init__(self, backend, account, name, ctype="buddy"):
        self.name = name
        self.backend = backend
        self.account = account
        self.type = ctype
        self.peers = []
        self.log_win = None
        self.input_win = None
        self.list_win = None
        self.notification = 0
        self.logger = None
        self.log_file = None
        if ctype == "buddy":
            self.list_win = MAIN_WINS["list"]
            self.logger, self.log_file = init_logger(backend, account, name)

    def activate(self):
        """
        Activate windows of conversation
        """

        # check log_win to determine, if windows are already created
        if self.log_win is not None:
            self.input_win.active = True
            self.input_win.redraw()
            self.log_win.active = False
            self.log_win.redraw()
            self.clear_notifications()
            return

    def has_windows(self):
        """
        Check if conversation has already created its windows
        """

        if self.log_win:
            return True

        return False

    def create_windows(self):
        """
        Create windows for this conversation
        """

        # create windows
        if self.type == "buddy":
            # standard chat windows
            log_title = "Chat log with {0}".format(self.name)
            input_title = "Message to {0}".format(self.name)
        else:
            # type: "nuqql" or "backend"
            # command windows for nuqql and backends
            log_title = "Command log of {0}".format(self.name)
            input_title = "Command to {0}".format(self.name)

        log_config = nuqql.config.get("log_win")
        self.log_win = LogWin(log_config, self, log_title)
        input_config = nuqql.config.get("input_win")
        self.input_win = InputWin(input_config, self, input_title)

        if self.type == "nuqql":
            # nuqql itself needs a list window for buddy list
            list_config = nuqql.config.get("list_win")
            self.list_win = ListWin(list_config, self, "Conversation list")
            # set list to conversations
            self.list_win.list = CONVERSATIONS
            # mark nuqql's list window as active, so main loop does not quit
            self.list_win.active = True

        if self.type == "buddy":
            # try to read old messages from message history
            init_log_from_file(self)

    def get_name(self):
        """
        Get the name of the conversation, depending on type
        """

        # check if there are pending notifications
        if self.notification > 0:
            notify = "# "
        else:
            notify = ""

        # is it a buddy?
        if self.type == "buddy":
            peer = self.peers[0]
            return "{0}[{1}] {2}".format(notify, peer.status, peer.alias)

        # is it a backend?
        if self.type == "backend":
            return "{0}{{backend}} {1}".format(notify, self.name)

        # is it nuqql itself?
        if self.type == "nuqql":
            return "{0}{{nuqql}}".format(notify)

        # this should not be reached
        return "<unknown>"

    def log(self, sender, msg, tstamp=None):
        """
        Log message to conversation's log window
        """

        if tstamp is None:
            tstamp = datetime.datetime.now()
        log_msg = LogMessage(tstamp, sender, msg)
        # if window does not exist, create it. TODO: log to conv?
        if not self.log_win:
            self.create_windows()
        self.log_win.add(log_msg)

    def notify(self):
        """
        Notify this conversation about new messages
        """

        self.notification = 1
        if self.list_win:
            self.list_win.redraw_pad()

    def clear_notifications(self):
        """
        Clear notifications of buddy
        """

        self.notification = 0
        if self.list_win:
            self.list_win.redraw_pad()

    def __lt__(self, other):
        # sort based on get_key output
        return self.get_key() < other.get_key()

    # status to sorting key mapping
    status_key = {
        "on": 0,
        "afk": 1,
        "off": 2,
    }

    def get_key(self):
        """
        Get a key for sorting this conversation
        """

        # defaults
        sort_notify = 0 - self.notification
        sort_type = 0
        sort_status = 0
        sort_name = self.name

        # is it a buddy?
        if self.type == "buddy":
            peer = self.peers[0]
            try:
                sort_status = self.status_key[peer.status]
            except KeyError:
                sort_status = len(self.status_key) + 1
            sort_name = peer.alias

        # is it a backend?
        if self.type == "backend":
            sort_type = 1

        # is it nuqql itself?
        if self.type == "nuqql":
            sort_type = 2

        # return tuple of sort keys
        return sort_notify, sort_type, sort_status, sort_name

    def is_active(self):
        """
        Check if this conversation is currently active, and return True if it
        is the case; otherwise, return False.
        """

        # check if input win is active
        if self.input_win and self.input_win.active:
            return True

        # check if log win is active
        if self.log_win and self.log_win.active:
            return True

        return False

    def process_input(self, char):
        """
        Process user input in active window
        """

        # try to give control to the input win first...
        if self.input_win and self.input_win.active:
            self.input_win.process_input(char)
            return

        # then, try to give control to the log win
        if self.log_win and self.log_win.active:
            self.log_win.process_input(char)
            return


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
            for conv in CONVERSATIONS:
                if conv.is_active():
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

        # move cursor back to original position
        self.pad.move(self.cur_y, self.cur_x)

        # check if visible part of pad needs to be moved and display it
        self.move_pad()
        self.check_borders()
        self.pad.refresh(self.pad_y, self.pad_x,
                         pos_y + 1, pos_x + 1,
                         pos_y + win_size_y - 2,
                         pos_x + win_size_x - 2)

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
            lines += len(parts) - 1
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
            if self.cur_y - win_size_y >= 0:
                self.pad.move(self.cur_y - win_size_y, self.cur_x)
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
            if self.cur_y + win_size_y < lines:
                self.pad.move(self.cur_y + win_size_y, self.cur_x)
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

        # TODO: unify the logging in a method of Conversation?
        # log message
        tstamp = datetime.datetime.now()
        # log_msg = LogMessage(now, self.conversation.account.name, self.msg,
        # TODO: add conversation -> own name function? just use "You"?
        log_msg = LogMessage(tstamp, self.conversation.name, self.msg,
                             own=True)
        self.conversation.log_win.add(log_msg)

        # depending on conversation type send a message or a command
        if self.conversation.type == "buddy":
            # send message
            self.conversation.backend.client.send_msg(
                self.conversation.account.aid, self.conversation.name,
                self.msg)
            tstamp = round(tstamp.timestamp())
            msg = "{} {} {} {}\r".format(tstamp, "OUT", "you", self.msg)
            self.conversation.logger.info(msg)
            set_lastread(self.conversation.backend, self.conversation.account,
                         self.conversation.name, tstamp,
                         "OUT", "you", self.msg)
        else:
            # send command message
            if self.conversation.backend is not None:
                self.conversation.backend.client.send_command(self.msg)

        # reset input
        self.msg = ""
        self.pad.clear()

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

    def go_back(self, *args):
        self.active = False
        self.conversation.log_win.active = False

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
                return
            if len(segments[self.cur_y]) == pad_size_x - 2 and char != "\n":
                return

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


##################
# Helper Classes #
##################

class LogMessage:
    """Class for log messages to be displayed in LogWins"""

    def __init__(self, tstamp, sender, msg, own=False):
        """
        Initialize log message with timestamp, sender of the message, and
        the message itself
        """

        # timestamp
        self.tstamp = tstamp

        # sender could be us or buddy/other user, as
        # indicated by self.own (helps with coloring etc. later)
        self.sender = sender
        self.own = own

        # the message itself
        self.msg = msg

        # has message been read?
        self.is_read = False

    def get_short_sender(self):
        """
        Convert name to a shorter version
        """

        # TODO: improve? Save short name in account and buddy instead?
        return self.sender.split("@")[0]

    def read(self):
        """
        Format and return log message; mark it as read
        """

        # format message
        msg = "{0} {1}: {2}\n".format(self.tstamp.strftime("%H:%M:%S"),
                                      self.get_short_sender(),
                                      self.msg)

        # message has now been read
        self.is_read = True

        return msg

    def is_equal(self, other):
        """
        Check if this message and the LogMessage "other" match
        """

        if self.tstamp != other.tstamp:
            return False
        if self.sender != other.sender:
            return False
        if self.msg != other.msg:
            return False

        return True


####################
# HELPER FUNCTIONS #
####################

def get_logger(name, file_name):
    """
    Create a logger for a conversation
    """

    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # create handler
    fileh = logging.FileHandler(file_name)
    fileh.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter(
        # fmt="%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s",
        fmt="%(message)s",
        datefmt="%s")

    # add formatter to handler
    fileh.setFormatter(formatter)

    # add handler to logger
    logger.addHandler(fileh)

    # return logger to caller
    return logger


def init_logger(backend, account, conv_name):
    """
    Init logger for a conversation
    """

    # make sure log directory exists
    log_dir = str(pathlib.Path.home()) + \
        "/.config/nuqql/conversation/{}/{}/{}".format(backend.name,
                                                      account.aid,
                                                      conv_name)
    pathlib.Path(log_dir).mkdir(parents=True, exist_ok=True)

    # create logger with log name and log file
    log_name = "{} {} {}".format(backend.name, account.aid, conv_name)
    log_file = log_dir + "/history"
    logger = get_logger(log_name, log_file)

    # return the ready logger and the log file to caller
    return logger, log_file


def get_lastread(backend, account, conv_name):
    """
    Get last read message from "lastread" file of the conversation
    """

    # make sure log directory exists
    lastread_dir = str(pathlib.Path.home()) + \
        "/.config/nuqql/conversation/{}/{}/{}".format(backend.name,
                                                      account.aid,
                                                      conv_name)
    pathlib.Path(lastread_dir).mkdir(parents=True, exist_ok=True)
    lastread_file = lastread_dir + "/lastread"

    try:
        with open(lastread_file, newline="\r\n") as in_file:
            lines = in_file.readlines()
            for line in lines:
                parts = line.split(sep=" ", maxsplit=3)
                tstamp = parts[0]
                direction = parts[1]
                is_own = False
                if direction == "OUT":
                    is_own = True
                sender = parts[2]
                msg = parts[3][:-2]
                tstamp = datetime.datetime.fromtimestamp(int(tstamp))
                log_msg = LogMessage(tstamp, sender, msg, own=is_own)
                log_msg.is_read = True
                return log_msg
    except FileNotFoundError:
        return None


def set_lastread(backend, account, conv_name, tstamp, direction, sender, msg):
    """
    Set last read message in "lastread" file of the conversation
    """

    # make sure log directory exists
    lastread_dir = str(pathlib.Path.home()) + \
        "/.config/nuqql/conversation/{}/{}/{}".format(backend.name,
                                                      account.aid,
                                                      conv_name)
    pathlib.Path(lastread_dir).mkdir(parents=True, exist_ok=True)
    lastread_file = lastread_dir + "/lastread"

    line = "{} {} {} {}\r\n".format(tstamp, direction, sender, msg)
    lines = []
    lines.append(line)
    with open(lastread_file, "w+") as in_file:
        lines = in_file.writelines(lines)


def init_log_from_file(conv):
    """
    Initialize a conversation's log from the conversation's log file
    """

    # get last read log message
    last_read = get_lastread(conv.backend, conv.account, conv.name)
    is_read = True

    lines = []
    with open(conv.log_file, newline="\r\n") as in_file:
        lines = in_file.readlines()
        for line in lines:
            # parse log message
            parts = line.split(sep=" ", maxsplit=3)
            tstamp = parts[0]
            direction = parts[1]
            is_own = False
            if direction == "OUT":
                is_own = True
            sender = parts[2]
            msg = parts[3][:-2]
            tstamp = datetime.datetime.fromtimestamp(int(tstamp))

            # add log message to the conversation's log
            log_msg = LogMessage(tstamp, sender, msg, own=is_own)
            log_msg.is_read = is_read
            conv.log_win.add(log_msg)

            # if this is the last read message, following message will be
            # marked as unread
            if last_read and last_read.is_equal(log_msg):
                is_read = False
    if lines:
        # if there were any log messages in the log file, put a marker in the
        # log where the new messages start
        tstamp = datetime.datetime.now()
        log_msg = LogMessage(tstamp, "<event>", "<Started new conversation.>",
                             own=True)
        log_msg.is_read = True
        conv.log_win.add(log_msg)


def log_main_window(msg):
    """
    Log message to main windows
    """

    now = datetime.datetime.now()
    log_msg = LogMessage(now, "nuqql", msg)
    MAIN_WINS["log"].add(log_msg)


def get_absolute_size(y_max, x_max, y_rel, x_rel):
    """
    Get absolute size for given relative size
    """

    y_abs = int(y_max * y_rel)
    x_abs = int(x_max * x_rel)
    return y_abs, x_abs


def resize_main_window():
    """
    Resize main window
    """

    # get main win
    screen = MAIN_WINS["screen"]

    # get new maxima
    max_y, max_x = screen.getmaxyx()

    # redraw main windows
    screen.clear()
    screen.refresh()

    # redraw conversation windows
    for conv in CONVERSATIONS:
        # resize and move conversation windows
        if conv.list_win:
            size_y, size_x = conv.list_win.config.get_size(max_y, max_x)
            conv.list_win.resize_win(size_y, size_x)
        if conv.log_win:
            size_y, size_x = conv.log_win.config.get_size(max_y, max_x)
            conv.log_win.resize_win(size_y, size_x)
            pos_y, pos_x = conv.log_win.config.get_pos(max_y, max_x)
            conv.log_win.move_win(pos_y, pos_x)
        if conv.input_win:
            size_y, size_x = conv.input_win.config.get_size(max_y, max_x)
            conv.input_win.resize_win(size_y, size_x)
            pos_y, pos_x = conv.input_win.config.get_pos(max_y, max_x)
            conv.input_win.move_win(pos_y, pos_x)
        # redraw active conversation windows
        if conv.list_win and conv.list_win.active:
            conv.list_win.redraw()
        if conv.log_win and conv.log_win.active:
            conv.log_win.redraw()
        if conv.input_win and conv.input_win.active:
            conv.input_win.redraw()


def create_main_windows():
    """
    Create main UI windows
    """

    # main screen
    # dummy conversation for main windows, creates log_win and input_win
    nuqql_conv = Conversation(None, None, "nuqql", ctype="nuqql")
    nuqql_conv.create_windows()
    CONVERSATIONS.append(nuqql_conv)

    # draw list
    nuqql_conv.list_win.redraw()
    nuqql_conv.log_win.redraw()
    nuqql_conv.input_win.redraw()

    # save windows
    MAIN_WINS["list"] = nuqql_conv.list_win
    MAIN_WINS["log"] = nuqql_conv.log_win
    MAIN_WINS["input"] = nuqql_conv.input_win


def handle_message(backend, acc_id, tstamp, sender, msg):
    """
    Handle message from backend
    """

    # look for an existing conversation and use it
    for conv in CONVERSATIONS:
        if conv.backend is backend and \
           conv.account and conv.account.aid == acc_id and \
           conv.name == sender:
            # log message
            conv.logger.info("{} {} {} {}\r".format(tstamp, "IN", sender,
                                                    msg))
            if conv.is_active():
                set_lastread(conv.backend, conv.account, conv.name, tstamp,
                             "IN", sender, msg)

            tstamp = datetime.datetime.fromtimestamp(tstamp)
            conv.log(conv.name, msg, tstamp=tstamp)
            # if window is not already active notify user
            if not conv.is_active():
                conv.notify()
            return

    # nothing found, log to main window
    backend.conversation.log(sender, msg, tstamp=tstamp)


def update_buddy(buddy):
    """
    Update buddy in UI
    """

    # look for existing buddy
    for conv in CONVERSATIONS:
        if conv.type != "buddy":
            continue

        conv_buddy = conv.peers[0]
        if conv_buddy is buddy:
            conv.list_win.redraw()


def add_buddy(buddy):
    """
    Add a new buddy to UI
    """

    # add a new conversation for the new buddy
    conv = Conversation(buddy.backend, buddy.account, buddy.name)
    conv.peers.append(buddy)
    conv.list_win.add(conv)
    conv.list_win.redraw()


def read_input():
    """
    Read user input and return it to caller
    """

    # try to get input from user (timeout set in init())
    try:
        wch = MAIN_WINS["screen"].get_wch()
    except curses.error:
        # no user input...
        wch = None

    return wch


def handle_input():
    """
    Read and handle user input
    """

    # wait for user input and get timeout or character to process
    char = read_input()

    # handle user input
    if char is None:
        # NO INPUT, keep waiting for input..
        return True

    # if terminal resized, resize and redraw active windows
    if char == curses.KEY_RESIZE:
        resize_main_window()
        return True

    # pass user input to active conversation
    for conv in CONVERSATIONS:
        if conv.is_active():
            conv.process_input(char)
            return True

    # if no conversation is active pass input to active list window
    if MAIN_WINS["list"].active:
        # list window navigation
        MAIN_WINS["input"].redraw()
        MAIN_WINS["log"].redraw()
        MAIN_WINS["list"].process_input(char)
        return True

    # list window is also inactive -> user quit
    return False


def start(stdscr, func):
    """
    Start UI and run provided function
    """

    # save stdscr
    MAIN_WINS["screen"] = stdscr

    # configuration
    stdscr.timeout(10)

    # clear everything
    stdscr.clear()
    stdscr.refresh()

    # make sure window config is loaded
    nuqql.config.init_win()

    # create main windows
    create_main_windows()

    # run function provided by caller
    func()


def init(func):
    """
    Initialize UI
    """

    curses.wrapper(start, func)
