"""
Nuqql Conversations
"""

import curses
import datetime
import logging

from types import SimpleNamespace
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import nuqql.config

from nuqql.win import InputWin, LogWin
from .history import History
from .logmessage import LogMessage

if TYPE_CHECKING:   # imports for typing
    # pylint: disable=cyclic-import
    # pylint hack: avoid code-duplication warning with buddyconversation
    # (see: https://github.com/PyCQA/pylint/issues/214)
    from nuqql.account import Account  # noqa
    from nuqql.backend import Backend  # noqa
    from nuqql.buddy import Buddy   # noqa

logger = logging.getLogger(__name__)

# list of active conversations
CONVERSATIONS: List["Conversation"] = []


class Conversation:
    """
    Class for conversations
    """

    def __init__(self, backend: Optional["Backend"], account:
                 Optional["Account"], name: str) -> None:
        # general
        self.name = name
        self.notification = 0

        # statistics
        self.stats: Dict[str, float] = {}
        self.stats["last_used"] = 0
        self.stats["last_send"] = 0
        self.stats["num_send"] = 0

        # backend info
        self.backend = backend
        self.account = account

        # windows of the conversation
        self.wins = SimpleNamespace()
        self.wins.log_win = None
        self.wins.input_win = None
        self.wins.list_win = None

        # history and logging
        self.history = History(self)

    def activate(self, set_last_used: bool = True) -> None:
        """
        Activate windows of conversation
        """

        # check log_win to determine, if windows are already created
        if self.wins.log_win is not None:
            curses.curs_set(1)
            self.wins.input_win.state.active = True
            self.wins.input_win.redraw()
            self.wins.log_win.state.active = False
            self.wins.log_win.redraw()
            self.clear_notifications()
            if set_last_used:
                self.stats["last_used"] = datetime.datetime.now().timestamp()
            logger.debug("activated conversation %s", self.name)
            return

    def activate_log(self) -> None:
        """
        Activate windows of conversation and go to history
        """

        # check log_win to determine, if windows are already created
        if self.wins.log_win is not None:
            curses.curs_set(1)
            self.wins.input_win.state.active = False
            self.wins.log_win.state.active = True
            self.wins.log_win.zoom_win()
            self.clear_notifications()
            logger.debug("activated log of conversation %s", self.name)
            return

    def has_windows(self) -> bool:
        """
        Check if conversation has already created its windows
        """

        if self.wins.log_win:
            return True

        return False

    def _create_windows_common(self, log_title, input_title) -> None:
        """
        Helper for creating common windows
        """

        log_config = nuqql.config.get("log_win")
        self.wins.log_win = LogWin(log_config, self, log_title)
        self.wins.log_win.list = self.history.log
        input_config = nuqql.config.get("input_win")
        self.wins.input_win = InputWin(input_config, self, input_title)

    def create_windows(self) -> None:
        """
        Create windows for this conversation
        """

        # implemented in sub classes

    def _get_name_notification(self) -> str:
        """
        get notification prefix for name
        """

        # check if there are pending notifications
        if self.notification > 0:
            notify = "# "
        else:
            notify = ""

        return notify

    def get_name(self) -> str:
        """
        Get the name of the conversation, depending on type
        """

        # implemented in sub classes

    def log(self, sender: str, msg: str, tstamp: datetime.datetime = None,
            own: bool = False) -> LogMessage:
        """
        Log message to conversation's history/log window
        """

        logger.debug("logging message in conversation %s: "
                     "sender %s, timestamp %s, msg %s",
                     self.name, sender, tstamp, msg)

        # create a log message
        if tstamp is None:
            tstamp = datetime.datetime.now()
        log_msg = LogMessage(tstamp, sender, msg, own=own)

        # if conversation has not been initialized yet, stop here.
        # Messages must be loaded from the history file first
        if not self.wins.log_win:
            return log_msg

        # put message into conversation's history
        if self.history.log:
            last_msg = self.history.log[-1]
            if last_msg.tstamp.date() != tstamp.date():
                date_change_msg = LogMessage(
                    log_msg.tstamp, "<event>", "<Date changed to {}>".format(
                        log_msg.tstamp.date()), own=True)
                date_change_msg.is_read = True
                self.history.log.append(date_change_msg)
        self.history.log.append(log_msg)

        # if conversation is already active, redraw the log
        if self.is_input_win_active():
            self.wins.log_win.redraw_pad()
            self.wins.input_win.redraw_pad()    # keep cursor in input_win

        return log_msg

    def notify(self) -> None:
        """
        Notify this conversation about new messages
        """

        self.notification = 1

        if self.wins.list_win:
            self.wins.list_win.redraw_pad()

    def clear_notifications(self) -> None:
        """
        Clear notifications of buddy
        """

        self.notification = 0
        if self.wins.list_win:
            self.wins.list_win.redraw_pad()

    def __lt__(self, other: "Conversation"):
        # sort based on get_key output
        return self.get_key() < other.get_key()

    # status to sorting key mapping
    status_key = {
        "on": 0,
        "afk": 1,
        "grp": 2,
        "grp_invite": 3,
        "off": 4,
    }

    def get_key(self) -> Tuple:
        """
        Get a key for sorting this conversation
        """

        # implemented in sub classes

    def is_log_win_active(self) -> bool:
        """
        Check if conversation's log window is active
        """

        # check if log win is active
        if self.wins.log_win and self.wins.log_win.state.active:
            return True

        return False

    def is_input_win_active(self) -> bool:
        """
        Check if conversation's input window is active
        """

        # check if input win is active
        if self.wins.input_win and self.wins.input_win.state.active:
            return True

        return False

    def is_active(self) -> bool:
        """
        Check if this conversation is currently active, and return True if it
        is the case; otherwise, return False.
        """

        # check if input win and/or log win is active
        if self.is_input_win_active() or self.is_log_win_active():
            return True

        return False

    def is_any_active(self) -> bool:
        """
        Check if any conversation is currently active
        """

        if self.is_active():
            return True

        for conv in CONVERSATIONS:
            if conv.is_active():
                return True

        return False

    def get_new(self) -> Optional["Conversation"]:
        """
        Check if there is any conversation with new messages and return it
        """

        for conv in CONVERSATIONS:
            if conv.notification > 0:
                logger.debug("found new conversation in conversation %s: %s",
                             self.name, conv.name)
                return conv

        return None

    def get_next(self) -> Optional["Conversation"]:
        """
        Check if there is any newer used conversation and return it
        """

        next_conv = None
        for conv in CONVERSATIONS:
            if conv.stats["last_used"] == 0:
                continue
            if conv.stats["last_used"] > self.stats["last_used"]:
                if next_conv and \
                   next_conv.stats["last_used"] < conv.stats["last_used"]:
                    # already found a next newer conversation
                    continue
                next_conv = conv
                logger.debug("found next conversation in conversation %s: %s",
                             self.name, next_conv.name)

        return next_conv

    def get_prev(self) -> Optional["Conversation"]:
        """
        Check if there is any previously used conversation and return it
        """

        prev_conv = None
        for conv in CONVERSATIONS:
            if conv.stats["last_used"] == 0:
                continue
            if conv.stats["last_used"] < self.stats["last_used"]:
                if prev_conv and \
                   prev_conv.stats["last_used"] > conv.stats["last_used"]:
                    # already found a next older conversation
                    continue
                prev_conv = conv
                logger.debug("found previous conversation in conversation %s: "
                             "%s", self.name, prev_conv.name)

        return prev_conv

    def process_input(self, char: str) -> None:
        """
        Process user input in active window
        """

        # try to give control to the input win first...
        if self.wins.input_win and self.wins.input_win.state.active:
            self.wins.input_win.process_input(char)
            return

        # then, try to give control to the log win
        if self.wins.log_win and self.wins.log_win.state.active:
            self.wins.log_win.process_input(char)
            return

    def _send_msg_prepare(self, msg) -> None:
        """
        helper for running common operations when sending a message
        """

        # TODO: unify the logging in a method of Conversation?
        # log message
        tstamp = datetime.datetime.now()
        log_msg = LogMessage(tstamp, "you", msg, own=True)
        self.wins.log_win.add(log_msg)

        # statistics
        self.stats["last_send"] = datetime.datetime.now().timestamp()
        self.stats["num_send"] += 1

        # redraw list_win in case sorting is affected by stats update above
        self.wins.list_win.redraw_pad()

    def send_msg(self, msg: str) -> None:
        """
        Send message coming from the UI/input window
        """

        # implemented in sub classes

    def set_lastread(self) -> None:
        """
        Helper that sets lastread to the last message in the conversation,
        thus, marking all messages as read.
        """

        # only relevant for BuddyConversation. Implemented there.
