"""
User Interface part of nuqql
"""

#######################
# USER INTERFACE PART #
#######################

import curses
import curses.ascii
import datetime

import nuqql.backend

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
        max_y, max_x = STDSCR.getmaxyx()
        self.name = name
        self.backend = backend
        self.account = account
        self.type = ctype

        # determine window sizes
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
        # TODO: unify this?
        if self.type == "buddy":
            # standard chat windows
            self.log_win = LogWin(self, 0, list_win_x, log_win_y, log_win_x,
                                  log_win_y - 2, log_win_x - 2,
                                  "Chat log with " + name)
            self.input_win = InputWin(self, max_y - input_win_y, list_win_x,
                                      input_win_y, input_win_x, 2000, 2000,
                                      "Message to " + name)
        if self.type == "nuqql" or \
           self.type == "backend":
            # command windows for nuqql and backends
            self.log_win = LogWin(self, 0, list_win_x, log_win_y, log_win_x,
                                  log_win_y - 2, log_win_x - 2,
                                  "Command log of " + name)
            self.input_win = MainInputWin(self, max_y - input_win_y,
                                          list_win_x, input_win_y, input_win_x,
                                          2000, 2000, "Command to " + name)
            # do not start as active...
            self.input_win.active = False
            # # ...nuqql's own input_win should be active though
            # if self.type == "nuqql":
            #     self.input_win.active = True

        # draw windows
        self.log_win.redraw()
        self.input_win.redraw()


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

    def go_back(self):
        """
        User input: go back
        """

        # implemented in sub classes

    def cursor_right(self):
        """
        User input: cursor right
        """

        # implemented in sub classes

    def cursor_left(self):
        """
        User input: cursor left
        """

        # implemented in sub classes

    def cursor_down(self):
        """
        User input: cursor down
        """

        # implemented in sub classes

    def cursor_up(self):
        """
        User input: cursor up
        """

        # implemented in sub classes

    def send_msg(self):
        """
        User input: send message
        """

        # implemented in sub classes

    def delete_char(self):
        """
        User input: delete character
        """

        # implemented in sub classes

    def cursor_msg_start(self):
        """
        User input: move cursor to message start
        """

        # implemented in sub classes

    def cursor_msg_end(self):
        """
        User input: move cursor to message end
        """

        # implemented in sub classes

    def cursor_line_start(self):
        """
        User input: move cursor to line start
        """

        # implemented in sub classes

    def cursor_line_end(self):
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
        for buddy in self.list:
            # msg = buddy.account.id + " " + buddy.name + "\n"
            msg = buddy.account.id + " " + buddy.alias + "\n"
            # add buddy status
            if buddy.status == "Offline":
                msg = "[off] " + msg
            elif buddy.status == "Available":
                msg = "[on] " + msg
            else:
                msg = "[{0}] ".format(buddy.status) + msg
            # add notifications
            if buddy.notify > 0:
                msg = "# " + msg
            if buddy.hilight:
                # highlight buddy in list
                self.pad.addstr(msg, curses.A_REVERSE)
            else:
                # just show buddy in list
                self.pad.addstr(msg)

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

    def cursor_up(self):
        if self.cur_y > 0:
            self.pad.move(self.cur_y - 1, self.cur_x)
            self.highlight(self.cur_y, False)
            self.highlight(self.cur_y - 1, True)

    def cursor_down(self):
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
        elif char == ":":
            # switch to command mode
            self.conversation.input_win.active = True
            self.conversation.log_win.active = True
            return
        elif char == "\n":
            # if a conversation exists already, switch to it
            for conv in CONVERSATIONS:
                if conv.account == self.list[self.cur_y].account and\
                   conv.name == self.list[self.cur_y].name:
                    conv.input_win.active = True
                    conv.input_win.redraw()
                    conv.log_win.active = True
                    conv.log_win.redraw()
                    self.clear_notifications(self.list[self.cur_y])
                    return
            # new conversation
            conv = Conversation(self.list[self.cur_y].backend,
                                self.list[self.cur_y].account,
                                self.list[self.cur_y].name)
            CONVERSATIONS.append(conv)
        # display changes in the pad
        self.redraw_pad()

    def notify(self, backend, acc_id, name):
        """
        Notify user about buddy activity
        """

        for buddy in self.list:
            if buddy.backend == backend and \
               buddy.account.id == acc_id and \
               buddy.name == name:
                buddy.notify = 1
        self.redraw_pad()

    def clear_notifications(self, buddy):
        """
        Clear notifications of buddy
        """

        buddy.notify = 0
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

    def cursor_up(self, segment):
        if self.cur_y > 0:
            self.pad.move(self.cur_y - 1,
                          min(self.cur_x, len(segment[self.cur_y - 1])))

    def cursor_down(self, segment):
        if self.cur_y < self.pad_y_max and self.cur_y < len(segment) - 1:
            self.pad.move(self.cur_y + 1,
                          min(self.cur_x, len(segment[self.cur_y + 1])))

    def cursor_left(self, segment):
        if self.cur_x > 0:
            self.pad.move(self.cur_y, self.cur_x - 1)

    def cursor_right(self, segment):
        if self.cur_x < self.pad_x_max and \
           self.cur_x < len(segment[self.cur_y]):
            self.pad.move(self.cur_y, self.cur_x + 1)

    def cursor_line_start(self, segment):
        if self.cur_x > 0:
            self.pad.move(self.cur_y, 0)

    def cursor_line_end(self, segment):
        if self.cur_x < self.pad_x_max and \
           self.cur_x < len(segment[self.cur_y]):
            self.pad.move(self.cur_y, len(segment[self.cur_y]))

    def cursor_msg_start(self, segment):
        if self.cur_y > 0 or self.cur_x > 0:
            self.pad.move(0, 0)

    def cursor_msg_end(self, segment):
        if self.cur_y < len(segment) - 1 or self.cur_x < len(segment[-1]):
            self.pad.move(len(segment) - 1, len(segment[-1]))

    def send_msg(self, segment):
        # do not send empty messages
        if self.msg == "":
            return
        # now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # self.log_win.add(now + " " + self.name + " <-- " + self.msg)
        # self.log_win.add(now + " " + getShortName(self.account.name) + \
        #                  ": " + self.msg)
        now = datetime.datetime.now().strftime("%H:%M:%S")
        log_msg = LogMessage(now, self.conversation.account.name, self.msg,
                             own=True)
        self.conversation.log_win.add(log_msg)
        # send message
        self.conversation.backend.send_client(self.conversation.account.id,
                                              self.conversation.name,
                                              self.msg)
        # reset input
        self.msg = ""
        self.pad.clear()

    def delete_char(self, segment):
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

    def go_back(self, segment):
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
            if type(char) is not str:
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


class MainInputWin(InputWin):
    """
    Class for Command Input Windows
    """

    def send_msg(self, segment):
        # do not send empty messages
        if self.msg == "":
            return

        now = datetime.datetime.now().strftime("%H:%M:%S")
        log_msg = LogMessage(now, self.conversation.account.name, self.msg,
                             own=True)
        self.conversation.log_win.add(log_msg)

        # send command message
        if self.conversation.backend is not None:
            self.conversation.backend.command_client(self.msg)

        # reset input
        self.msg = ""
        self.pad.clear()


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

    max_y_new, max_x_new = STDSCR.getmaxyx()
    if max_y_new == nuqql.ui.MAX_Y and max_x_new == nuqql.ui.MAX_X:
        # nothing has changed
        return MAX_Y, MAX_X

    # window has been resized
    # save new maxima
    nuqql.ui.MAX_Y = max_y_new
    nuqql.ui.MAX_X = max_x_new
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
        conv.log_win.resizeWin(log_win_y, log_win_x)
        conv.log_win.moveWin(0, list_win_x)
        conv.input_win.resizeWin(input_win_y, input_win_x)
        conv.input_win.moveWin(MAX_Y - input_win_y, list_win_x)
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

    # determine window sizes
    # TODO: add to conversation somehow? and/or add variables for the sizes?
    list_win_y, list_win_x = get_absolute_size(MAX_Y, MAX_X,
                                               LIST_WIN_Y_PER, LIST_WIN_X_PER)
    # log_win_y, log_win_x = getAbsoluteSize(MAX_Y, MAX_X,
    #                                        LOG_WIN_Y_PER, LOG_WIN_X_PER)
    # input_win_y, input_win_x = getAbsoluteSize(MAX_Y, MAX_X,
    #                                            INPUT_WIN_Y_PER,
    #                                            INPUT_WIN_X_PER)

    # dummy account for main windows
    nuqql_acc = nuqql.backend.Account()
    nuqql_acc.name = "nuqql"
    nuqql_acc.id = -1
    nuqql_acc.buddies = []

    # main screen
    # dummy conversation for main windows, creates log_win and input_win
    nuqql_conv = Conversation(None, nuqql_acc, "nuqql", ctype="nuqql")
    # user does not start in command mode, so set input_win inactive
    nuqql_conv.input_win.active = False

    # list window for buddy list
    list_win = ListWin(nuqql_conv, 0, 0, list_win_y, list_win_x,
                       list_win_y - 2, 128, "Buddy List")
    list_win.redraw()

    # save windows
    nuqql.ui.LIST_WIN = list_win
    nuqql.ui.LOG_WIN = nuqql_conv.log_win
    nuqql.ui.INPUT_WIN = nuqql_conv.input_win


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


def init(stdscr):
    """
    Initialize UI
    """

    # save stdscr
    nuqql.ui.STDSCR = stdscr

    # configuration
    max_y, max_x = stdscr.getmaxyx()
    nuqql.ui.MAX_Y = max_y
    nuqql.ui.MAX_X = max_x
    stdscr.timeout(10)

    # clear everything
    stdscr.clear()
    stdscr.refresh()

    # create main windows
    create_main_windows()