#######################
# USER INTERFACE PART #
#######################

import curses.ascii
import datetime
import curses

import nuqql.backend

# screen and main windows
stdscr = None
list_win = None
log_win = None
input_win = None
max_y = 0
max_x = 0


# list of active conversations
conversations = []

# default keymap for special keys
default_keymap = {
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
default_input_win_keybinds = {
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
default_log_win_keybinds = default_input_win_keybinds

# default key bindings for list window (Buddy List)
default_list_win_keybinds = default_input_win_keybinds
# default_list_win_keybinds = {
#   ...
#    #"q"             : "GO_BACK", # TODO: do we want something like that?
#    #"\n"            : "DO_SOMETHING", # TODO: do we want something like that?
#   ...
# }

# window x and y sizes in percent
list_win_y_per = 1
list_win_x_per = 0.2
log_win_y_per = 0.8
log_win_x_per = 0.8
input_win_y_per = 0.2
input_win_x_per = 0.8


class Conversation:
    def __init__(self, backend, account, name, ctype="buddy"):
        max_y, max_x = stdscr.getmaxyx()
        self.name = name
        self.backend = backend
        self.account = account
        self.type = ctype

        # determine window sizes
        list_win_y, list_win_x = getAbsoluteSize(max_y, max_x,
                                                 list_win_y_per,
                                                 list_win_x_per)
        log_win_y, log_win_x = getAbsoluteSize(max_y, max_x,
                                               log_win_y_per,
                                               log_win_x_per)
        input_win_y, input_win_x = getAbsoluteSize(max_y, max_x,
                                                   input_win_y_per,
                                                   input_win_x_per)

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
                                          2000, 2000, "Command to: " + name)
            # do not start as active
            self.input_win.active = False

        # draw windows
        self.log_win.redraw()
        self.input_win.redraw()


class Win:
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
        self.keymap = default_keymap
        self.keybind = {}
        self.init_keybinds()
        self.keyfunc = {}
        self.init_keyfunc()

        # conversation
        self.conversation = conversation

        # window title
        # TODO: use name instead?
        self.title = " " + title + " "

    def redrawWin(self):
        self.win.clear()

        # color settings on
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        self.win.attron(curses.color_pair(1) | curses.A_BOLD)

        # window border
        self.win.border()

        # window title
        max_title_len = min(len(self.title), self.win_x_max - 3)
        title = self.title[:max_title_len]
        if len(title) > 0:
            title = title[:-1] + " "
        self.win.addstr(0, 2, title)

        # color settings off
        self.win.attroff(curses.color_pair(1) | curses.A_BOLD)

        self.win.refresh()

    def movePad(self):
        if self.cur_x >= self.win_x_max - 2:
            self.pad_x = self.cur_x - (self.win_x_max - 2)
        if self.cur_x < self.pad_x:
            self.pad_x = self.pad_x - self.cur_x
        if self.cur_y >= self.win_y_max - 2:
            self.pad_y = self.cur_y - (self.win_y_max - 2)
        if self.cur_y < self.pad_y:
            self.pad_y = self.pad_y - self.cur_y

    def checkBorders(self):
        if self.pad_x < 0:
            self.pad_x = 0
        if self.pad_x > self.pad_x_max - self.win_x_max:
            self.pad_x = self.pad_x_max - self.win_x_max
        if self.pad_y < 0:
            self.pad_y = 0
        if self.pad_y > self.pad_y_max - self.win_y_max:
            self.pad_y = self.pad_y_max - self.win_y_max

    def redrawPad(self):
        pass    # implemented in other classes

    def redraw(self):
        self.redrawWin()
        self.redrawPad()

    def add(self, entry):
        self.list.append(entry)
        if self.active:
            self.redraw()

    def resizeWin(self, win_y_max, win_x_max):
        self.win_y_max = win_y_max
        self.win_x_max = win_x_max
        self.win.resize(self.win_y_max, self.win_x_max)

    def moveWin(self, pos_y, pos_x):
        self.pos_y = pos_y
        self.pos_x = pos_x
        self.win.mvwin(self.pos_y, self.pos_x)

    def go_back(self):
        # implemented in sub classes
        pass

    def cursor_right(self):
        # implemented in sub classes
        pass

    def cursor_left(self):
        # implemented in sub classes
        pass

    def cursor_down(self):
        # implemented in sub classes
        pass

    def cursor_up(self):
        # implemented in sub classes
        pass

    def send_msg(self):
        # implemented in sub classes
        pass

    def delete_char(self):
        # implemented in sub classes
        pass

    def cursor_msg_start(self):
        # implemented in sub classes
        pass

    def cursor_msg_end(self):
        # implemented in sub classes
        pass

    def cursor_line_start(self):
        # implemented in sub classes
        pass

    def cursor_line_end(self):
        # implemented in sub classes
        pass

    def init_keybinds(self):
        # implemented in sub classes
        pass

    def init_keyfunc(self):
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
    def redrawPad(self):
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
        self.movePad()
        self.checkBorders()
        self.pad.refresh(self.pad_y, self.pad_x,
                         self.pos_y + 1, self.pos_x + 1,
                         self.pos_y + self.win_y_max - 2,
                         self.pos_x + self.win_x_max - 2)

    def movePad(self):
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

    def highlight(self, y, val):
        buddy = self.list[y]
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
        self.keybind = default_list_win_keybinds

    def processInput(self, ch):
        self.cur_y, self.cur_x = self.pad.getyx()

        # look for special key mappings in keymap or process as text
        if ch in self.keymap:
            func = self.keyfunc[self.keybind[self.keymap[ch]]]
            func()
        elif ch == "q":
            self.active = False
            return  # Exit the while loop
        elif ch == ":":
            # switch to command mode
            self.conversation.input_win.active = True
            self.conversation.log_win.active = True
            return
        elif ch == "\n":
            # if a conversation exists already, switch to it
            for c in conversations:
                if c.account == self.list[self.cur_y].account and\
                   c.name == self.list[self.cur_y].name:
                    c.input_win.active = True
                    c.input_win.redraw()
                    c.log_win.active = True
                    c.log_win.redraw()
                    self.clearNotifications(self.list[self.cur_y])
                    return
            # new conversation
            c = Conversation(self.list[self.cur_y].backend,
                             self.list[self.cur_y].account,
                             self.list[self.cur_y].name)
            conversations.append(c)
        # display changes in the pad
        self.redrawPad()

    def notify(self, backend, acc_id, name):
        for buddy in self.list:
            if buddy.backend == backend and \
               buddy.account.id == acc_id and \
               buddy.name == name:
                buddy.notify = 1
        self.redrawPad()

    def clearNotifications(self, buddy):
        buddy.notify = 0
        self.redrawPad()


class LogWin(Win):
    def redrawPad(self):
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
            self.pad.addstr(getShortName(msg.sender) + ": ")
            self.pad.addstr(msg.msg + "\n")

            # message has now been read
            msg.is_read = True

            # resize pad
            new_y, new_x = self.pad.getyx()
            self.pad_y_max += new_y - old_y
            self.pad.resize(self.pad_y_max, self.pad_x_max)

        # check if visible part of pad needs to be moved and display it
        self.cur_y, self.cur_x = self.pad.getyx()
        self.movePad()
        self.checkBorders()
        self.pad.refresh(self.pad_y, self.pad_x,
                         self.pos_y + 1, self.pos_x + 1,
                         self.pos_y + self.win_y_max - 2,
                         self.pos_x + self.win_x_max - 2)


class InputWin(Win):
    def redrawPad(self):
        self.movePad()
        self.checkBorders()
        self.pad.refresh(self.pad_y, self.pad_x,
                         self.pos_y + 1, self.pos_x + 1,
                         self.pos_y + self.win_y_max - 2,
                         self.pos_x + self.win_x_max - 2)

    def movePad(self):
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
        if len(self.msg) == 0:
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
        self.conversation.backend.sendClient(self.conversation.account.id,
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
        self.keybind = default_input_win_keybinds

    def processInput(self, c):
        segment = self.msg.split("\n")
        self.cur_y, self.cur_x = self.pad.getyx()

        # look for special key mappings in keymap or process as text
        if c in self.keymap:
            func = self.keyfunc[self.keybind[self.keymap[c]]]
            func(segment)
        else:
            # insert new character into segments
            if type(c) is not str:
                return
            segment[self.cur_y] = segment[self.cur_y][:self.cur_x] + c +\
                segment[self.cur_y][self.cur_x:]
            # reconstruct orginal message for output in pad
            self.msg = "\n".join(segment)
            # reconstruct segments in case newline character was entered
            segment = self.msg.split("\n")
            # output new message in pad
            self.pad.erase()
            self.pad.addstr(self.msg)
            # move cursor to new position
            if c == "\n":
                self.pad.move(self.cur_y + 1,
                              min(self.cur_x, len(segment[self.cur_y + 1])))
            else:
                self.pad.move(self.cur_y, self.cur_x + 1)
        # display changes in the pad
        self.redrawPad()


class MainInputWin(InputWin):
    def send_msg(self, segment):
        # do not send empty messages
        if len(self.msg) == 0:
            return

        now = datetime.datetime.now().strftime("%H:%M:%S")
        log_msg = LogMessage(now, self.conversation.account.name, self.msg,
                             own=True)
        self.conversation.log_win.add(log_msg)

        # send command message
        if self.conversation.backend is not None:
            self.conversation.backend.commandClient(self.msg)

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

def getAbsoluteSize(y_max, x_max, y_rel, x_rel):
    y_abs = int(y_max * y_rel)
    x_abs = int(x_max * x_rel)
    return y_abs, x_abs


def resizeMainWindow():
    max_y_new, max_x_new = stdscr.getmaxyx()
    if max_y_new == nuqql.ui.max_y and max_x_new == nuqql.ui.max_x:
        # nothing has changed
        return

    # window has been resized
    # save new maxima
    nuqql.ui.max_y = max_y_new
    nuqql.ui.max_x = max_x_new
    list_win_y, list_win_x = getAbsoluteSize(max_y, max_x,
                                             list_win_y_per, list_win_x_per)
    log_win_y, log_win_x = getAbsoluteSize(max_y, max_x,
                                           log_win_y_per, log_win_x_per)
    input_win_y, input_win_x = getAbsoluteSize(max_y, max_x,
                                               input_win_y_per,
                                               input_win_x_per)

    # resize and move main windows
    list_win.resizeWin(list_win_y, list_win_x)
    log_win.resizeWin(log_win_y, log_win_x)
    log_win.moveWin(0, list_win_x)
    input_win.resizeWin(input_win_y, input_win_x)
    input_win.moveWin(max_y - input_win_y, list_win_x)

    # redraw main windows
    stdscr.clear()
    stdscr.refresh()
    list_win.redraw()
    log_win.redraw()
    input_win.redraw()

    # redraw conversation windows
    for conv in conversations:
        # resize and move conversation windows
        conv.log_win.resizeWin(log_win_y, log_win_x)
        conv.log_win.moveWin(0, list_win_x)
        conv.input_win.resizeWin(input_win_y, input_win_x)
        conv.input_win.moveWin(max_y - input_win_y, list_win_x)
        # redraw active conversation windows
        if conv.input_win.active:
            conv.input_win.redraw()
        if conv.log_win.active:
            conv.log_win.redraw()

    return max_y, max_x


def getShortName(name):
    # TODO: move that somewhere? Improve it?
    # Save short name in account and buddy instead?
    return name.split("@")[0]


def createMainWindows():
    # determine window sizes
    # TODO: add to conversation somehow? and/or add variables for the sizes?
    list_win_y, list_win_x = getAbsoluteSize(max_y, max_x,
                                             list_win_y_per, list_win_x_per)
    log_win_y, log_win_x = getAbsoluteSize(max_y, max_x,
                                           log_win_y_per, log_win_x_per)
    input_win_y, input_win_x = getAbsoluteSize(max_y, max_x,
                                               input_win_y_per,
                                               input_win_x_per)

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
    nuqql.ui.list_win = list_win
    nuqql.ui.log_win = nuqql_conv.log_win
    nuqql.ui.input_win = nuqql_conv.input_win


def readInput():
    """
    Read user input and return it to caller
    """

    # try to get input from user (timeout set in init())
    try:
        ch = stdscr.get_wch()
    except curses.error:
        # no user input...
        ch = None

    return ch


def init(stdscr):
    """
    Initialize UI
    """

    # save stdscr
    nuqql.ui.stdscr = stdscr

    # configuration
    max_y, max_x = stdscr.getmaxyx()
    nuqql.ui.max_y = max_y
    nuqql.ui.max_x = max_x
    stdscr.timeout(10)

    # clear everything
    stdscr.clear()
    stdscr.refresh()

    # create main windows
    nuqql.ui.createMainWindows()
