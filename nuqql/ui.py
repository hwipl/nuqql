"""
User Interface part of nuqql
"""

#######################
# USER INTERFACE PART #
#######################

import curses
import curses.ascii
import datetime

# screen and main windows
STDSCR = None
LIST_WIN = None
LOG_WIN = None
INPUT_WIN = None
MAX_Y = 0
MAX_X = 0


# list of active conversations
CONVERSATIONS = []

# default keymap for special keys
DEFAULT_KEYMAP = {
    chr(curses.ascii.ESC):  "KEY_ESC",
    curses.KEY_RIGHT:       "KEY_RIGHT",
    curses.KEY_LEFT:        "KEY_LEFT",
    curses.KEY_DOWN:        "KEY_DOWN",
    curses.KEY_UP:          "KEY_UP",
    curses.ascii.ctrl("x"): "KEY_CTRL_X",
    chr(curses.ascii.DEL):  "KEY_DEL",
    curses.KEY_DC:          "KEY_DEL",
    curses.KEY_HOME:        "KEY_HOME",
    curses.KEY_END:         "KEY_END",
    curses.KEY_PPAGE:       "KEY_PAGE_UP",
    curses.KEY_NPAGE:       "KEY_PAGE_DOWN",
}

# default key bindings for input windows
DEFAULT_INPUT_WIN_KEYBINDS = {
    "KEY_ESC":          "GO_BACK",
    "KEY_RIGHT":        "CURSOR_RIGHT",
    "KEY_LEFT":         "CURSOR_LEFT",
    "KEY_DOWN":         "CURSOR_DOWN",
    "KEY_UP":           "CURSOR_UP",
    "KEY_CTRL_X":       "SEND_MSG",
    "KEY_DEL":          "DEL_CHAR",
    "KEY_HOME":         "CURSOR_MSG_START",
    "KEY_END":          "CURSOR_MSG_END",
    "KEY_PAGE_UP":      "CURSOR_LINE_START",
    "KEY_PAGE_DOWN":    "CURSOR_LINE_END",
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
        self.list_win = None
        self.log_win = None
        self.input_win = None
        self.notification = 0

    def activate(self):
        """
        Activate windows of conversation
        """

        # check log_win to determine, if windows are already created
        if self.log_win is not None:
            self.input_win.active = True
            self.input_win.redraw()
            self.log_win.active = True
            self.log_win.redraw()
            self.clear_notifications()
            return

        # determine window sizes
        max_y, max_x = STDSCR.getmaxyx()
        list_win_y, list_win_x = get_absolute_size(max_y, max_x,
                                                   LIST_WIN_Y_PER,
                                                   LIST_WIN_X_PER)
        log_win_y, log_win_x = get_absolute_size(max_y, max_x,
                                                 LOG_WIN_Y_PER,
                                                 LOG_WIN_X_PER)
        input_win_y, input_win_x = get_absolute_size(max_y, max_x,
                                                     INPUT_WIN_Y_PER,
                                                     INPUT_WIN_X_PER)

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

        self.log_win = LogWin(self, 0, list_win_x, log_win_y, log_win_x,
                              log_win_y - 2, log_win_x - 2, log_title)
        self.input_win = InputWin(self, max_y - input_win_y, list_win_x,
                                  input_win_y, input_win_x, 2000, 2000,
                                  input_title)

        if self.type == "backend":
            # do not start as active
            self.input_win.active = False

        if self.type == "nuqql":
            # nuqql itself needs a list window for buddy list
            self.list_win = ListWin(self, 0, 0, list_win_y, list_win_x,
                                    list_win_y - 2, 128, "Buddy List")
            # set list to conversations
            self.list_win.list = CONVERSATIONS
            # do not start as active
            self.input_win.active = False

        # draw windows
        self.log_win.redraw()
        self.input_win.redraw()

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
            tstamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = LogMessage(tstamp, sender, msg)
        # if window does not exist, activate it. TODO: log to conv?
        if not self.log_win:
            self.activate()
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
        # sort based on get_name output
        return self.get_name() < other.get_name()


class Win:
    """
    Base class for Windows
    """

    def __init__(self, conversation, pos_y, pos_x, win_y_max, win_x_max,
                 pad_y_max, pad_x_max, title):
        # is window active?
        self.active = True
        self.pos_y = pos_y
        self.pos_x = pos_x

        # new window
        self.win_y_max = win_y_max
        self.win_x_max = win_x_max
        self.win = curses.newwin(self.win_y_max, self.win_x_max,
                                 self.pos_y, self.pos_x)

        # new pad
        self.pad_x_max = pad_x_max
        self.pad_y_max = pad_y_max
        self.pad_y = 0
        self.pad_x = 0
        self.pad = curses.newpad(self.pad_y_max, self.pad_x_max)

        # cursor positions
        self.cur_y = 0
        self.cur_x = 0

        # input message
        self.msg = ""

        # list entries/message log
        self.list = []

        # keymaps/bindings
        self.keymap = DEFAULT_KEYMAP
        self.keybind = {}
        self.init_keybinds()
        self.keyfunc = {}
        self.init_keyfunc()

        # conversation
        self.conversation = conversation

        # window title
        # TODO: use name instead?
        self.title = " " + title + " "

    def redraw_win(self):
        """
        Redraw entire window
        """

        self.win.clear()

        # color settings on
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        self.win.attron(curses.color_pair(1) | curses.A_BOLD)

        # window border
        self.win.border()

        # window title
        max_title_len = min(len(self.title), self.win_x_max - 3)
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

        if self.cur_x >= self.win_x_max - 2:
            self.pad_x = self.cur_x - (self.win_x_max - 2)
        if self.cur_x < self.pad_x:
            self.pad_x = self.pad_x - self.cur_x
        if self.cur_y >= self.win_y_max - 2:
            self.pad_y = self.cur_y - (self.win_y_max - 2)
        if self.cur_y < self.pad_y:
            self.pad_y = self.pad_y - self.cur_y

    def check_borders(self):
        """
        Check borders
        """

        if self.pad_x < 0:
            self.pad_x = 0
        if self.pad_x > self.pad_x_max - self.win_x_max:
            self.pad_x = self.pad_x_max - self.win_x_max
        if self.pad_y < 0:
            self.pad_y = 0
        if self.pad_y > self.pad_y_max - self.win_y_max:
            self.pad_y = self.pad_y_max - self.win_y_max

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

        self.list.append(entry)
        if self.active:
            self.redraw()

    def resize_win(self, win_y_max, win_x_max):
        """
        Resize window
        """

        self.win_y_max = win_y_max
        self.win_x_max = win_x_max
        self.win.resize(self.win_y_max, self.win_x_max)

    def move_win(self, pos_y, pos_x):
        """
        Move window
        """

        self.pos_y = pos_y
        self.pos_x = pos_x
        self.win.mvwin(self.pos_y, self.pos_x)

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

    def init_keybinds(self):
        """
        Initialize key bindings
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

        self.cur_y, self.cur_x = self.pad.getyx()
        self.pad.clear()
        # set colors
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        self.pad.attron(curses.color_pair(2))
        # sort list
        self.list.sort()
        # dump log messages and resize pad according to new lines added
        self.pad_y_max = self.win_y_max - 2     # reset minimum size of pad
        # for buddy in self.list[-(self.pad_y_max-1):]:
        # for buddy in self.list[:self.pad_y_max-1]:
        for index, conv in enumerate(self.list):
            name = conv.get_name() + "\n"
            if index == self.cur_y:
                # pointer is on conversation, highlight it in list
                self.pad.addstr(name, curses.A_REVERSE)
            else:
                # just show the conversation in list
                self.pad.addstr(name)

            # resize pad for more buddies
            self.pad_y_max += 1
            self.pad.resize(self.pad_y_max, self.pad_x_max)
        # reset colors
        self.pad.attroff(curses.color_pair(2))

        # move cursor back to original position
        self.pad.move(self.cur_y, self.cur_x)
        # check if visible part of pad needs to be moved and display it
        self.move_pad()
        self.check_borders()
        self.pad.refresh(self.pad_y, self.pad_x,
                         self.pos_y + 1, self.pos_x + 1,
                         self.pos_y + self.win_y_max - 2,
                         self.pos_x + self.win_x_max - 2)

    def move_pad(self):
        """
        Move pad
        """

        # TODO: re-check all that moving stuff
        self.cur_y, self.cur_x = self.pad.getyx()
        if self.cur_x >= self.win_x_max - 2:
            # TODO: change -3 to -2 somehow? then use super class function
            self.pad_x = self.cur_x - (self.win_x_max - 3)
        if self.cur_x < self.pad_x:
            self.pad_x = self.cur_x
        # TODO: change -3 to -2 somehow? then use super class function
        if self.cur_y >= self.win_y_max - 3:
            # TODO: change -3 to -2 somehow? then use super class function
            self.pad_y = self.cur_y - (self.win_y_max - 3)
        elif self.cur_y < self.pad_y:
            self.pad_y = self.cur_y

    def highlight(self, coord_y, val):
        """
        Highlight entry in internal list
        """

        buddy = self.list[coord_y]
        buddy.hilight = val

    def cursor_up(self, *args):
        if self.cur_y > 0:
            self.pad.move(self.cur_y - 1, self.cur_x)
            self.highlight(self.cur_y, False)
            self.highlight(self.cur_y - 1, True)

    def cursor_down(self, *args):
        if self.cur_y < self.pad_y_max and self.cur_y < len(self.list) - 1:
            self.pad.move(self.cur_y + 1, self.cur_x)
            self.highlight(self.cur_y, False)
            self.highlight(self.cur_y + 1, True)

    def init_keybinds(self):
        self.keybind = DEFAULT_LIST_WIN_KEYBINDS

    def process_input(self, char):
        """
        Process input from user (character)
        """

        self.cur_y, self.cur_x = self.pad.getyx()

        # look for special key mappings in keymap or process as text
        if char in self.keymap:
            func = self.keyfunc[self.keybind[self.keymap[char]]]
            func()
        elif char == "q":
            self.active = False
            return  # Exit the while loop
        elif char == "\n":
            # activate conversation
            self.list[self.cur_y].activate()
        # display changes in the pad
        self.redraw_pad()


class LogWin(Win):
    """
    Class for Log Windows
    """

    def redraw_pad(self):
        self.pad.clear()
        # if window was resized, resize pad x size according to new window size
        # TODO: do the same thing for y size and ensure a minimal pad y size?
        if self.pad_x_max != self.win_x_max - 2:
            self.pad_x_max = self.win_x_max - 2
            self.pad.resize(self.pad_y_max, self.pad_x_max)

        # dump log messages and resize pad according to new lines added
        for msg in self.list[-(self.pad_y_max-1):]:
            # current pad dimensions for resize later
            old_y, old_x = self.pad.getyx()

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

            # output message
            self.pad.addstr(msg.tstamp + " ")
            self.pad.addstr(get_short_name(msg.sender) + ": ")
            self.pad.addstr(msg.msg + "\n")

            # message has now been read
            msg.is_read = True

            # resize pad
            new_y, new_x = self.pad.getyx()
            self.pad_y_max += new_y - old_y
            self.pad.resize(self.pad_y_max, self.pad_x_max)

        # check if visible part of pad needs to be moved and display it
        self.cur_y, self.cur_x = self.pad.getyx()
        self.move_pad()
        self.check_borders()
        self.pad.refresh(self.pad_y, self.pad_x,
                         self.pos_y + 1, self.pos_x + 1,
                         self.pos_y + self.win_y_max - 2,
                         self.pos_x + self.win_x_max - 2)


class InputWin(Win):
    """
    Class for Input Windows
    """

    def redraw_pad(self):
        self.move_pad()
        self.check_borders()
        self.pad.refresh(self.pad_y, self.pad_x,
                         self.pos_y + 1, self.pos_x + 1,
                         self.pos_y + self.win_y_max - 2,
                         self.pos_x + self.win_x_max - 2)

    def move_pad(self):
        self.cur_y, self.cur_x = self.pad.getyx()
        if self.cur_x >= self.win_x_max - 2:
            # TODO: change -3 to -2 somehow? then use super class function
            self.pad_x = self.cur_x - (self.win_x_max - 3)
        if self.cur_x < self.pad_x:
            self.pad_x = self.cur_x
        if self.cur_y >= self.win_y_max - 2:
            # TODO: change -3 to -2 somehow? then use super class function
            self.pad_y = self.cur_y - (self.win_y_max - 3)
        if self.cur_y < self.pad_y:
            self.pad_y = self.cur_y

    def cursor_up(self, *args):
        segment = args[0]
        if self.cur_y > 0:
            self.pad.move(self.cur_y - 1,
                          min(self.cur_x, len(segment[self.cur_y - 1])))

    def cursor_down(self, *args):
        segment = args[0]
        if self.cur_y < self.pad_y_max and self.cur_y < len(segment) - 1:
            self.pad.move(self.cur_y + 1,
                          min(self.cur_x, len(segment[self.cur_y + 1])))

    def cursor_left(self, *args):
        if self.cur_x > 0:
            self.pad.move(self.cur_y, self.cur_x - 1)

    def cursor_right(self, *args):
        segment = args[0]
        if self.cur_x < self.pad_x_max and \
           self.cur_x < len(segment[self.cur_y]):
            self.pad.move(self.cur_y, self.cur_x + 1)

    def cursor_line_start(self, *args):
        if self.cur_x > 0:
            self.pad.move(self.cur_y, 0)

    def cursor_line_end(self, *args):
        segment = args[0]
        if self.cur_x < self.pad_x_max and \
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

        # log message
        now = datetime.datetime.now().strftime("%H:%M:%S")
        # log_msg = LogMessage(now, self.conversation.account.name, self.msg,
        # TODO: add conversation -> own name function? just use "You"?
        log_msg = LogMessage(now, self.conversation.name, self.msg,
                             own=True)
        self.conversation.log_win.add(log_msg)

        # depending on conversation type send a message or a command
        if self.conversation.type == "buddy":
            # send message
            self.conversation.backend.client.send_msg(
                self.conversation.account.aid, self.conversation.name,
                self.msg)
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

    def init_keybinds(self):
        self.keybind = DEFAULT_INPUT_WIN_KEYBINDS

    def process_input(self, char):
        """
        Process user input (character)
        """

        segment = self.msg.split("\n")
        self.cur_y, self.cur_x = self.pad.getyx()

        # look for special key mappings in keymap or process as text
        if char in self.keymap:
            func = self.keyfunc[self.keybind[self.keymap[char]]]
            func(segment)
        else:
            # insert new character into segments
            if not isinstance(char, str):
                return
            segment[self.cur_y] = segment[self.cur_y][:self.cur_x] + char +\
                segment[self.cur_y][self.cur_x:]
            # reconstruct orginal message for output in pad
            self.msg = "\n".join(segment)
            # reconstruct segments in case newline character was entered
            segment = self.msg.split("\n")
            # output new message in pad
            self.pad.erase()
            self.pad.addstr(self.msg)
            # move cursor to new position
            if char == "\n":
                self.pad.move(self.cur_y + 1,
                              min(self.cur_x, len(segment[self.cur_y + 1])))
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


####################
# HELPER FUNCTIONS #
####################

def log_main_window(msg):
    """
    Log message to main windows
    """

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = LogMessage(now, "nuqql", msg)
    LOG_WIN.add(log_msg)


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

    global MAX_Y, MAX_X

    max_y_new, max_x_new = STDSCR.getmaxyx()
    if max_y_new == MAX_Y and max_x_new == MAX_X:
        # nothing has changed
        return MAX_Y, MAX_X

    # window has been resized
    # save new maxima
    MAX_Y = max_y_new
    MAX_X = max_x_new
    list_win_y, list_win_x = get_absolute_size(MAX_Y, MAX_X,
                                               LIST_WIN_Y_PER, LIST_WIN_X_PER)
    log_win_y, log_win_x = get_absolute_size(MAX_Y, MAX_X,
                                             LOG_WIN_Y_PER, LOG_WIN_X_PER)
    input_win_y, input_win_x = get_absolute_size(MAX_Y, MAX_X,
                                                 INPUT_WIN_Y_PER,
                                                 INPUT_WIN_X_PER)

    # resize and move main windows
    LIST_WIN.resize_win(list_win_y, list_win_x)
    LOG_WIN.resize_win(log_win_y, log_win_x)
    LOG_WIN.move_win(0, list_win_x)
    INPUT_WIN.resize_win(input_win_y, input_win_x)
    INPUT_WIN.move_win(MAX_Y - input_win_y, list_win_x)

    # redraw main windows
    STDSCR.clear()
    STDSCR.refresh()
    LIST_WIN.redraw()
    LOG_WIN.redraw()
    INPUT_WIN.redraw()

    # redraw conversation windows
    for conv in CONVERSATIONS:
        # resize and move conversation windows
        conv.log_win.resize_win(log_win_y, log_win_x)
        conv.log_win.move_win(0, list_win_x)
        conv.input_win.resize_win(input_win_y, input_win_x)
        conv.input_win.move_win(MAX_Y - input_win_y, list_win_x)
        # redraw active conversation windows
        if conv.input_win.active:
            conv.input_win.redraw()
        if conv.log_win.active:
            conv.log_win.redraw()

    return MAX_Y, MAX_X


def get_short_name(name):
    """
    Convert name to a shorter version
    """

    # TODO: move that somewhere? Improve it?
    # Save short name in account and buddy instead?
    return name.split("@")[0]


def create_main_windows():
    """
    Create main UI windows
    """

    global LIST_WIN, LOG_WIN, INPUT_WIN

    # main screen
    # dummy conversation for main windows, creates log_win and input_win
    nuqql_conv = Conversation(None, None, "nuqql", ctype="nuqql")
    nuqql_conv.activate()
    CONVERSATIONS.append(nuqql_conv)

    # draw list
    nuqql_conv.list_win.redraw()

    # save windows
    LIST_WIN = nuqql_conv.list_win
    LOG_WIN = nuqql_conv.log_win
    INPUT_WIN = nuqql_conv.input_win


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
            conv.log(conv.name, msg, tstamp=tstamp)
            # if window is not already active notify user
            if not conv.input_win.active:
                conv.notify()
            return

    # TODO: clean up? handle messages from unknown peer?
    # for buddy in LIST_WIN.list:
    #     if buddy.backend is backend and \
    #        buddy.account.aid == acc_id and \
    #        buddy.name == sender:
    #         # new conversation
    #         # conv = Conversation(buddy.backend, buddy.account, buddy.name)
    #         conv = Conversation(buddy.name)
    #         conv.peers.append(buddy)
    #         conv.activate()
    #         conv.input_win.active = False
    #         conv.log_win.active = False
    #         CONVERSATIONS.append(conv)
    #         # log message
    #         conv.log(conv.name, msg, tstamp=tstamp)
    #         # notify user
    #         LIST_WIN.notify(backend, acc_id, sender)
    #         return

    # nothing found, log to main window
    backend.conversation.log(sender, msg, tstamp=tstamp)


def update_buddy(backend, acc_id, name, alias, status):
    """
    Update buddy in UI
    """

    # look for existing buddy
    for conv in LIST_WIN.list:
        if conv.type != "buddy":
            continue

        buddy = conv.peers[0]
        if buddy.backend is backend and \
           buddy.account.aid == acc_id and \
           buddy.name == name:
            old_status = buddy.status
            old_alias = buddy.alias
            buddy.status = status
            buddy.alias = alias
            if old_status != status or old_alias != alias:
                LIST_WIN.redraw()
            return True

    return False


def add_buddy(buddy):
    """
    Add a new buddy to UI
    """

    # add a new conversation for the new buddy
    conv = Conversation(buddy.backend, buddy.account, buddy.name)
    conv.peers.append(buddy)
    LIST_WIN.add(conv)
    LIST_WIN.redraw()


def read_input():
    """
    Read user input and return it to caller
    """

    # try to get input from user (timeout set in init())
    try:
        wch = STDSCR.get_wch()
    except curses.error:
        # no user input...
        wch = None

    return wch


def handle_input():
    """
    Read and handle user input
    """

    # check size and redraw windows if necessary
    resize_main_window()

    # wait for user input and get timeout or character to process
    char = read_input()

    # handle user input
    if char is None:
        # NO INPUT, keep waiting for input..
        return True

    # pass user input to active conversation
    for conv in CONVERSATIONS:
        if conv.input_win and conv.input_win.active:
            conv.input_win.process_input(char)
            return True

    # if no conversation is active pass input to command or list window
    if LIST_WIN.active:
        # list window navigation
        INPUT_WIN.redraw()
        LOG_WIN.redraw()
        LIST_WIN.process_input(char)
        return True

    # list window is also inactive -> user quit
    return False


def start(stdscr, func):
    """
    Start UI and run provided function
    """

    global STDSCR, MAX_Y, MAX_X

    # save stdscr
    STDSCR = stdscr

    # configuration
    max_y, max_x = stdscr.getmaxyx()
    MAX_Y = max_y
    MAX_X = max_x
    stdscr.timeout(10)

    # clear everything
    stdscr.clear()
    stdscr.refresh()

    # create main windows
    create_main_windows()

    # run function provided by caller
    func()


def init(func):
    """
    Initialize UI
    """

    curses.wrapper(start, func)
