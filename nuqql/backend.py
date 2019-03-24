################
# NETWORK PART #
################

import subprocess
import datetime
import socket
import select
import time
import html

import nuqql.ui

from pathlib import Path

# network buffer
BUFFER_SIZE = 4096

# update buddies only every BUDDY_UPDATE_TIMER seconds
BUDDY_UPDATE_TIMER = 5

# dictionary for all active backends
backends = {}


class Backend:
    """
    Class for backends. Allows starting server processes and connecting to
    (self-started or externally started) servers
    """

    def __init__(self, name, external=False, cmd="", path="",
                 af=socket.AF_UNIX, ip="127.0.0.1", port=32000, sock_file=""):
        # backend
        self.name = name
        self.accounts = {}

        # server
        self.external = external
        self.proc = None
        self.server_path = path
        self.server_cmd = cmd

        # client
        self.sock = None
        self.sock_af = af
        self.sock_file = sock_file
        self.ip = ip
        self.port = port
        self.buffer = ""

        # self.collect_acc = -1

    def startServer(self):
        # do not start a server process if backend is external
        if self.external:
            return

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

    def stopServer(self):
        # do not stop anything if the backend is external
        if self.external:
            return

        # stop running server
        self.proc.terminate()

    def initClient(self):
        # open sockets and connect
        if self.sock_af == socket.AF_INET:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.ip, self.port))
        elif self.sock_af == socket.AF_UNIX:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(self.sock_file)

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
        # collect all messages since time 0
        # TODO: only works as intended if we spawn our own purpled daemon at
        # nuqql's startup, FIXME?
        msg = "account {0} collect 0\r\n".format(account)
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

    def handleNetwork(self, conversation, list_win, log_win):
        msg = self.readClient()
        if msg is None:
            return
        # TODO: do not ignore account name
        # TODO: it's not even an acc_name, it's the name of the buddy? FIXME
        msg = self.parseMsg(msg)
        msg_type = msg[0]

        # handle info message or error message
        if msg_type == "info" or msg_type == "error":
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            text = msg_type + ": " + msg[1]
            log_msg = nuqql.ui.LogMessage(log_win, now, None, "nuqql", True,
                                          text)
            log_win.add(log_msg)
            return

        # handle account message
        if msg_type == "account":
            self.handleAccountMsg(log_win, msg)
            return

        # handle buddy messages
        if msg_type == "buddy":
            self.handleBuddyMsg(list_win, msg)
            return

        # handle normal messages and error messages
        # TODO: handle error messages somewhere else?
        if msg_type == "message" or msg_type == "error":
            (msg_type, acc, acc_name, tstamp, sender, msg) = msg

        # account specific message parsing
        for tmp_acc_name, tmp_acc in self.accounts.items():
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
                # conv.log_win.add(tstamp + " " + getShortName(sender) + \
                #         ": " +msg)
                log_msg = nuqql.ui.LogMessage(conv.log_win, tstamp,
                                              conv.account, conv.name, True,
                                              msg)
                conv.log_win.add(log_msg)
                # if window is not already active notify user
                if not conv.input_win.active:
                    list_win.notify(acc, sender)
                return

        # create a new conversation if buddy exists
        # TODO: can we add some helper functions?
        for buddy in list_win.list:
            if buddy.account.id == acc and buddy.name == sender:
                c = nuqql.ui.Conversation(list_win.superWin, buddy.account,
                                          buddy.name)
                c.input_win.active = False
                c.log_win.active = False
                conversation.append(c)
                # c.log_win.add(tstamp + " " + sender + " --> " + msg)
                # c.log_win.add(tstamp + " " + getShortName(sender) + \
                #         ": " + msg)
                log_msg = nuqql.ui.LogMessage(c.log_win, tstamp, c.account,
                                              c.name, True, msg)
                c.log_win.add(log_msg)
                list_win.notify(acc, sender)
                return

        # nothing found, log to main window
        # log_win.add(tstamp + " " + sender + " --> " + msg)
        log_msg = nuqql.ui.LogMessage(log_win, tstamp, None, sender, True, msg)
        log_win.add(log_msg)

    def handleAccountMsg(self, log_win, msg):
        """
        Handle Account message
        """

        # "account", acc_id, acc_alias, acc_prot, acc_user, acc_status
        (msg_type, acc_id, acc_alias, acc_prot, acc_user, acc_status) = msg

        # output account
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = "account {0} ({1}) {2} {3} {4}.".format(acc_id, acc_alias,
                                                       acc_prot, acc_user,
                                                       acc_status)
        log_msg = nuqql.ui.LogMessage(log_win, now, None, "nuqql", True, text)
        log_win.add(log_msg)

        # do not add account if it already exists
        if acc_user in self.accounts:
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
        self.accounts[acc.name] = acc

        # collect buddies from purpled
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = "Collecting buddies for {0} account {1}: {2}.".format(
            acc.type, acc.id, acc.name)
        log_msg = nuqql.ui.LogMessage(log_win, now, None, "nuqql", True, text)
        log_win.add(log_msg)
        acc.buddies_update = time.time()
        self.buddiesClient(acc.id)

        # collect messages from purpled
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = "Collecting messages for {0} account {1}: {2}.".format(
            acc.type, acc.id, acc.name)
        log_msg = nuqql.ui.LogMessage(log_win, now, None, "nuqql", True, text)
        log_win.add(log_msg)
        self.collectClient(acc.id)

    def handleBuddyMsg(self, list_win, msg):
        """
        Handle Buddy message
        """

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
        for acc_name, account in self.accounts.items():
            if account.id == acc:
                new_buddy = Buddy(account, name)
                new_buddy.status = status
                new_buddy.alias = alias
                list_win.add(new_buddy)
                list_win.redraw()
                return

    def updateBuddies(self, log_win):
        """
        Update buddies of this account
        """
        # update buddies
        # TODO: move account list to backend?
        for acc in self.accounts.values():
            # update only once every BUDDY_UPDATE_TIMER seconds
            if time.time() - acc.buddies_update <= BUDDY_UPDATE_TIMER:
                continue
            acc.buddies_update = time.time()
            self.buddiesClient(acc.id)


##################
# Helper Classes #
##################

class Account:
    pass


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


####################
# HELPER FUNCTIONS #
####################

def updateBuddies(log_win):
    """
    Helper for updating buddies on all backends
    """

    for backend in backends.values():
        backend.updateBuddies(log_win)


def handleNetwork(conversation, list_win, log_win):
    """
    Helper for handling network events on all backends
    """

    for backend in backends.values():
        backend.handleNetwork(conversation, list_win, log_win)


def initBackends():
    """
    Helper for starting all backends
    """

    # purpled
    purpled_path = str(Path.home()) + "/.config/nuqql/backend/purpled"
    purpled_cmd = "purpled -u -w" + purpled_path
    purpled_sock_file = purpled_path + "/purpled.sock"

    purpled = Backend("purpled", cmd=purpled_cmd, path=purpled_path,
                      sock_file=purpled_sock_file)

    backends["purpled"] = purpled


def stopBackends():
    """
    Helper for stopping all backends
    """
    for backend in backends.values():
        backend.exitClient()
        backend.stopServer()
