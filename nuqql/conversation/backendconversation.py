"""
Backend conversation
"""

import logging

from typing import Tuple, TYPE_CHECKING

import nuqql.win

from .conversation import Conversation, CONVERSATIONS

if TYPE_CHECKING:   # imports for typing
    # pylint: disable=cyclic-import
    from nuqql.account import Account  # noqa
    from nuqql.backend import Backend  # noqa

logger = logging.getLogger(__name__)


class BackendConversation(Conversation):
    """
    Class for backend conversations
    """

    def create_windows(self) -> None:
        """
        Create windows for this conversation
        """

        logger.debug("creating windows for conversation %s", self.name)

        # create command windows for backends
        log_title = "Command log of {0}".format(self.name)
        input_title = "Command to {0}".format(self.name)
        self._create_windows_common(log_title, input_title)

        self.wins.list_win = nuqql.win.MAIN_WINS["list"]

    def get_name(self) -> str:
        """
        Get the name of the conversation, depending on type
        """

        notify = self._get_name_notification()
        return "{0}{{backend}} {1}".format(notify, self.name)

    def get_key(self) -> Tuple:
        """
        Get a key for sorting this conversation
        """

        # return tuple of sort keys:
        # notify, used, type, status, name
        return 0 - self.notification, 0, 1, 0, self.name

    @staticmethod
    def _check_chat_command(backend: "Backend", account: "Account", cmd: str,
                            name: str) -> None:
        """
        Check for chat commands
        """

        # check for existing conversation
        existing_conv = None
        existing_conv_index = -1
        for index, conv in enumerate(CONVERSATIONS):
            if not isinstance(conv, nuqql.conversation.BuddyConversation):
                continue
            if conv.backend == backend and \
               conv.account == account and \
               conv.name == name:
                existing_conv = conv
                existing_conv_index = index
                break

        # join: account <id> chat join <name>
        if cmd == "join":
            # make sure the conversation does not already exist
            if existing_conv:
                return

            # create temporary group conversation
            conv = nuqql.conversation.BuddyConversation(backend, account, name)
            conv.temporary = True
            conv.wins.list_win.add(conv)
            conv.wins.list_win.redraw()

        # part: account <id> chat part <name>
        if cmd == "part":
            # if it is (still) a temporary group conversation, remove it again
            if existing_conv and existing_conv.temporary:
                del CONVERSATIONS[existing_conv_index]
                existing_conv.wins.list_win.redraw()

    def _check_command(self, msg: str) -> None:
        """
        Check if msg is a special command we want to handle in nuqql before
        sending it to the backend
        """

        # TODO: test if we still need these functions

        parts = msg.split(" ")
        # check for account command
        # account <id> <command>
        if len(parts) < 3:
            return
        if parts[0] != "account":
            return

        # get account for this command
        assert self.backend
        account = self.backend.get_account(parts[1])
        if not account:
            return

        # check for delete command
        # account <id> delete
        if parts[2] == "delete":
            self.backend.delete_account(account.aid)
            return

        # check for chat commands
        # account <id> chat <join/part> <name>
        if len(parts) >= 5 and parts[2] == "chat":
            self._check_chat_command(self.backend, account, parts[3], parts[4])
            return

    def send_msg(self, msg: str) -> None:
        """
        Send message coming from the UI/input window
        """

        logger.debug("sending message %s in conversation %s", msg, self.name)

        self._send_msg_prepare(msg)

        # send command message to backend
        if self.backend and self.backend.client:
            # check for special commands to handle in nuqql first
            self._check_command(msg)

            self.backend.client.send_command(msg)

            if msg in ("bye", "quit"):
                # user told the backend to disconnect/quit, stop backend
                self.backend.stop()
