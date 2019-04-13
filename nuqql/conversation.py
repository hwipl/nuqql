"""
Nuqql Conversations
"""

import datetime

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
        self.logger = None
        self.log_file = None
        if ctype == "buddy":
            self.list_win = nuqql.win.MAIN_WINS["list"]
            self.logger, self.log_file = nuqql.history.init_logger(backend,
                                                                   account,
                                                                   name)

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
        self.log_win = nuqql.win.LogWin(log_config, self, log_title)
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
        Log message to conversation's log window
        """

        if tstamp is None:
            tstamp = datetime.datetime.now()
        log_msg = nuqql.history.LogMessage(tstamp, sender, msg)
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
        # log_msg = LogMessage(now, self.conversation.account.name, self.msg,
        # TODO: add conversation -> own name function? just use "You"?
        log_msg = nuqql.history.LogMessage(tstamp, self.name, msg, own=True)
        self.log_win.add(log_msg)

        # depending on conversation type send a message or a command
        if self.type == "buddy":
            # send message
            self.backend.client.send_msg(self.account.aid, self.name, msg)
            tstamp = round(tstamp.timestamp())
            msg = nuqql.history.create_log_line(tstamp, "OUT", "you", msg)
            self.logger.info(msg)
            nuqql.history.set_lastread(self.backend, self.account, self.name,
                                       tstamp, "OUT", "you", msg)
        else:
            # send command message
            if self.backend is not None:
                self.backend.client.send_command(msg)


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
    nuqql.win.MAIN_WINS["list"] = nuqql_conv.list_win
    nuqql.win.MAIN_WINS["log"] = nuqql_conv.log_win
    nuqql.win.MAIN_WINS["input"] = nuqql_conv.input_win
