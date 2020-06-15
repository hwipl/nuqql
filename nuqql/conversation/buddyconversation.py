"""
Buddy conversation
"""

import datetime
import logging
import urllib.parse

from typing import List, Tuple, TYPE_CHECKING

import nuqql.win

from .conversation import Conversation

if TYPE_CHECKING:   # imports for typing
    # pylint: disable=cyclic-import
    from nuqql.account import Account  # noqa
    from nuqql.backend import Backend  # noqa
    from nuqql.buddy import Buddy   # noqa

logger = logging.getLogger(__name__)


class BuddyConversation(Conversation):
    """
    Class for conversations with buddies
    """

    def __init__(self, backend: "Backend", account: "Account",
                 name: str) -> None:
        Conversation.__init__(self, backend, account, name)

        # conv already in backend or new (temporary) conv in nuqql only
        self.temporary = False

        self.peers: List["Buddy"] = []
        self.wins.list_win = nuqql.win.MAIN_WINS["list"]
        self.history.init_logger()

    def create_windows(self) -> None:
        """
        Create windows for this conversation
        """

        logger.debug("creating windows for conversation %s", self.name)

        # create standard chat windows
        log_title = "Chat log with {0}".format(self.name)
        input_title = "Message to {0}".format(self.name)
        self._create_windows_common(log_title, input_title)

        # try to read old messages from message history
        self.history.init_log_from_file()

    def get_name(self) -> str:
        """
        Get the name of the conversation, depending on type
        """

        if self.peers:
            peer = self.peers[0]
            notify = self._get_name_notification()
            # unquote the alias, e.g., remove %20 for whitespace
            alias = urllib.parse.unquote(peer.alias)
            return "{0}[{1}] {2}".format(notify, peer.status, alias)
        return "{0}[{1}] {2}".format(notify, "off", self.name)

    def get_key(self) -> Tuple:
        """
        Get a key for sorting this conversation
        """

        # defaults
        sort_notify = 0 - self.notification
        sort_used = 0.0
        sort_type = 0
        sort_status = 0
        sort_name = self.name

        # get sort key from config
        config = nuqql.config.get("conversations")
        sort_key = config["sort_key"]

        if self.peers:
            peer = self.peers[0]
            if peer.status != "off" and sort_key in self.stats:
                sort_used = 0 - self.stats[sort_key]
            try:
                sort_status = self.status_key[peer.status]
            except KeyError:
                sort_status = len(self.status_key) + 1
            sort_name = peer.alias

        # return tuple of sort keys
        return sort_notify, sort_used, sort_type, sort_status, sort_name

    def send_msg(self, msg: str) -> None:
        """
        Send message coming from the UI/input window
        """

        logger.debug("sending message %s in conversation %s", msg, self.name)

        # send message and log it in the history file
        if not self.account or not self.backend.client:
            return
        self.backend.client.send_msg(self.account.aid, self.name, msg)

        # statistics
        self.stats["last_send"] = datetime.datetime.now().timestamp()
        self.stats["num_send"] += 1

        # redraw list_win in case sorting is affected by stats update above
        self.wins.list_win.redraw_pad()

        # log message
        log_msg = self.log("you", msg, own=True)
        self.history.log_to_file(log_msg)

    def set_lastread(self) -> None:
        """
        Helper that sets lastread to the last message in the conversation,
        thus, marking all messages as read.
        """

        log_msg = None
        if self.wins.log_win.list:
            log_msg = self.wins.log_win.list[-1]
            # do not put new conversation event in last_read
            if log_msg.sender == "<event>":
                log_msg = None
                if len(self.wins.log_win.list) > 1:
                    log_msg = self.wins.log_win.list[-2]

        # if there is a log message, write it to lastread
        if log_msg:
            logger.debug("setting lastread in conversation %s to %s",
                         self.name, log_msg)
            self.history.set_lastread(log_msg)