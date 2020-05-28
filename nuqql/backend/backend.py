"""
Backend part of nuqql.
"""

################
# NETWORK PART #
################

import socket
import time

from pathlib import Path
from typing import Dict, Optional, Tuple

import nuqql.conversation
import nuqql.ui
import nuqql.parse

from nuqql.account import Account
from .server import BackendServer
from .client import BackendClient

# dictionary for all active backends
BACKENDS: Dict[str, "Backend"] = {}


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
        status = self.read_global_status()
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