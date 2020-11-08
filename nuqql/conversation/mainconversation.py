"""
special nuqql main conversation for welcome screen
"""

import logging

import nuqql.config

from .conversation import Conversation

logger = logging.getLogger(__name__)


class MainConversation(Conversation):
    """
    Class for the main/welcome screen conversation
    """

    def create_windows(self) -> None:
        """
        Create windows for this conversation
        """

        logger.debug("creating windows for conversation %s", self.name)

        # create command windows for nuqql
        list_config = nuqql.config.get("list_win")
        log_config = nuqql.config.get("log_win_main")
        self.wins.list_win = nuqql.win.ListWin(list_config, self,
                                               "Conversation list")
        self.wins.log_win = nuqql.win.LogWin(log_config, self,
                                             f"nuqql v{nuqql.VERSION}")

        # list conversations in list window
        self.wins.list_win.list = nuqql.conversation.CONVERSATIONS

        # mark nuqql's list window as active, so main loop does not quit
        self.wins.list_win.state.active = True

        # draw list
        self.wins.list_win.redraw()
        self.wins.log_win.redraw()

        # save windows
        nuqql.win.MAIN_WINS["list"] = self.wins.list_win
        nuqql.win.MAIN_WINS["log"] = self.wins.log_win
