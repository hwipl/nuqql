#!/usr/bin/env python3

import curses
import curses.ascii
# import sys
import socket
import select
import datetime
import html
import subprocess
import time
import configparser
import signal


from pathlib import Path

###############
# CONFIG PART #
###############

# purpled
PURPLED_CMD = "purpled -u"

# purpled server address/port
SERVER_INET = False
SERVER_IP = "127.0.0.1"
SERVER_PORT = 32000

SERVER_UNIX = True
# /home/<user>/purpled/purpled.sock
SERVER_UNIX_PATH = str(Path.home()) + "/purpled/purpled.sock"

# update buddies only every BUDDY_UPDATE_TIMER seconds
BUDDY_UPDATE_TIMER = 5

# window x and y sizes in percent
list_win_y_per = 1
list_win_x_per = 0.2
log_win_y_per = 0.8
log_win_x_per = 0.8
input_win_y_per = 0.2
input_win_x_per = 0.8

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


####################
# CONFIG FILE PART #
####################


class Account:
    pass


class Config:
    def __init__(self, config_file="nuqql.conf"):
        # init parser for config file
        self.config = configparser.ConfigParser()
        self.config_file = config_file

        # key mapping/binding
        self.keymap = {}
        self.keybind = {}

        # init keybinds
        self.keybind["list_win"] = {}
        self.keybind["input_win"] = {}
        self.keybind["log_win"] = {}

        # accounts
        self.account = {}

    def addAccount(self, account):
        self.account[account.name] = account

    def delAccount(self, account):
        del self.account[account.name]

    def addKeymap(self, key, name):
        self.keymap[key] = name

    def delKeymap(self, key):
        del self.keymap[key]

    def addKeybind(self, context, name, action):
        self.keybind[context][name] = action

    def delKeybind(self, context, name):
        del self.keybind[context][name]

    def readConfig(self):
        self.config.read(self.config_file)
        for section in self.config.sections():
            if section == "list_win":
                pass
            elif section == "log_win":
                pass
            elif section == "input_win":
                pass
            elif section == "purpled":
                pass
            else:
                # everything else is treated as account settings
                pass

    def writeConfig(self):
        with open(self.config_file, "w") as configfile:
            self.config.write(configfile)


################
# NETWORK PART #
################

BUFFER_SIZE = 4096


class PurpledServer:
    def __init__(self):
        self.proc = None

    def start(self):
        purpled_cmd = PURPLED_CMD
        self.proc = subprocess.Popen(
            purpled_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,     # dont send SIGINT from nuqql to
                                        # subprocess
        )
        # give it some time
        time.sleep(1)

    def stop(self):
        self.proc.terminate()


class PurpledClient:
    def __init__(self, config):
        self.config = config
        self.sock = None
        self.buffer = ""
        # self.collect_acc = -1

    def initClient(self):
        # open sockets and connect
        if SERVER_INET:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((SERVER_IP, SERVER_PORT))
        elif SERVER_UNIX:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(SERVER_UNIX_PATH)

    def exitClient(self):
        self.sock.close()

    def readClient(self):
        reads, writes, errs = select.select([self.sock, ], [],
                                            [self.sock, ], 0)
        if self.sock in reads:
            # read data from socket and add it to buffer
            data = self.sock.recv(BUFFER_SIZE)
            self.buffer += data.decode()

        # get next message from buffer and return it
        eom = self.buffer.find("\r\n")
        if eom == -1:
            # no message found
            return None

        # remove message from buffer and return it
        msg = self.buffer[:eom]
        # remove message including "\r\n" from buffer
        self.buffer = self.buffer[eom + 2:]
        return msg

    def commandClient(self, cmd):
        # TODO: do more?
        msg = cmd + "\r\n"
        msg = msg.encode()
        self.sock.send(msg)
        return

    def sendClient(self, account, buddy, msg):
        prefix = "account {0} send {1} ".format(account, buddy)
        msg = html.escape(msg)
        msg = "<br>".join(msg.split("\n"))
        msg = prefix + msg + "\r\n"
        msg = msg.encode()
        self.sock.send(msg)

    def collectClient(self, account):
        msg = "account {0} collect\r\n".format(account)
        msg = msg.encode()
        # self.collect_acc = account
        self.sock.send(msg)

    def buddiesClient(self, account):
        msg = "account {0} buddies\r\n".format(account)
        msg = msg.encode()
        self.sock.send(msg)

    def accountsClient(self):
        msg = "account list\r\n"
        msg = msg.encode()
        self.sock.send(msg)

    def parseErrorMsg(self, orig_msg):
        # "error: %s\r\n"
        error = orig_msg[7:]
        return "error", error

    def parseInfoMsg(self, orig_msg):
        # "info: %s\r\n"
        info = orig_msg[6:]
        return "info", info

    def parseAccountMsg(self, orig_msg):
        # "account: %d %s %s %s [%s]\r\n"
        orig_msg = orig_msg[9:]
        part = orig_msg.split(" ")
        acc_id = part[0]
        acc_alias = part[1]
        acc_prot = part[2].lower()
        acc_user = part[3]
        acc_status = part[4]    # ignore [ and ] for now
        return "account", acc_id, acc_alias, acc_prot, acc_user, acc_status

    def parseCollectMsg(self, orig_msg):
        # collect response and message have the same message format
        return self.parseMessageMsg(orig_msg)

    def parseMessageMsg(self, orig_msg):
        orig_msg = orig_msg[9:]
        part = orig_msg.split(" ")
        acc = part[0]
        acc_name = part[1]
        tstamp = part[2]
        sender = part[3]
        msg = " ".join(part[4:])
        msg = "\n".join(msg.split("<BR>"))
        msg = html.unescape(msg)
        tstamp = datetime.datetime.fromtimestamp(int(tstamp))
        # tstamp = tstamp.strftime("%Y-%m-%d %H:%M:%S")
        # TODO: move timestamp conversion to caller?
        tstamp = tstamp.strftime("%H:%M:%S")
        return "message", acc, acc_name, tstamp, sender, msg

    def parseBuddyMsg(self, orig_msg):
        orig_msg = orig_msg[7:]
        # <acc> status: <Offline/Available> name: <name> alias: <alias>
        part = orig_msg.split(" ")
        acc = part[0]
        status = part[2]
        name = part[4]
        alias = part[6]
        return "buddy", acc, status, name, alias

    def parseMsg(self, orig_msg):
        if orig_msg.startswith("message: "):
            return self.parseMessageMsg(orig_msg)
        elif orig_msg.startswith("collect: "):
            return self.parseCollectMsg(orig_msg)
        elif orig_msg.startswith("buddy: "):
            return self.parseBuddyMsg(orig_msg)
        elif orig_msg.startswith("account: "):
            return self.parseAccountMsg(orig_msg)
        elif orig_msg.startswith("info: "):
            return self.parseInfoMsg(orig_msg)
        elif orig_msg.startswith("error: "):
            return self.parseErrorMsg(orig_msg)
        else:
            # TODO: improve/remove this error handling!
            acc = -1
            acc_name = "error"
            tstamp = "never"
            sender = "purpled"
            msg = "Error parsing message: " + orig_msg
            return "error", acc, acc_name, tstamp, sender, msg


##################
# Helper Classes #
##################

class LogMessage:
    """Class for log messages to be displayed in LogWins"""

    def __init__(self, log_win, tstamp, account, buddy, inc, msg):
        # associate this message with a LogWin
        self.log_win = log_win

        # timestamp
        self.tstamp = tstamp

        # account
        self.account = account

        # buddy and is message incoming or outgoing
        self.buddy = buddy
        self.inc = inc

        # message itself
        self.msg = msg

        # has message been read?
        self.is_read = False

    def show(self):
        """Show message in LogWin"""
        # TODO: maybe in the future?
        # self.log_win.pad.addstr(msg + "\n")
        # message is read now
        # self.is_read = True
        return


class Buddy:
    def __init__(self, account, name):
        self.account = account
        self.name = name
        self.alias = name
        self.status = "Offline"
        self.hilight = False
        self.notify = False

    # def __cmp__(self, other):
    #    if hasattr(other, 'getKey'):
    #        return self.getKey().__cmp__(other.getKey())

    def __lt__(self, other):
        return self.getKey() < other.getKey()

    def getKey(self):
        return self.status + self.name


#######################
# USER INTERFACE PART #
#######################

# list of active conversations
# TODO: does this even make sense?
conversation = []


class Conversation:
    def __init__(self, stdscr, account, name):
        max_y, max_x = stdscr.getmaxyx()
        self.name = name
        self.account = account

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

        # create and draw windows
        self.log_win = LogWin(stdscr, account, name, None, None, 0, list_win_x,
                              log_win_y, log_win_x,
                              log_win_y - 2, log_win_x - 2,
                              "Chat log with " + name)
        self.log_win.redraw()
        self.input_win = InputWin(stdscr, account, name, self.log_win, None,
                                  max_y - input_win_y, list_win_x,
                                  input_win_y, input_win_x, 2000, 2000,
                                  "Message to " + name)
        self.input_win.redraw()


class Win:
    def __init__(self, stdscr, account, name, log_win, input_win, pos_y, pos_x,
                 win_y_max, win_x_max, pad_y_max, pad_x_max, title):
        self.superWin = stdscr
        self.name = name

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

        # log window
        self.log_win = log_win

        # input window
        self.input_win = input_win

        # list entries/message log
        self.list = []

        # keymaps/bindings
        self.keymap = default_keymap
        self.keybind = {}
        self.init_keybinds()
        self.keyfunc = {}
        self.init_keyfunc()

        # account
        self.account = account

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
            self.input_win.active = True
            self.log_win.active = True
            return
        elif ch == "\n":
            # if a conversation exists already, switch to it
            for c in conversation:
                if c.account == self.list[self.cur_y].account and\
                   c.name == self.list[self.cur_y].name:
                    c.input_win.active = True
                    c.input_win.redraw()
                    c.log_win.active = True
                    c.log_win.redraw()
                    self.clearNotifications(self.list[self.cur_y])
                    return
            # new conversation
            c = Conversation(self.superWin, self.list[self.cur_y].account,
                             self.list[self.cur_y].name)
            conversation.append(c)
        # display changes in the pad
        self.redrawPad()

    def notify(self, acc_id, name):
        for buddy in self.list:
            if buddy.account.id == acc_id and buddy.name == name:
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
            if msg.inc:
                # message from buddy
                if msg.is_read:
                    # old message
                    self.pad.attroff(curses.A_BOLD)
                    self.pad.attron(curses.color_pair(3) | curses.A_NORMAL)
                else:
                    # new message
                    self.pad.attroff(curses.A_NORMAL)
                    self.pad.attron(curses.color_pair(3) | curses.A_BOLD)

                # output message
                self.pad.addstr(msg.tstamp + " ")
                self.pad.addstr(getShortName(msg.buddy) + ": ")
                self.pad.addstr(msg.msg + "\n")
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
                self.pad.addstr(getShortName(msg.account.name) + ": ")
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

    def cursor_up(self, segment, client):
        if self.cur_y > 0:
            self.pad.move(self.cur_y - 1,
                          min(self.cur_x, len(segment[self.cur_y - 1])))

    def cursor_down(self, segment, client):
        if self.cur_y < self.pad_y_max and self.cur_y < len(segment) - 1:
            self.pad.move(self.cur_y + 1,
                          min(self.cur_x, len(segment[self.cur_y + 1])))

    def cursor_left(self, segment, client):
        if self.cur_x > 0:
            self.pad.move(self.cur_y, self.cur_x - 1)

    def cursor_right(self, segment, client):
        if self.cur_x < self.pad_x_max and \
           self.cur_x < len(segment[self.cur_y]):
            self.pad.move(self.cur_y, self.cur_x + 1)

    def cursor_line_start(self, segment, client):
        if self.cur_x > 0:
            self.pad.move(self.cur_y, 0)

    def cursor_line_end(self, segment, client):
        if self.cur_x < self.pad_x_max and \
           self.cur_x < len(segment[self.cur_y]):
            self.pad.move(self.cur_y, len(segment[self.cur_y]))

    def cursor_msg_start(self, segment, client):
        if self.cur_y > 0 or self.cur_x > 0:
            self.pad.move(0, 0)

    def cursor_msg_end(self, segment, client):
        if self.cur_y < len(segment) - 1 or self.cur_x < len(segment[-1]):
            self.pad.move(len(segment) - 1, len(segment[-1]))

    def send_msg(self, segment, client):
        # do not send empty messages
        if len(self.msg) == 0:
            return
        # now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # self.log_win.add(now + " " + self.name + " <-- " + self.msg)
        # self.log_win.add(now + " " + getShortName(self.account.name) + \
        #                  ": " + self.msg)
        now = datetime.datetime.now().strftime("%H:%M:%S")
        log_msg = LogMessage(self.log_win, now, self.account, self.name, False,
                             self.msg)
        self.log_win.add(log_msg)
        # send message
        client.sendClient(self.account.id, self.name, self.msg)
        # reset input
        self.msg = ""
        self.pad.clear()

    def delete_char(self, segment, client):
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

    def go_back(self, segment, client):
        self.active = False
        self.log_win.active = False

    def init_keybinds(self):
        self.keybind = default_input_win_keybinds

    def processInput(self, c, client):
        segment = self.msg.split("\n")
        self.cur_y, self.cur_x = self.pad.getyx()

        # look for special key mappings in keymap or process as text
        if c in self.keymap:
            func = self.keyfunc[self.keybind[self.keymap[c]]]
            func(segment, client)
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
    def send_msg(self, segment, client):
        # do not send empty messages
        if len(self.msg) == 0:
            return

        now = datetime.datetime.now().strftime("%H:%M:%S")
        log_msg = LogMessage(self.log_win, now, self.account, self.name, False,
                             self.msg)
        self.log_win.add(log_msg)

        # send command message
        client.commandClient(self.msg)

        # reset input
        self.msg = ""
        self.pad.clear()

####################
# HELPER FUNCTIONS #
####################


def getAbsoluteSize(y_max, x_max, y_rel, x_rel):
    y_abs = int(y_max * y_rel)
    x_abs = int(x_max * x_rel)
    return y_abs, x_abs


def resizeMainWindow(stdscr, list_win, log_win, input_win, conversation,
                     max_y, max_x):
    max_y_new, max_x_new = stdscr.getmaxyx()
    if max_y_new == max_y and max_x_new == max_x:
        # nothing has changed
        return max_y, max_x

    # window has been resized
    # save new maxima
    max_y = max_y_new
    max_x = max_x_new
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
    for conv in conversation:
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


def handleAccountMsg(config, client, log_win, msg):
    # "account", acc_id, acc_alias, acc_prot, acc_user, acc_status
    (msg_type, acc_id, acc_alias, acc_prot, acc_user, acc_status) = msg

    # output account
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = "account {0} ({1}) {2} {3} {4}.".format(acc_id, acc_alias, acc_prot,
                                                   acc_user, acc_status)
    log_msg = LogMessage(log_win, now, None, "nuqql", True, text)
    log_win.add(log_msg)

    # do not add account if it already exists
    if acc_user in config.account:
        return

    # new account, add it
    acc = Account()
    acc.name = acc_user
    acc.id = acc_id
    acc.alias = acc_alias
    acc.type = acc_prot
    acc.status = acc_status
    acc.buddies = []
    acc.buddies_update = 0
    config.addAccount(acc)

    # collect buddies from purpled
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = "Collecting buddies for {0} account {1}: {2}.".format(
        acc.type, acc.id, acc.name)
    log_msg = LogMessage(log_win, now, None, "nuqql", True, text)
    log_win.add(log_msg)
    acc.buddies_update = time.time()
    client.buddiesClient(acc.id)

    # collect messages from purpled
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = "Collecting messages for {0} account {1}: {2}.".format(
        acc.type, acc.id, acc.name)
    log_msg = LogMessage(log_win, now, None, "nuqql", True, text)
    log_win.add(log_msg)
    client.collectClient(acc.id)


def handleBuddyMsg(config, list_win, msg):
    (msg_type, acc, status, name, alias) = msg
    # # look for existing buddy
    # for buddy in config.account[acc].buddies:
    #    if buddy == name:
    #        # TODO: use/update status
    #        return
    # # new buddy
    # config.account[acc].buddies.append(name)

    # look for existing buddy
    for buddy in list_win.list:
        if buddy.account.id == acc and\
           buddy.name == name:
            old_status = buddy.status
            old_alias = buddy.alias
            buddy.status = status
            buddy.alias = alias
            if old_status != status or old_alias != alias:
                list_win.redraw()
            return
    # new buddy
    for acc_name, account in config.account.items():
        if account.id == acc:
            new_buddy = Buddy(account, name)
            new_buddy.status = status
            new_buddy.alias = alias
            list_win.add(new_buddy)
            list_win.redraw()
            return


def updateBuddies(config, client, log_win):
    # update buddies
    for acc in config.account.values():
        # update only once every BUDDY_UPDATE_TIMER seconds
        if time.time() - acc.buddies_update <= BUDDY_UPDATE_TIMER:
            continue
        acc.buddies_update = time.time()
        client.buddiesClient(acc.id)


def handleNetwork(config, client, conversation, list_win, log_win):
    msg = client.readClient()
    if msg is None:
        return
    # TODO: do not ignore account name
    # TODO: it's not even an acc_name, it's the name of the buddy? FIXME
    msg = client.parseMsg(msg)
    msg_type = msg[0]

    # handle info message or error message
    if msg_type == "info" or msg_type == "error":
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = msg_type + ": " + msg[1]
        log_msg = LogMessage(log_win, now, None, "nuqql", True, text)
        log_win.add(log_msg)
        return

    # handle account message
    if msg_type == "account":
        handleAccountMsg(config, client, log_win, msg)
        return

    # handle buddy messages
    if msg_type == "buddy":
        handleBuddyMsg(config, list_win, msg)
        return

    # handle normal messages and error messages
    # TODO: handle error messages somewhere else?
    if msg_type == "message" or msg_type == "error":
        (msg_type, acc, acc_name, tstamp, sender, msg) = msg

    # account specific message parsing
    for tmp_acc_name, tmp_acc in config.account.items():
        if tmp_acc.id == acc:
            if tmp_acc.type == "icq":
                if sender[-1] == ":":
                    sender = sender[:-1]
                if msg[:6] == "<BODY>":
                    msg = msg[6:]
                if msg[-7:] == "</BODY>":
                    msg = msg[:-7]
                break
            elif tmp_acc.type == "xmpp":
                sender = sender.split("/")[0]
                break

    # look for an existing conversation and use it
    for conv in conversation:
        if conv.input_win.account.id == acc and\
           conv.input_win.name == sender:
            # conv.log_win.add(tstamp + " " + sender + " --> " + msg)
            # conv.log_win.add(tstamp + " " + getShortName(sender) + ": " +msg)
            log_msg = LogMessage(conv.log_win, tstamp, conv.account, conv.name,
                                 True, msg)
            conv.log_win.add(log_msg)
            # if window is not already active notify user
            if not conv.input_win.active:
                list_win.notify(acc, sender)
            return

    # create a new conversation if buddy exists
    # TODO: can we add some helper functions?
    for buddy in list_win.list:
        if buddy.account.id == acc and buddy.name == sender:
            c = Conversation(list_win.superWin, buddy.account, buddy.name)
            c.input_win.active = False
            c.log_win.active = False
            conversation.append(c)
            # c.log_win.add(tstamp + " " + sender + " --> " + msg)
            # c.log_win.add(tstamp + " " + getShortName(sender) + ": " + msg)
            log_msg = LogMessage(c.log_win, tstamp, c.account, c.name, True,
                                 msg)
            c.log_win.add(log_msg)
            list_win.notify(acc, sender)
            return

    # nothing found, log to main window
    # log_win.add(tstamp + " " + sender + " --> " + msg)
    log_msg = LogMessage(log_win, tstamp, None, sender, True, msg)
    log_win.add(log_msg)


def createMainWindows(config, stdscr, max_y, max_x):
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
    nuqql_acc = Account()
    nuqql_acc.name = "nuqql"
    nuqql_acc.id = -1
    nuqql_acc.buddies = []

    # main screen
    # list window for buddy list
    list_win = ListWin(stdscr, nuqql_acc, "BuddyList", None, None, 0, 0,
                       list_win_y, list_win_x, list_win_y - 2, 128,
                       "Buddy List")
    list_win.redraw()
    # fill with buddies from config
    for acc in config.account.keys():
        for buddy in config.account[acc].buddies:
            new_buddy = Buddy(config.account[acc], buddy)
            list_win.add(new_buddy)

    # control/config conversation
    # TODO: add to conversation somehow? and/or add variables for the sizes?
    log_win = LogWin(stdscr, nuqql_acc, "nuqql", None, None, 0, list_win_x,
                     log_win_y, log_win_x, log_win_y - 2, log_win_x - 2,
                     "nuqql main log")
    log_win.redraw()
    input_win = MainInputWin(stdscr, nuqql_acc, "nuqql", log_win, None,
                             max_y - input_win_y, list_win_x,
                             input_win_y, input_win_x, 2000, 2000,
                             "nuqql commands")
    input_win.redraw()

    # user does not start in command mode, so set input_win inactive
    input_win.active = False

    # save input_win and log_win in list_win
    list_win.log_win = log_win
    list_win.input_win = input_win

    return list_win, log_win, input_win


def getShortName(name):
    # TODO: move that somewhere? Improve it?
    # Save short name in account and buddy instead?
    return name.split("@")[0]

###############
# MAIN (LOOP) #
###############


def main(stdscr):
    max_y, max_x = stdscr.getmaxyx()
    stdscr.timeout(10)

    stdscr.clear()
    stdscr.refresh()

    # load config
    config = Config()
    config.readConfig()

    # create main windows
    list_win, log_win, input_win = createMainWindows(config, stdscr,
                                                     max_y, max_x)

    # start purpled
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = LogMessage(log_win, now, None, "nuqql", True, "Start purpled.")
    log_win.add(log_msg)
    server = PurpledServer()
    server.start()

    # start purpled client
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = LogMessage(log_win, now, None, "nuqql", True, "Start client.")
    log_win.add(log_msg)
    client = PurpledClient(config)
    client.initClient()

    # collect accounts from purpled
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = LogMessage(log_win, now, None, "nuqql", True,
                         "Collecting accounts.")
    log_win.add(log_msg)
    client.accountsClient()

    # start main loop
    while True:
        # wait for user input
        try:
            ch = stdscr.get_wch()
        except curses.error:
            # no user input...
            ch = None

        # check size and redraw windows if necessary
        max_y, max_x = resizeMainWindow(stdscr, list_win, log_win, input_win,
                                        conversation, max_y, max_x)

        # update buddies
        updateBuddies(config, client, log_win)

        # handle network input
        handleNetwork(config, client, conversation, list_win, log_win)

        # handle user input
        if ch is None:
            # NO INPUT, keep waiting for input...
            continue

        # pass user input to active conversation
        conv_active = False
        for conv in conversation:
            if conv.input_win.active:
                conv.input_win.processInput(ch, client)
                conv_active = True
                break
        # if no conversation is active pass input to list window
        if not conv_active:
            if input_win.active:
                input_win.processInput(ch, client)
            elif list_win.active:
                # TODO: improve ctrl window handling?
                input_win.redraw()
                log_win.redraw()
                list_win.processInput(ch)
            else:
                # list window is also inactive -> user quit
                client.exitClient()
                server.stop()
                break


# ignore SIGINT
signal.signal(signal.SIGINT, signal.SIG_IGN)

curses.wrapper(main)
