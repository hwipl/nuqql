"""
Backend part of nuqql.
"""

################
# NETWORK PART #
################

import subprocess
import socket
import select
import shutil
import time
import html
import os
import re

from pathlib import Path

import nuqql.conversation
import nuqql.ui

# network buffer
BUFFER_SIZE = 4096

# update buddies only every BUDDY_UPDATE_TIMER seconds
BUDDY_UPDATE_TIMER = 5

# dictionary for all active backends
BACKENDS = {}

# enable/disable logging of subprocess output
SUBPROCESS_LOGGING = True

# how long should we wait for backends (in seconds) before starting clients
BACKENDS_WAIT_TIME = 1

# how often should a backend client try to connect to its server and
# how long (in seconds) should a backend client sleep between retries?
CLIENT_MAX_RETRIES = 100
CLIENT_RETRY_SLEEP = 0.1

# backend error message
BACKEND_ERROR = "Error accessing backend."


class BackendServer:
    """
    Class for a backend's server process
    """

    def __init__(self, cmd="", path=""):
        # server
        self.proc = None
        self.server_path = path
        self.server_cmd = cmd

        # subprocess output logging files
        self.stdout_file = subprocess.DEVNULL
        self.stderr_file = subprocess.DEVNULL

    def start(self):
        """
        Start the backend's server process
        """

        # make sure server's working directory exists
        Path(self.server_path).mkdir(parents=True, exist_ok=True)

        # if logging is enabled for subprocess output, open log files
        if SUBPROCESS_LOGGING:
            Path(self.server_path + "/logs").mkdir(parents=True, exist_ok=True)
            self.stdout_file = open(self.server_path +
                                    "/logs/backend-stdout.log", "a")
            self.stderr_file = open(self.server_path +
                                    "/logs/backend-stderr.log", "a")

        # start server process
        self.proc = subprocess.Popen(
            self.server_cmd,
            shell=True,
            stdout=self.stdout_file,
            stderr=self.stderr_file,
            start_new_session=True,     # dont send SIGINT from nuqql to
                                        # subprocess
        )

    def stop(self):
        """
        Stop the backend's server process
        """

        # stop running server
        self.proc.terminate()

        # close subprocess log files if logging is enabled
        if SUBPROCESS_LOGGING:
            self.stdout_file.close()
            self.stderr_file.close()


class BackendClient:
    """
    Class for a backend's client connection to a
    local or remote backend server process
    """

    def __init__(self, sock_af=socket.AF_UNIX, ip_addr="127.0.0.1", port=32000,
                 sock_file=""):
        # client
        self.backend = None
        self.sock = None
        self.sock_af = sock_af
        self.sock_file = sock_file
        self.ip_addr = ip_addr
        self.port = port
        self.buffer = ""

    def _connect(self):
        """
        Helper for connecting to the server
        """

        if self.sock_af == socket.AF_INET:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.ip_addr, self.port))
        elif self.sock_af == socket.AF_UNIX:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(self.sock_file)

    def start(self):
        """
        Start the backend's client
        """

        # open sockets and connect
        retries = 0
        while not self.sock and retries < CLIENT_MAX_RETRIES:
            try:
                self._connect()
            except OSError:
                self.sock = None
                retries += 1
                time.sleep(CLIENT_RETRY_SLEEP)

    def stop(self):
        """
        Stop the backend's client
        """

        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def read(self):
        """
        Read from the client connection
        """

        if not self.sock:
            return None

        try:
            reads, unused_writes, errs = select.select([self.sock, ], [],
                                                       [self.sock, ], 0)
        except OSError:
            nuqql.conversation.log_main_window(BACKEND_ERROR)
            self.backend.stop()
            return None

        if self.sock in errs:
            # something is wrong
            self.backend.stop()
            return None

        if self.sock in reads:
            # read data from socket and add it to buffer
            try:
                data = self.sock.recv(BUFFER_SIZE)
            except OSError:
                nuqql.conversation.log_main_window(BACKEND_ERROR)
                self.backend.stop()
                return None
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

    def _send(self, msg):
        """
        Helper for sending any messages and catching errors.
        """

        if not self.sock:
            return

        msg = msg.encode()

        try:
            self.sock.send(msg)
        except OSError:
            nuqql.conversation.log_main_window(BACKEND_ERROR)
            self.backend.stop()
            return

    def send_command(self, cmd):
        """
        Send a command over the client connection
        """

        msg = cmd + "\r\n"
        self._send(msg)

    def send_msg(self, account, buddy, msg):
        """
        Send a regular message over the client connection
        """

        prefix = "account {0} send {1} ".format(account, buddy)
        msg = html.escape(msg)
        msg = "<br/>".join(msg.split("\n"))
        msg = prefix + msg + "\r\n"
        self._send(msg)

    def send_group_msg(self, account, buddy, msg):
        """
        Send a group message over the client connection
        """

        prefix = "account {0} chat send {1} ".format(account, buddy)
        msg = html.escape(msg)
        msg = "<br/>".join(msg.split("\n"))
        msg = prefix + msg + "\r\n"
        self._send(msg)

    def send_collect(self, account):
        """
        Send "collect" message over the client connection,
        which collects all messages received by the backend
        """

        # collect all messages since time 0
        # TODO: only works as intended if we spawn our own purpled daemon at
        # nuqql's startup, FIXME?
        msg = "account {0} collect 0\r\n".format(account)
        # self.collect_acc = account
        self._send(msg)

    def send_buddies(self, account):
        """
        Send "buddies" message over the client connection,
        which retrieves all buddies of the specified account from the backend
        """

        msg = "account {0} buddies\r\n".format(account)
        self._send(msg)

    def send_accounts(self):
        """
        Send "account list" message over the client connection,
        which retrieves all accounts from the backend
        """

        msg = "account list\r\n"
        self._send(msg)

    def send_status_set(self, account, status):
        """
        Send "status set" message over client connection,
        which sets the status of the specified account of the backend
        """

        msg = "account {} status set {}\r\n".format(account, status)
        self._send(msg)


class Backend:
    """
    Class for backends. Allows starting server processes and connecting to
    (self-started or externally started) servers
    """

    def __init__(self, name):
        # backend
        self.name = name
        self.accounts = {}
        # conversation for communication with the backend.
        self.conversation = None

        # server
        self.server = None

        # client
        self.client = None

        # self.collect_acc = -1

    def start_server(self, cmd, path):
        """
        Add a server to this backend and start it
        """

        self.server = BackendServer(cmd, path)
        self.server.start()

    def stop_server(self):
        """
        Stop the server of this backend
        """

        if self.server:
            self.server.stop()

    def start_client(self):
        """
        Start the backend's client
        """

        self.client.start()

    def init_client(self, sock_af=socket.AF_UNIX, ip_addr="127.0.0.1",
                    port=32000, sock_file=""):
        """
        Add a client to this backend
        """

        self.client = BackendClient(sock_af, ip_addr, port, sock_file)
        self.client.backend = self

    def stop_client(self):
        """
        Stop the client of this backend
        """

        if self.client:
            self.client.stop()

    def handle_network(self):
        """
        Try to read from the client connection and handle messages.
        """

        # try to read message
        msg = self.client.read()
        if msg is None:
            return

        # parse it
        parsed_msg = parse_msg(msg)
        msg_type = parsed_msg[0]

        # handle info message or error message
        if msg_type in ("info", "error"):
            text = msg_type + ": " + parsed_msg[1]
            self.conversation.log("nuqql", text)
            return

        # handle account message
        if msg_type == "account":
            self.handle_account_msg(parsed_msg)
            return

        # handle status message
        if msg_type == "status":
            text = "account {} status: {}".format(parsed_msg[1], parsed_msg[2])
            self.conversation.log("nuqql", text)
            return

        # handle chat message
        if msg_type == "chat":
            self.handle_chat_msg(parsed_msg)
            return

        # handle buddy messages
        if msg_type == "buddy":
            self.handle_buddy_msg(parsed_msg)
            return

        # handle normal messages and error messages
        # TODO: handle error messages somewhere else?
        if msg_type in ("message", "parsing error"):
            self.handle_message_msg(parsed_msg)

    def handle_message_msg(self, parsed_msg):
        """
        Handle "message" message
        """

        # msg_type = parsed_msg[0]
        acc_id = parsed_msg[1]
        # destination = parsed_msg[2]
        tstamp = parsed_msg[3]
        sender = parsed_msg[4]
        msg = parsed_msg[5]

        # account specific message parsing
        # TODO: remove duplicate code?
        resource = ""
        for tmp_acc in self.accounts.values():
            if tmp_acc.aid == acc_id:
                if tmp_acc.type == "icq":
                    if sender[-1] == ":":
                        sender = sender[:-1]
                    if msg[:6] == "<BODY>":
                        msg = msg[6:]
                    if msg[-7:] == "</BODY>":
                        msg = msg[:-7]
                    break
                elif tmp_acc.type == "xmpp":
                    sender_parts = sender.split("/")
                    sender = sender_parts[0]
                    if len(sender_parts) > 1:
                        resource = sender_parts[1]
                    break
                elif tmp_acc.type == "matrix":
                    # TODO: improve?
                    sender = sender[1:].split(":")[0]
                    resource = sender
                    sender = parsed_msg[2]
                    break

        # let ui handle the message
        nuqql.ui.handle_message(self, acc_id, tstamp, sender, msg, resource)

    def handle_chat_msg(self, parsed_msg):
        """
        Handle Chat message
        """

        # "chat", ctype, acc, chat, nick
        ctype = parsed_msg[1]
        acc_id = parsed_msg[2]
        chat = parsed_msg[3]

        # msg message
        if ctype == "msg:":
            timestamp = parsed_msg[4]
            sender = parsed_msg[5]
            msg = parsed_msg[6]

            # account specific message parsing
            # TODO: remove duplicate code?
            for tmp_acc in self.accounts.values():
                if tmp_acc.aid == acc_id:
                    if tmp_acc.type == "icq":
                        if sender[-1] == ":":
                            sender = sender[:-1]
                        if msg[:6] == "<BODY>":
                            msg = msg[6:]
                        if msg[-7:] == "</BODY>":
                            msg = msg[:-7]
                        break
                    elif tmp_acc.type == "xmpp":
                        sender_parts = sender.split("/")
                        sender = sender_parts[0]
                        break
                    elif tmp_acc.type == "matrix":
                        # TODO: improve?
                        sender = sender[1:].split(":")[0]
                        break
            # handle message in ui
            nuqql.ui.handle_chat_msg_message(self, acc_id, chat, timestamp,
                                             sender, msg)
            return

        # user message
        if ctype == "user:":
            nick = parsed_msg[4]
            alias = parsed_msg[5]
            status = parsed_msg[6]
            # if there is a conversation for this type and group chat, log to
            # it. Otherwise, just log to backend conversation later
            if nuqql.ui.handle_chat_message(self, acc_id, ctype, chat, nick,
                                            alias, status):
                return

        # list message
        if ctype == "list:":
            chat_alias = parsed_msg[4]
            nick = parsed_msg[5]
            if chat != chat_alias:
                chat = "{} ({})".format(chat_alias, chat)

        # log to backend conversation
        text = "account {} chat: {} {} {}".format(acc_id, ctype, chat, nick)
        self.conversation.log("nuqql", text)

    def handle_account_msg(self, parsed_msg):
        """
        Handle Account message
        """

        # "account", acc_id, acc_alias, acc_prot, acc_user, acc_status
        # msg_type = parsed_msg[0]
        acc_id = parsed_msg[1]
        acc_alias = parsed_msg[2]
        acc_prot = parsed_msg[3]
        acc_user = parsed_msg[4]
        acc_status = parsed_msg[5]

        # output account
        text = "account {0} ({1}) {2} {3} {4}.".format(acc_id, acc_alias,
                                                       acc_prot, acc_user,
                                                       acc_status)
        self.conversation.log("nuqql", text)

        # do not add account if it already exists
        if acc_user in self.accounts:
            return

        # new account, add it
        acc = Account(acc_id, acc_prot, acc_user)
        self.accounts[acc.name] = acc

        # collect buddies from backend
        text = "Collecting buddies for {0} account {1}: {2}.".format(
            acc.type, acc.aid, acc.name)
        self.conversation.log("nuqql", text)
        acc.buddies_update = time.time()
        self.client.send_buddies(acc.aid)

        # collect messages from backend
        text = "Collecting messages for {0} account {1}: {2}.".format(
            acc.type, acc.aid, acc.name)
        self.conversation.log("nuqql", text)
        self.client.send_collect(acc.aid)

        # if there is a global_status, set account status to it
        status = NuqqlBackend.read_global_status()
        if status != "":
            self.client.send_status_set(acc_id, status)

    def handle_buddy_msg(self, parsed_msg):
        """
        Handle Buddy message
        """

        # get message parts
        # msg_type = parsed_msg[0]
        acc_id = parsed_msg[1]
        status = parsed_msg[2]
        name = parsed_msg[3]
        alias = parsed_msg[4]

        # if there is no alias, just use name
        if alias == "":
            alias = name

        # handle buddy update
        for account in self.accounts.values():
            if account.aid == acc_id:
                account.update_buddy(self, name, alias, status)
                return

    def update_buddies(self):
        """
        Update buddies of this account
        """

        # update buddies
        for acc in self.accounts.values():
            if acc.update_buddies():
                self.client.send_buddies(acc.aid)

    def get_account(self, account_id):
        """
        Get account with specified account id
        """

        for acc in self.accounts.values():
            if acc.aid == account_id:
                return acc

        return None

    def stop(self):
        """
        Stop the backend, Note: changes BACKENDS
        """

        # print to main window
        log_msg = "Stopping client and server for backend \"{0}\".".format(
            self.name)
        nuqql.conversation.log_main_window(log_msg)

        # stop client and server
        self.stop_client()
        self.stop_server()

        # remove backend from backends dict
        del BACKENDS[self.name]  # changes BACKENDS, be carefull

        # remove conversation and update list window
        nuqql.conversation.remove_backend_conversations(self)


class NuqqlBackend(Backend):
    """
    Class for the nuqql dummy backend
    """

    def _handle_nuqql_global_status(self, parts):
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
            self._handle_nuqql_global_status_set(parts[1:])
        elif sub_command == "get":
            self._handle_nuqql_global_status_get()

    def _handle_nuqql_global_status_set(self, status):
        """
        Handle nuqql command: global-status set
        Set status and store it in global_status file
        """

        # only use the first word as status
        if not status or status[0] == "":
            return
        status = status[0]

        # write status
        self._write_global_status(status)

        # set status in all backends and their accounts
        for backend in BACKENDS.values():
            for acc in backend.accounts.values():
                backend.client.send_status_set(acc.aid, status)

        # log message
        msg = "global-status: " + status
        self.conversation.log("nuqql", msg)

    def _handle_nuqql_global_status_get(self):
        """
        Handle nuqql command: global-status get
        Read status from global_status file
        """

        # read status
        status = self.read_global_status()
        if status == "":
            return

        # log message
        msg = "global-status: " + status
        self.conversation.log("nuqql", msg)

    @staticmethod
    def _write_global_status(status):
        """
        Write global status to global_status file
        """

        # write status to file
        global_status_dir = str(Path.home()) + "/.config/nuqql"
        Path(global_status_dir).mkdir(parents=True, exist_ok=True)
        global_status_file = global_status_dir + "/global_status"
        line = status + "\n"
        lines = []
        lines.append(line)
        with open(global_status_file, "w+") as status_file:
            status_file.writelines(lines)

    @staticmethod
    def read_global_status():
        """
        Read global status from global_status file
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
                    return ""
                return status[0]
        except FileNotFoundError:
            return ""

    @staticmethod
    def _handle_stop(parts):
        """
        Handle stop command, stop a backend
        """

        if not parts:
            return

        backend_name = parts[0]
        if backend_name in BACKENDS:
            BACKENDS[backend_name].stop()

    def handle_nuqql_command(self, msg):
        """
        Handle a nuqql command (from the nuqql conversation)
        """

        # parse message
        parts = msg.split()
        if not parts:
            return

        # check command and call helper functions
        command_map = {
            "global-status": self._handle_nuqql_global_status,
            "stop": self._handle_stop,
        }
        command = parts[0]
        if command in command_map:
            command_map[command](parts[1:])


##################
# Helper Classes #
##################

class Account:
    """
    Class for Accounts
    """

    def __init__(self, aid, prot, user):
        self.aid = aid
        self.name = user
        self.type = prot
        self.buddies = []
        self.buddies_update = 0

    def update_buddies(self):
        """
        Update the buddy list of this account.
        Return True if an update is pending, False otherwise.
        """

        # update only once every BUDDY_UPDATE_TIMER seconds
        if time.time() - self.buddies_update <= BUDDY_UPDATE_TIMER:
            return False
        self.buddies_update = time.time()

        # remove buddies, that have not been updated for a while
        for rem in [buddy for buddy in self.buddies if not buddy.updated]:
            nuqql.ui.remove_buddy(rem)
        self.buddies = [buddy for buddy in self.buddies if buddy.updated]

        # set update pending in buddy
        for buddy in self.buddies:
            buddy.updated = False

        return True

    def update_buddy(self, backend, name, alias, status):
        """
        Update a single buddy of this account. Could be a new buddy.
        """

        # look for existing buddy
        for buddy in self.buddies:
            if buddy.name == name:
                if buddy.update(status, alias):
                    # tell ui about the update
                    nuqql.ui.update_buddy(buddy)

                # found existing buddy; stop here
                return

        # new buddy
        new_buddy = Buddy(backend, self, name)
        new_buddy.update(status, alias)
        self.buddies.append(new_buddy)

        # tell ui there is a new buddy
        nuqql.ui.add_buddy(new_buddy)


class Buddy:
    """
    Class for Buddies
    """

    def __init__(self, backend, account, name):
        self.backend = backend
        self.account = account
        self.name = name
        self.alias = name
        self.status = "off"     # use short status name
        self.updated = True

    # dictionary for mapping status names to shorter version (key: lower case)
    status_map = {
        "offline": "off",
        "available": "on",
        "away": "afk",
        "group_chat": "grp",
        "group_chat_invite": "grp_invite",
    }

    def set_status(self, status):
        """
        Set status of buddy; convert status to something shorter
        """

        try:
            self.status = Buddy.status_map[status.lower()]
        except KeyError:
            self.status = status

    def update(self, status, alias):
        """
        Update Buddy
        """

        # save old status and alias to check if buddy has changed
        old_status = self.status
        old_alias = self.alias

        # set new values
        self.updated = True
        self.set_status(status)
        self.alias = alias

        # check if buddy has changed
        if old_status != self.status or old_alias != self.alias:
            return True

        # has not changed
        return False


#####################
# Parsing functions #
#####################

def parse_error_msg(orig_msg):
    """
    Parse "error" message received from backend

    Format:
        "error: %s\r\n"
    """

    error = orig_msg[7:]
    return "error", error


def parse_info_msg(orig_msg):
    """
    Parse "info" message received from backend

    Format:
        "info: %s\r\n"
    """

    info = orig_msg[6:]
    return "info", info


def parse_account_msg(orig_msg):
    """
    Parse "account" message received from backend

    Format:
        "account: %d %s %s %s [%s]\r\n"
    """

    orig_msg = orig_msg[9:]
    part = orig_msg.split(" ")
    acc_id = part[0]
    acc_alias = part[1]
    acc_prot = part[2].lower()
    acc_user = part[3]
    acc_status = part[4]    # ignore [ and ] for now
    return "account", acc_id, acc_alias, acc_prot, acc_user, acc_status


def parse_collect_msg(orig_msg):
    """
    Parse "collect" message received from backend
    """

    # collect response and message have the same message format
    return parse_message_msg(orig_msg)


def parse_message_msg(orig_msg):
    """
    Parse "message" message received from backend
    """

    orig_msg = orig_msg[9:]
    part = orig_msg.split(" ")
    acc = part[0]
    acc_name = part[1]
    tstamp = part[2]
    sender = part[3]
    msg = " ".join(part[4:])
    msg = "\n".join(re.split("<br/>", msg, flags=re.IGNORECASE))
    msg = html.unescape(msg)

    return "message", acc, acc_name, int(tstamp), sender, msg


def parse_buddy_msg(orig_msg):
    """
    Parse "buddy" message received from backend
    """

    orig_msg = orig_msg[7:]
    # <acc> status: <Offline/Available> name: <name> alias: <alias>
    part = orig_msg.split(" ")
    acc = part[0]
    status = part[2]
    name = part[4]
    alias = part[6]
    return "buddy", acc, status, name, alias


def parse_status_msg(orig_msg):
    """
    Parse "status" message received from backend
    """

    orig_msg = orig_msg[8:]
    # account <acc> status: <status>
    part = orig_msg.split(" ")
    acc = part[1]
    status = part[3]

    return "status", acc, status


def parse_chat_msg(orig_msg):
    """
    Parse "chat" message received from backend
    """

    orig_msg = orig_msg[6:]
    # list: <acc> <chat> <chat_alias> <nick>
    # user: <acc> <chat> <user> <user_alias> <status>
    part = orig_msg.split(" ")
    if len(part) < 5:
        # TODO: return a parsing error or something similar?
        return ("", )

    # common entries
    ctype = part[0]
    acc = part[1]
    chat = part[2]

    # list message
    if ctype == "list:":
        chat_alias = part[3]
        nick = part[4]
        return "chat", ctype, acc, chat, chat_alias, nick

    # user message
    if ctype == "user:" and len(part) >= 6:
        user = part[3]
        user_alias = part[4]
        status = part[5]
        return "chat", ctype, acc, chat, user, user_alias, status

    # msg message
    # TODO: remove duplicate code?
    if ctype == "msg:" and len(part) >= 6:
        tstamp = part[3]
        sender = part[4]
        msg = " ".join(part[5:])
        msg = "\n".join(re.split("<br/>", msg, flags=re.IGNORECASE))
        msg = html.unescape(msg)
        return "chat", ctype, acc, chat, int(tstamp), sender, msg

    return ("", )


# dictionary for parsing functions, used by parse_msg()
PARSE_FUNCTIONS = {
    "message:": parse_message_msg,
    "collect:": parse_collect_msg,
    "buddy:": parse_buddy_msg,
    "account:": parse_account_msg,
    "status:": parse_status_msg,
    "chat:": parse_chat_msg,
    "info:": parse_info_msg,
    "error:": parse_error_msg,
}


def parse_msg(orig_msg):
    """
    Parse message received from backend,
    calls more specific parsing functions
    """

    # extract message type and then call respectice parsing function
    msg_type = orig_msg.split(maxsplit=1)[0]
    try:
        return PARSE_FUNCTIONS[msg_type](orig_msg)
    except KeyError:
        # return this as parsing error
        acc = "-1"
        acc_name = "error"
        tstamp = int(time.time())
        sender = "<backend>"
        msg = "Error parsing message: " + orig_msg
        return "parsing error", acc, acc_name, tstamp, sender, msg


####################
# HELPER FUNCTIONS #
####################

def update_buddies():
    """
    Helper for updating buddies on all backends
    """

    for backend in dict(BACKENDS).values():
        backend.update_buddies()


def handle_network():
    """
    Helper for handling network events on all backends
    """

    for backend in dict(BACKENDS).values():
        backend.handle_network()


def start_backend(backend_name, backend_exe, backend_path, backend_cmd_fmt,
                  backend_sockfile):
    """
    Helper for starting a backend
    """

    # check if backend exists in path
    exe = shutil.which(backend_exe, path=os.getcwd())
    if exe is None:
        exe = shutil.which(backend_exe)
    if exe is None:
        # does not exist, stop here
        return

    backend_cmd = backend_cmd_fmt.format(exe, backend_path)

    backend = Backend(backend_name)
    backend.start_server(cmd=backend_cmd, path=backend_path)
    backend.init_client(sock_file=backend_sockfile)

    BACKENDS[backend_name] = backend

    # add conversation and show it in list window
    conv = nuqql.conversation.BackendConversation(backend, None, backend.name)
    conv.create_windows()
    nuqql.conversation.CONVERSATIONS.append(conv)
    backend.conversation = conv
    conv.wins.list_win.redraw()


def start_purpled():
    """
    Helper for starting the "purpled" backend
    """

    # check if purpled exists in path
    exe = shutil.which("purpled", path=os.getcwd())
    if exe is None:
        exe = shutil.which("purpled")
    if exe is None:
        # does not exist, stop here
        return

    ###########
    # purpled #
    ###########

    backend_name = "purpled"
    backend_exe = "purpled"
    backend_path = str(Path.home()) + "/.config/nuqql/backend/purpled"
    backend_cmd_fmt = "{0} -u -w{1}"
    backend_sockfile = backend_path + "/purpled.sock"

    start_backend(backend_name, backend_exe, backend_path, backend_cmd_fmt,
                  backend_sockfile)


def start_based():
    """
    Helper for starting the "based" backend
    """

    ###############
    # nuqql-based #
    ###############

    backend_name = "based"
    backend_exe = "based.py"
    backend_path = str(Path.home()) + "/.config/nuqql/backend/based"
    backend_cmd_fmt = "{0} --af unix --dir {1} --sockfile based.sock"
    backend_sockfile = backend_path + "/based.sock"

    start_backend(backend_name, backend_exe, backend_path, backend_cmd_fmt,
                  backend_sockfile)


def start_slixmppd():
    """
    Helper for starting the "slixmppd" backend
    """

    ##################
    # nuqql-slixmppd #
    ##################

    backend_name = "slixmppd"
    backend_exe = "slixmppd.py"
    backend_path = str(Path.home()) + "/.config/nuqql/backend/slixmppd"
    backend_cmd_fmt = "{0} --af unix --dir {1} --sockfile slixmppd.sock"
    backend_sockfile = backend_path + "/slixmppd.sock"

    start_backend(backend_name, backend_exe, backend_path, backend_cmd_fmt,
                  backend_sockfile)


def start_matrixd():
    """
    Helper for starting the "matrixd" backend
    """

    ##################
    # nuqql-matrixd #
    ##################

    backend_name = "matrixd"
    backend_exe = "matrixd.py"
    backend_path = str(Path.home()) + "/.config/nuqql/backend/matrixd"
    backend_cmd_fmt = "{0} --af unix --dir {1} --sockfile matrixd.sock"
    backend_sockfile = backend_path + "/matrixd.sock"

    start_backend(backend_name, backend_exe, backend_path, backend_cmd_fmt,
                  backend_sockfile)


def start_backend_clients():
    """
    Helper for starting all backend clients
    """

    # give backend servers some time
    time.sleep(BACKENDS_WAIT_TIME)

    for backend in dict(BACKENDS).values():
        # let user know we are connecting
        log_msg = "Starting client for backend \"{0}\".".format(backend.name)
        nuqql.conversation.log_main_window(log_msg)

        # start backend client and connect to backend server
        backend.start_client()

        # make sure the connection to the backend was successful
        if not backend.client.sock:
            log_msg = "Could not connect to backend \"{0}\".".format(
                backend.name)
            nuqql.conversation.log_main_window(log_msg)
            backend.stop()
            continue

        # request accounts from backend
        backend.client.send_accounts()

        # log it
        log_msg = "Collecting accounts for \"{0}\".".format(backend.name)
        backend.conversation.log("nuqql", log_msg)


def start_nuqql():
    """
    Start the nuqql dummy backend
    """

    # create backend
    backend = NuqqlBackend("nuqql")

    # add conversation and show it in list window
    conv = nuqql.conversation.NuqqlConversation(backend, None, backend.name)
    conv.create_windows()
    backend.conversation = conv


def start_backends():
    """
    Helper for starting all backends
    """

    # start nuqql dummy backend
    start_nuqql()

    # start backends
    nuqql.conversation.log_main_window("Starting backends.")
    start_purpled()
    start_based()
    start_slixmppd()
    start_matrixd()

    # start backend clients
    start_backend_clients()


def stop_backends():
    """
    Helper for stopping all backends
    """

    for backend in dict(BACKENDS).values():
        backend.stop()  # changes BACKENDS
