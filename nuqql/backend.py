"""
Backend part of nuqql.
"""

################
# NETWORK PART #
################

import socket
import shutil
import time
import os

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import nuqql.conversation
import nuqql.ui
import nuqql.parse

from nuqql.backendserver import BackendServer
from nuqql.backendclient import BackendClient
from nuqql.account import Account

# dictionary for all active backends
BACKENDS: Dict[str, "Backend"] = {}

# how long should we wait for backends (in seconds) before starting clients
BACKENDS_WAIT_TIME = 1

# filenames that should not get started as backends
BACKEND_BLACKLIST = ["nuqql-keys", "nuqql-based"]

# disable the python backends' own history?
BACKEND_DISABLE_HISTORY = True


class Backend:
    """
    Class for backends. Allows starting server processes and connecting to
    (self-started or externally started) servers
    """

    def __init__(self, name: str) -> None:
        # backend
        self.name = name
        self.accounts: Dict[str, Account] = {}
        # conversation for communication with the backend.
        self.conversation: Optional[nuqql.conversation.Conversation] = None

        # server
        self.server: Optional[BackendServer] = None

        # client
        self.client: Optional[BackendClient] = None

        # self.collect_acc = -1

    def start_server(self, cmd: str, path: str) -> None:
        """
        Add a server to this backend and start it
        """

        self.server = BackendServer(cmd, path)
        self.server.start()

    def stop_server(self) -> None:
        """
        Stop the server of this backend
        """

        if self.server:
            self.server.stop()

    def start_client(self) -> None:
        """
        Start the backend's client
        """

        if self.client:
            self.client.start()

    def init_client(self, sock_af: "socket.AddressFamily" = socket.AF_UNIX,
                    ip_addr: str = "127.0.0.1", port: int = 32000,
                    sock_file: str = "") -> None:
        """
        Add a client to this backend
        """

        self.client = BackendClient(sock_af, ip_addr, port, sock_file)
        self.client.backend = self

    def stop_client(self) -> None:
        """
        Stop the client of this backend
        """

        if self.client:
            self.client.stop()

    def handle_network(self) -> None:
        """
        Try to read from the client connection and handle messages.
        """

        # try to read message
        if not self.client:
            return
        msg = self.client.read()
        if msg is None:
            return

        # parse it
        parsed_msg = nuqql.parse.parse_msg(msg)
        msg_type = parsed_msg[0]

        # handle info message or error message
        if msg_type in ("info", "error"):
            text = msg_type + ": " + parsed_msg[1]
            if self.conversation:
                self.conversation.log("nuqql", text)
            return

        # handle account message
        if msg_type == "account":
            self.handle_account_msg(parsed_msg)
            return

        # handle status message
        if msg_type == "status":
            text = "account {} status: {}".format(parsed_msg[1], parsed_msg[2])
            if self.conversation:
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

    def handle_message_msg(self, parsed_msg: Tuple[str, ...]) -> None:
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
                if tmp_acc.type == "xmpp":
                    sender_parts = sender.split("/")
                    sender = sender_parts[0]
                    if len(sender_parts) > 1:
                        resource = sender_parts[1]
                    break
                if tmp_acc.type == "matrix":
                    # TODO: improve?
                    sender = sender[1:].split(":")[0]
                    resource = sender
                    sender = parsed_msg[2]
                    break

        # let ui handle the message
        nuqql.ui.handle_message(self, acc_id, tstamp, sender, msg, resource)

    def handle_chat_msg(self, parsed_msg: Tuple[str, ...]) -> None:
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
                    if tmp_acc.type == "xmpp":
                        sender_parts = sender.split("/")
                        sender = sender_parts[0]
                        break
                    if tmp_acc.type == "matrix":
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
        if self.conversation:
            self.conversation.log("nuqql", text)

    def handle_account_msg(self, parsed_msg: Tuple[str, ...]) -> None:
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
        if self.conversation:
            self.conversation.log("nuqql", text)

        if not self.client:
            return

        # do not add account if it already exists
        if acc_user in self.accounts:
            return

        # new account, add it
        acc = Account(acc_id, acc_prot, acc_user)
        self.accounts[acc.name] = acc

        # collect buddies from backend
        text = "Collecting buddies for {0} account {1}: {2}.".format(
            acc.type, acc.aid, acc.name)
        if self.conversation:
            self.conversation.log("nuqql", text)
        acc.buddies_update = int(time.time())
        self.client.send_buddies(acc.aid)

        # collect messages from backend
        text = "Collecting messages for {0} account {1}: {2}.".format(
            acc.type, acc.aid, acc.name)
        if self.conversation:
            self.conversation.log("nuqql", text)
        self.client.send_collect(acc.aid)

        # if there is a global_status, set account status to it
        status = NuqqlBackend.read_global_status()
        if status != "":
            self.client.send_status_set(acc_id, status)

    def handle_buddy_msg(self, parsed_msg: Tuple[str, ...]) -> None:
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

    def update_buddies(self) -> None:
        """
        Update buddies of this account
        """

        if not self.client:
            return

        # update buddies
        for acc in self.accounts.values():
            if acc.update_buddies():
                self.client.send_buddies(acc.aid)

    def get_account(self, account_id: int) -> Optional["Account"]:
        """
        Get account with specified account id
        """

        for acc in self.accounts.values():
            if acc.aid == account_id:
                return acc

        return None

    def stop(self) -> None:
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

    def __init__(self, name: str) -> None:
        Backend.__init__(self, name)
        self.version = ""

    def _handle_nuqql_global_status(self, parts: List[str]) -> None:
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
            self._handle_nuqql_global_status_set(parts[1])
        elif sub_command == "get":
            self._handle_nuqql_global_status_get()

    def _handle_nuqql_global_status_set(self, status: str) -> None:
        """
        Handle nuqql command: global-status set
        Set status and store it in global_status file
        """

        # only use the first word as status
        if not status or status == "":
            return

        # write status
        self._write_global_status(status)

        # set status in all backends and their accounts
        for backend in BACKENDS.values():
            for acc in backend.accounts.values():
                if backend.client:
                    backend.client.send_status_set(acc.aid, status)

        # log message
        msg = "global-status: " + status
        if self.conversation:
            self.conversation.log("nuqql", msg)

    def _handle_nuqql_global_status_get(self) -> None:
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
        if self.conversation:
            self.conversation.log("nuqql", msg)

    @staticmethod
    def _write_global_status(status: str) -> None:
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
    def read_global_status() -> str:
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
    def _handle_stop(parts: List[str]) -> None:
        """
        Handle stop command, stop a backend
        """

        if not parts:
            return

        backend_name = parts[0]
        if backend_name in BACKENDS:
            BACKENDS[backend_name].stop()

    @staticmethod
    def _handle_start(parts: List[str]) -> None:
        """
        Handle start command, start a backend
        """

        if not parts:
            return

        backend_name = parts[0]
        if backend_name in BACKENDS:
            # backend already running
            return

        # try to start backend
        backend = None

        # extra check for purpled, other backends are started from PATH
        if backend_name == "purpled":
            backend = start_purpled()
        else:
            for filename in get_backends_from_path():
                # ignore "nuqql-" in filename
                if backend_name == filename[6:]:
                    backend = start_backend_from_path(filename)
                    break

        # start the backend client
        if backend:
            start_backend_client(backend)

    @staticmethod
    def _handle_restart(parts: List[str]) -> None:
        """
        Handle restart command, stop and start a backend
        """

        NuqqlBackend._handle_stop(parts)
        NuqqlBackend._handle_start(parts)

    def _handle_quit(self, _parts: List[str]) -> None:
        """
        Handle quit command, quit nuqql
        """

        if self.conversation:
            self.conversation.wins.input_win.state.active = False
            self.conversation.wins.list_win.state.active = False

    def _handle_version(self, _parts: List[str]) -> None:
        """
        Handle version command, print nuqql version
        """

        # log message
        msg = f"version: nuqql v{self.version}"
        if self.conversation:
            self.conversation.log("nuqql", msg)

    def handle_nuqql_command(self, msg: str) -> None:
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
            "start": self._handle_start,
            "restart": self._handle_restart,
            "quit": self._handle_quit,
            "version": self._handle_version,
        }
        command = parts[0]
        if command in command_map:
            command_map[command](parts[1:])


####################
# HELPER FUNCTIONS #
####################

def update_buddies() -> None:
    """
    Helper for updating buddies on all backends
    """

    for backend in dict(BACKENDS).values():
        backend.update_buddies()


def handle_network() -> None:
    """
    Helper for handling network events on all backends
    """

    for backend in dict(BACKENDS).values():
        backend.handle_network()


def start_backend(backend_name: str, backend_exe: str, backend_path: str,
                  backend_cmd_fmt: str,
                  backend_sockfile: str) -> Optional[Backend]:
    """
    Helper for starting a backend
    """

    # check if backend exists in path
    exe = shutil.which(backend_exe, path=os.getcwd())
    if exe is None:
        exe = shutil.which(backend_exe)
    if exe is None:
        # does not exist, stop here
        return None

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

    # return the backend
    return backend


def start_purpled() -> Optional[Backend]:
    """
    Helper for starting the "purpled" backend
    """

    # check if purpled exists in path
    exe = shutil.which("purpled", path=os.getcwd())
    if exe is None:
        exe = shutil.which("purpled")
    if exe is None:
        # does not exist, stop here
        return None

    ###########
    # purpled #
    ###########

    backend_name = "purpled"
    backend_exe = "purpled"
    backend_path = str(Path.home()) + "/.config/nuqql/backend/purpled"
    backend_cmd_fmt = "{0} -u -w{1}"
    backend_sockfile = backend_path + "/purpled.sock"

    return start_backend(backend_name, backend_exe, backend_path,
                         backend_cmd_fmt, backend_sockfile)


def start_backend_from_path(filename) -> Optional[Backend]:
    """
    Helper for starting a single backend found in PATH.
    """

    backend_name = filename[6:]
    backend_exe = filename
    backend_path = str(Path.home()) + f"/.config/nuqql/backend/{backend_name}"
    backend_cmd_fmt = "{0} --af unix --dir {1} --sockfile " + \
        f"{backend_name}.sock"
    if BACKEND_DISABLE_HISTORY:
        backend_cmd_fmt += " --disable-history"
    backend_sockfile = backend_path + f"/{backend_name}.sock"

    return start_backend(backend_name, backend_exe, backend_path,
                         backend_cmd_fmt, backend_sockfile)


def get_backends_from_path() -> List[str]:
    """
    Get a list of backends found in PATH.
    """

    backends: List[str] = []
    for path_dir in os.get_exec_path():
        with os.scandir(path_dir) as path:
            for entry in path:
                if entry.is_file() and \
                   entry.name.startswith("nuqql-") and \
                   entry.name not in BACKEND_BLACKLIST and \
                   entry.name not in backends:
                    backends.append(entry.name)
    return backends


def start_backends_from_path() -> None:
    """
    Helper for starting all backends found in PATH.
    These backends are expected to have the same command line arguments.
    """

    for filename in get_backends_from_path():
        start_backend_from_path(filename)


def start_backend_client(backend: Backend) -> None:
    """
    Helper for starting a single backend client
    """

    # let user know we are connecting
    log_msg = "Starting client for backend \"{0}\".".format(backend.name)
    nuqql.conversation.log_main_window(log_msg)

    # start backend client and connect to backend server
    backend.start_client()

    # make sure the connection to the backend was successful
    if not backend.client or not backend.client.sock:
        log_msg = "Could not connect to backend \"{0}\".".format(
            backend.name)
        nuqql.conversation.log_main_window(log_msg)
        backend.stop()
        return

    # request accounts from backend
    backend.client.send_accounts()

    # log it
    log_msg = "Collecting accounts for \"{0}\".".format(backend.name)
    if backend.conversation:
        backend.conversation.log("nuqql", log_msg)


def start_backend_clients() -> None:
    """
    Helper for starting all backend clients
    """

    # give backend servers some time
    time.sleep(BACKENDS_WAIT_TIME)

    for backend in dict(BACKENDS).values():
        start_backend_client(backend)


def start_nuqql(version: str) -> None:
    """
    Start the nuqql dummy backend
    """

    # create backend
    backend = NuqqlBackend("nuqql")
    backend.version = version

    # add conversation and show it in list window
    conv = nuqql.conversation.NuqqlConversation(backend, None, backend.name)
    conv.create_windows()
    backend.conversation = conv
    nuqql.conversation.log_main_window(f"Started nuqql v{version}.")


def start_backends(version: str) -> None:
    """
    Helper for starting all backends
    """

    # start nuqql dummy backend
    start_nuqql(version)

    # start backends
    nuqql.conversation.log_main_window("Starting backends.")
    start_purpled()
    start_backends_from_path()

    # start backend clients
    start_backend_clients()


def stop_backends() -> None:
    """
    Helper for stopping all backends
    """

    for backend in dict(BACKENDS).values():
        backend.stop()  # changes BACKENDS
