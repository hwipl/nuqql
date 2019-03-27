"""
Backend part of nuqql.
"""

################
# NETWORK PART #
################

import subprocess
import datetime
import socket
import select
import shutil
import time
import html
import os

from pathlib import Path

import nuqql.ui

# network buffer
BUFFER_SIZE = 4096

# update buddies only every BUDDY_UPDATE_TIMER seconds
BUDDY_UPDATE_TIMER = 5

# dictionary for all active backends
BACKENDS = {}


class BackendServer:
    """
    Class for a backend's server process
    """

    def __init__(self, cmd="", path=""):
        # server
        self.proc = None
        self.server_path = path
        self.server_cmd = cmd

    def start(self):
        """
        Start the backend's server process
        """

        # make sure server's working directory exists
        Path(self.server_path).mkdir(parents=True, exist_ok=True)

        # start server process
        self.proc = subprocess.Popen(
            self.server_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,     # dont send SIGINT from nuqql to
                                        # subprocess
        )
        # give it some time
        time.sleep(1)

    def stop(self):
        """
        Stop the backend's server process
        """

        # stop running server
        self.proc.terminate()


class BackendClient:
    """
    Class for a backend's client connection to a
    local or remote backend server process
    """

    def __init__(self, sock_af=socket.AF_UNIX, ip_addr="127.0.0.1", port=32000,
                 sock_file=""):
        # client
        self.sock = None
        self.sock_af = sock_af
        self.sock_file = sock_file
        self.ip_addr = ip_addr
        self.port = port
        self.buffer = ""

    def start(self):
        """
        Start the backend's client
        """

        # open sockets and connect
        if self.sock_af == socket.AF_INET:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.ip_addr, self.port))
        elif self.sock_af == socket.AF_UNIX:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(self.sock_file)

    def stop(self):
        """
        Stop the backend's client
        """

        self.sock.close()

    def read(self):
        """
        Read from the client connection
        """

        reads, unused_writes, errs = select.select([self.sock, ], [],
                                                   [self.sock, ], 0)
        if self.sock in errs:
            # something is wrong
            return None

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

    def send_command(self, cmd):
        """
        Send a command over the client connection
        """

        # TODO: do more?
        msg = cmd + "\r\n"
        msg = msg.encode()
        self.sock.send(msg)

    def send_msg(self, account, buddy, msg):
        """
        Send a regular message over the client connection
        """

        prefix = "account {0} send {1} ".format(account, buddy)
        msg = html.escape(msg)
        msg = "<br>".join(msg.split("\n"))
        msg = prefix + msg + "\r\n"
        msg = msg.encode()
        self.sock.send(msg)

    def send_collect(self, account):
        """
        Send "collect" message over the client connection,
        which collects all messages received by the backend
        """

        # collect all messages since time 0
        # TODO: only works as intended if we spawn our own purpled daemon at
        # nuqql's startup, FIXME?
        msg = "account {0} collect 0\r\n".format(account)
        msg = msg.encode()
        # self.collect_acc = account
        self.sock.send(msg)

    def send_buddies(self, account):
        """
        Send "buddies" message over the client connection,
        which retrieves all buddies of the specified account from the backend
        """

        msg = "account {0} buddies\r\n".format(account)
        msg = msg.encode()
        self.sock.send(msg)

    def send_accounts(self):
        """
        Send "account list" message over the client connection,
        which retrieves all accounts from the backend
        """

        msg = "account list\r\n"
        msg = msg.encode()
        self.sock.send(msg)


class Backend:
    """
    Class for backends. Allows starting server processes and connecting to
    (self-started or externally started) servers
    """

    def __init__(self, name):
        # backend
        self.name = name
        self.accounts = {}
        # conversation for communication with the backend. TODO: check
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

    def start_client(self, sock_af=socket.AF_UNIX, ip_addr="127.0.0.1",
                     port=32000, sock_file=""):
        """
        Add a client to this backend and start it
        """

        self.client = BackendClient(sock_af, ip_addr, port, sock_file)
        self.client.start()

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

        # TODO: do not ignore account name
        # TODO: it's not even an acc_name, it's the name of the buddy? FIXME
        # msg_type = msg[0]
        acc_id = parsed_msg[1]
        # acc_name = msg[2]
        tstamp = parsed_msg[3]
        sender = parsed_msg[4]
        msg = parsed_msg[5]

        # account specific message parsing
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
                    sender = sender.split("/")[0]
                    break

        # let ui handle the message
        nuqql.ui.handle_message(self, acc_id, tstamp, sender, msg)

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

        # handle buddy update in ui
        if nuqql.ui.update_buddy(self, acc_id, name, alias, status):
            return

        # new buddy
        for account in self.accounts.values():
            if account.aid == acc_id:
                new_buddy = Buddy(self, account, name)
                new_buddy.status = status
                new_buddy.alias = alias
                nuqql.ui.add_buddy(new_buddy)
                return

    def update_buddies(self):
        """
        Update buddies of this account
        """
        # update buddies
        for acc in self.accounts.values():
            # update only once every BUDDY_UPDATE_TIMER seconds
            if time.time() - acc.buddies_update <= BUDDY_UPDATE_TIMER:
                continue
            acc.buddies_update = time.time()
            self.client.send_buddies(acc.aid)


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


class Buddy:
    """
    Class for Buddies
    """

    def __init__(self, backend, account, name):
        self.backend = backend
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
        return self.get_key() < other.get_key()

    def get_key(self):
        """
        Get key for comparison of Buddy instances
        """

        return self.status + self.name


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
    msg = "\n".join(msg.split("<BR>"))
    msg = html.unescape(msg)
    tstamp = datetime.datetime.fromtimestamp(int(tstamp))
    # tstamp = tstamp.strftime("%Y-%m-%d %H:%M:%S")
    # TODO: move timestamp conversion to caller?
    tstamp = tstamp.strftime("%H:%M:%S")
    return "message", acc, acc_name, tstamp, sender, msg


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


# dictionary for parsing functions, used by parse_msg()
PARSE_FUNCTIONS = {
    "message:": parse_message_msg,
    "collect:": parse_collect_msg,
    "buddy:": parse_buddy_msg,
    "account:": parse_account_msg,
    "into:": parse_info_msg,
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
        tstamp = "never"
        sender = "purpled"
        msg = "Error parsing message: " + orig_msg
        return "parsing error", acc, acc_name, tstamp, sender, msg


####################
# HELPER FUNCTIONS #
####################

def update_buddies():
    """
    Helper for updating buddies on all backends
    """

    for backend in BACKENDS.values():
        backend.update_buddies()


def handle_network():
    """
    Helper for handling network events on all backends
    """

    for backend in BACKENDS.values():
        backend.handle_network()


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

    purpled_path = str(Path.home()) + "/.config/nuqql/backend/purpled"
    purpled_cmd = "{0} -u -w{1}".format(exe, purpled_path)
    purpled_sockfile = purpled_path + "/purpled.sock"

    purpled = Backend("purpled")
    purpled.start_server(cmd=purpled_cmd, path=purpled_path)
    purpled.start_client(sock_file=purpled_sockfile)

    BACKENDS["purpled"] = purpled

    # pseudo account
    account = Account("0", "nuqql", "purpled")

    # add pseudo buddy for purpled
    new_buddy = Buddy(purpled, account, "purpled")
    new_buddy.status = "backend"
    new_buddy.alias = "purpled"
    # add it to list_win
    nuqql.ui.add_buddy(new_buddy)

    # add conversation for purpled
    conv = nuqql.ui.Conversation(purpled, account, purpled.name,
                                 ctype="backend")
    nuqql.ui.CONVERSATIONS.append(conv)
    purpled.conversation = conv

    # request accounts from backend
    purpled.client.send_accounts()

    # log it
    log_msg = "Collecting accounts for \"{0}\".".format(purpled.name)
    nuqql.ui.log_main_window(log_msg)


def start_based():
    """
    Helper for starting the "based" backend
    """

    # check if purpled exists in path
    exe = shutil.which("based.py", path=os.getcwd())
    if exe is None:
        exe = shutil.which("based.py")
    if exe is None:
        # does not exist, stop here
        return

    ###############
    # nuqql-based #
    ###############

    based_path = str(Path.home()) + "/.config/nuqql/backend/based"
    based_cmd = "{0} --af unix --dir {1} --sockfile based.sock".format(
        exe, based_path)
    based_sockfile = based_path + "/based.sock"

    based = Backend("based")
    based.start_server(cmd=based_cmd, path=based_path)
    based.start_client(sock_file=based_sockfile)

    BACKENDS["based"] = based

    # pseudo account
    account = Account("1", "nuqql", "based")

    # add pseudo buddy
    new_buddy = Buddy(based, account, "based")
    new_buddy.status = "backend"
    new_buddy.alias = "based"
    # add it to list_win
    nuqql.ui.add_buddy(new_buddy)

    # add conversation
    conv = nuqql.ui.Conversation(based, account, based.name, ctype="backend")
    nuqql.ui.CONVERSATIONS.append(conv)
    based.conversation = conv

    # request accounts from backend
    based.client.send_accounts()

    # log it
    log_msg = "Collecting accounts for \"{0}\".".format(based.name)
    nuqql.ui.log_main_window(log_msg)


def start_backends():
    """
    Helper for starting all backends
    """

    start_purpled()
    start_based()


def stop_backends():
    """
    Helper for stopping all backends
    """

    for backend in BACKENDS.values():
        backend.stop_client()
        backend.stop_server()
