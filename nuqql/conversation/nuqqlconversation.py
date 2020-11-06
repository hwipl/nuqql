"""
special nuqql conversation
"""

import logging

from typing import Tuple

import nuqql.config

from .conversation import Conversation, CONVERSATIONS

logger = logging.getLogger(__name__)


class NuqqlConversation(Conversation):
    """
    Class for the nuqql conversation
    """

    def create_windows(self) -> None:
        """
        Create windows for this conversation
        """

        logger.debug("creating windows for conversation %s", self.name)

        # create command windows for nuqql
        log_title = "Command log of nuqql"
        input_title = "Command to nuqql"
        self._create_windows_common(log_title, input_title)

        # nuqql itself needs a list window for buddy list
        self.wins.list_win = nuqql.win.MAIN_WINS["list"]

        # add to conversation list
        CONVERSATIONS.append(self)

    def get_name(self) -> str:
        """
        Get the name of the conversation, depending on type
        """

        notify = self._get_name_notification()
        return "{0}{{nuqql}}".format(notify)

    def get_key(self) -> Tuple:
        """
        Get a key for sorting this conversation
        """

        # return tuple of sort keys:
        # notify, used, type, status, name
        return 0 - self.notification, 0, 2, 0, self.name

    def send_msg(self, msg: str) -> None:
        """
        Send message coming from the UI/input window
        """

        logger.debug("sending message %s in conversation %s", msg, self.name)

        self._send_msg_prepare(msg)

        # handle nuqql command
        assert isinstance(self.backend, nuqql.backend.NuqqlBackend)
        self.backend.handle_nuqql_command(msg)
