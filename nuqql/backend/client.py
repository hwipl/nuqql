"""
Backend client
"""

import logging
import socket
import select
import time
import html

from typing import Optional, TYPE_CHECKING

import nuqql.conversation

if TYPE_CHECKING:   # imports for typing
    # pylint: disable=cyclic-import
    from nuqql.backend import Backend

logger = logging.getLogger(__name__)

# how often should a backend client try to connect to its server and
# how long (in seconds) should a backend client sleep between retries?
CLIENT_MAX_RETRIES = 100
CLIENT_RETRY_SLEEP = 0.1

# backend error message
BACKEND_ERROR = "Error accessing backend."

# network buffer
BUFFER_SIZE = 4096


class BackendClient:
    """
    Class for a backend's client connection to a
    local or remote backend server process
    """

    def __init__(self, sock_af: "socket.AddressFamily" = socket.AF_UNIX,
                 ip_addr: str = "127.0.0.1", port: int = 32000,
                 sock_file: str = "") -> None:
        # client
        self.backend: Optional["Backend"] = None
        self.sock: Optional[socket.socket] = None
        self.sock_af = sock_af
        self.sock_file = sock_file
        self.ip_addr = ip_addr
        self.port = port
        self.buffer = ""

    def _connect(self) -> None:
        """
        Helper for connecting to the server
        """

        if self.sock_af == socket.AF_INET:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.ip_addr, self.port))
            logger.debug("connected AF_INET socket")
        elif self.sock_af == socket.AF_UNIX:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(self.sock_file)
            logger.debug("connected AF_UNIX socket")

    def start(self) -> None:
        """
        Start the backend's client
        """

        # open sockets and connect
        retries = 0
        logger.debug("starting client")
        while not self.sock and retries < CLIENT_MAX_RETRIES:
            try:
                self._connect()
            except OSError:
                self.sock = None
                retries += 1
                time.sleep(CLIENT_RETRY_SLEEP)

    def stop(self) -> None:
        """
        Stop the backend's client
        """

        logger.debug("stopping client")
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def read(self) -> Optional[str]:
        """
        Read from the client connection
        """

        if not self.sock:
            return None

        try:
            reads, unused_writes, errs = select.select([self.sock, ], [],
                                                       [self.sock, ], 0)
        except OSError:
            nuqql.conversation.log_nuqql_conv(BACKEND_ERROR)
            logger.error("read error (select)")
            if self.backend:
                self.backend.stop()
            return None

        if self.sock in errs:
            # something is wrong
            logger.error("read error (socket)")
            if self.backend:
                self.backend.stop()
            return None

        if self.sock in reads:
            # read data from socket and add it to buffer
            try:
                data = self.sock.recv(BUFFER_SIZE)
            except OSError:
                nuqql.conversation.log_nuqql_conv(BACKEND_ERROR)
                logger.error("read error (recv)")
                if self.backend:
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

        logger.debug("read message: %s", msg)
        return msg

    def _send(self, msg: str) -> None:
        """
        Helper for sending any messages and catching errors.
        """

        if not self.sock:
            return

        try:
            self.sock.sendall(msg.encode())
            logger.debug("sent message: %s", msg)
        except OSError:
            nuqql.conversation.log_nuqql_conv(BACKEND_ERROR)
            logger.error("send error")
            if self.backend:
                self.backend.stop()
            return

    def send_command(self, cmd: str) -> None:
        """
        Send a command over the client connection
        """

        msg = cmd + "\r\n"
        logger.debug("sending command: %s", msg)
        self._send(msg)

    def send_msg(self, account_id: str, buddy: str, msg: str) -> None:
        """
        Send a regular message over the client connection
        """

        prefix = "account {0} send {1} ".format(account_id, buddy)
        msg = html.escape(msg)
        msg = "<br/>".join(msg.split("\n"))
        msg = prefix + msg + "\r\n"
        logger.debug("sending message: %s", msg)
        self._send(msg)

    def send_group_msg(self, account_id: str, buddy: str, msg: str) -> None:
        """
        Send a group message over the client connection
        """

        prefix = "account {0} chat send {1} ".format(account_id, buddy)
        msg = html.escape(msg)
        msg = "<br/>".join(msg.split("\n"))
        msg = prefix + msg + "\r\n"
        logger.debug("sending group message: %s", msg)
        self._send(msg)

    def send_collect(self, account_id: str) -> None:
        """
        Send "collect" message over the client connection,
        which collects all messages received by the backend
        """

        # collect all messages since time 0
        # TODO: only works as intended if we spawn our own purpled daemon at
        # nuqql's startup, FIXME?
        msg = "account {0} collect 0\r\n".format(account_id)
        # self.collect_acc = account
        logger.debug("sending collect message: %s", msg)
        self._send(msg)

    def send_buddies(self, account_id: str) -> None:
        """
        Send "buddies" message over the client connection,
        which retrieves all buddies of the specified account from the backend
        """

        msg = "account {0} buddies\r\n".format(account_id)
        logger.debug("sending buddies message: %s", msg)
        self._send(msg)

    def send_accounts(self) -> None:
        """
        Send "account list" message over the client connection,
        which retrieves all accounts from the backend
        """

        msg = "account list\r\n"
        logger.debug("sending account list message: %s", msg)
        self._send(msg)

    def send_status_set(self, account_id: str, status: str) -> None:
        """
        Send "status set" message over client connection,
        which sets the status of the specified account of the backend
        """

        msg = "account {} status set {}\r\n".format(account_id, status)
        logger.debug("sending status set message: %s", msg)
        self._send(msg)
