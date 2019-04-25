"""
Nuqql Conversations
"""

import datetime

from pathlib import Path

import nuqql.history
import nuqql.win


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
        self.history = []
        self.logger = None
        self.log_file = None
        if ctype == "buddy":
            self.list_win = nuqql.win.MAIN_WINS["list"]
            self.logger, self.log_file = nuqql.history.init_logger(self)

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

    def activate_log(self):
        """
        Activate windows of conversation and go to history
        """

        # check log_win to determine, if windows are already created
        if self.log_win is not None:
            self.input_win.active = False
            self.input_win.redraw()
            self.log_win.active = True
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
        self.log_win = nuqql.win.LogWin(log_config, self, log_title)
        self.log_win.list = self.history
        input_config = nuqql.config.get("input_win")
        self.input_win = nuqql.win.InputWin(input_config, self, input_title)

        if self.type == "nuqql":
            # nuqql itself needs a list window for buddy list
            list_config = nuqql.config.get("list_win")
            self.list_win = nuqql.win.ListWin(list_config, self,
                                              "Conversation list")
            # set list to conversations
            self.list_win.list = CONVERSATIONS
            # mark nuqql's list window as active, so main loop does not quit
            self.list_win.active = True

        if self.type == "buddy":
            # try to read old messages from message history
            nuqql.history.init_log_from_file(self)

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
        Log message to conversation's history/log window
        """

        # create a log message and put it into conversation's history
        if tstamp is None:
            tstamp = datetime.datetime.now()
        log_msg = nuqql.history.LogMessage(tstamp, sender, msg)
        self.history.append(log_msg)

        # if conversation is already active, redraw the log window
        if self.is_active():
            self.log_win.redraw()

        return log_msg

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

    def is_any_active(self):
        """
        Check if any conversation is currently active
        """

        if self.is_active():
            return True

        for conv in CONVERSATIONS:
            if conv.is_active():
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

    def send_msg(self, msg):
        """
        Send message coming from the UI/input window
        """

        # TODO: unify the logging in a method of Conversation?
        # log message
        tstamp = datetime.datetime.now()
        log_msg = nuqql.history.LogMessage(tstamp, "you", msg, own=True)
        self.log_win.add(log_msg)

        # depending on conversation type send a message or a command
        if self.type == "buddy":
            # send message and log it in the history file
            self.backend.client.send_msg(self.account.aid, self.name, msg)
            nuqql.history.log(self, log_msg)
        elif self.type == "backend":
            # send command message to backend
            if self.backend is not None:
                self.backend.client.send_command(msg)
        elif self.type == "nuqql":
            # handle nuqql command
            handle_nuqql_command(self, msg)

    def set_lastread(self):
        """
        Helper that sets lastread to the last message in the conversation,
        thus, marking all messages as read.
        """

        # make sure it's a buddy conversation, only they have a lastread file
        if self.type != "buddy":
            return

        log_msg = None
        if self.log_win.list:
            log_msg = self.log_win.list[-1]
            # do not put new conversation event in last_read
            if log_msg.sender == "<event>" and \
               log_msg.msg == "<Started new conversation.>":
                log_msg = None
                if len(self.log_win.list) > 1:
                    log_msg = self.log_win.list[-2]

        # if there is a log message, write it to lastread
        if log_msg:
            nuqql.history.set_lastread(self, log_msg)


def handle_nuqql_global_status(conv, parts):
    """
    Handle nuqql command: global-status
    Call getter and setter funcions
    """

    if not parts:
        return
    sub_command = parts[0]
    if sub_command == "set":
        if len(parts) < 2:
            return
        handle_nuqql_global_status_set(conv, parts[1:])
    elif sub_command == "get":
        handle_nuqql_global_status_get(conv)


def handle_nuqql_global_status_set(conv, status):
    """
    Handle nuqql command: global-status set
    Set status and store it in global_status file
    """

    # only use the first word as status
    if not status or status[0] == "":
        return
    status = status[0]

    # write status to file
    global_status_dir = str(Path.home()) + "/.config/nuqql"
    Path(global_status_dir).mkdir(parents=True, exist_ok=True)
    global_status_file = global_status_dir + "/global_status"
    line = status + "\n"
    lines = []
    lines.append(line)
    with open(global_status_file, "w+") as status_file:
        status_file.writelines(lines)

    # set status in all backends and their accounts
    for conversation in CONVERSATIONS:
        if conversation.type == "backend":
            for acc in conversation.backend.accounts.values():
                conversation.backend.client.send_status_set(acc.aid, status)

    # log message
    tstamp = datetime.datetime.now()
    msg = "global-status: " + status
    log_msg = nuqql.history.LogMessage(tstamp, "nuqql", msg)
    conv.log_win.add(log_msg)


def handle_nuqql_global_status_get(conv):
    """
    Handle nuqql command: global-status get
    Read status from global_status file
    """

    # if there is a global_status file, read it
    global_status_dir = str(Path.home()) + "/.config/nuqql"
    Path(global_status_dir).mkdir(parents=True, exist_ok=True)
    global_status_file = global_status_dir + "/global_status"
    try:
        with open(global_status_file) as status_file:
            line = status_file.readline()
            status = line.split()
            if not status:
                return
            status = status[0]
    except FileNotFoundError:
        return

    # log message
    tstamp = datetime.datetime.now()
    msg = "global-status: " + status
    log_msg = nuqql.history.LogMessage(tstamp, "nuqql", msg)
    conv.log_win.add(log_msg)


def handle_nuqql_command(conv, msg):
    """
    Handle a nuqql command (from the nuqql conversation)
    """

    # parse message
    parts = msg.split()
    if not parts:
        return

    # check command and call helper functions
    command = parts[0]
    if command == "global-status":
        handle_nuqql_global_status(conv, parts[1:])


def log_main_window(msg):
    """
    Log message to main windows
    """

    now = datetime.datetime.now()
    log_msg = nuqql.history.LogMessage(now, "nuqql", msg)
    nuqql.win.MAIN_WINS["log"].add(log_msg)


def resize_main_window():
    """
    Resize main window
    """

    # get main win
    screen = nuqql.win.MAIN_WINS["screen"]

    # get new maxima
    max_y, max_x = screen.getmaxyx()

    # redraw main windows
    screen.clear()
    screen.refresh()

    # redraw conversation windows
    found_active = False
    for conv in CONVERSATIONS:
        # resize and move conversation windows
        if conv.list_win:
            size_y, size_x = conv.list_win.config.get_size()
            conv.list_win.resize_win(size_y, size_x)
        if conv.log_win:
            # TODO: move zoom/resizing to win.py?
            if conv.log_win.zoomed:
                size_y, size_x = max_y, max_x
                pos_y, pos_x = 0, 0
                conv.log_win.pad_y = 0  # reset pad position
            else:
                size_y, size_x = conv.log_win.config.get_size()
                pos_y, pos_x = conv.log_win.config.get_pos()
            conv.log_win.resize_win(size_y, size_x)
            conv.log_win.move_win(pos_y, pos_x)
        if conv.input_win:
            size_y, size_x = conv.input_win.config.get_size()
            conv.input_win.resize_win(size_y, size_x)
            pos_y, pos_x = conv.input_win.config.get_pos()
            conv.input_win.move_win(pos_y, pos_x)
        # redraw active conversation windows
        if conv.is_active():
            found_active = True
            conv.list_win.redraw()
            conv.input_win.redraw()
            conv.log_win.redraw()

    # if there are no active conversations, redraw nuqql main windows
    if not found_active:
        nuqql.win.MAIN_WINS["list"].redraw()
        nuqql.win.MAIN_WINS["log"].redraw()
        nuqql.win.MAIN_WINS["input"].redraw()


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
    nuqql.win.MAIN_WINS["list"] = nuqql_conv.list_win
    nuqql.win.MAIN_WINS["log"] = nuqql_conv.log_win
    nuqql.win.MAIN_WINS["input"] = nuqql_conv.input_win
