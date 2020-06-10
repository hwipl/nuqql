"""
Group conversation
"""

import datetime
import logging

import nuqql.history

from .conversation import BuddyConversation

logger = logging.getLogger(__name__)


class GroupConversation(BuddyConversation):
    """
    Class for group chat conversations
    """

    def create_windows(self) -> None:
        # call method of super class
        BuddyConversation.create_windows(self)

        # if this conversation belongs to a group chat invite, display special
        # event to the user
        if self.peers:
            buddy = self.peers[0]
            if buddy.status == "grp_invite":
                msg = "<You are invited to this group chat. " \
                        "Enter \"/join\" to accept or \"/part\" to decline " \
                        "this invite.>"
                self.log("<event>", msg, own=True)

    def send_msg(self, msg: str) -> None:
        """
        Send message coming from the UI/input window
        """

        logger.debug("sending message %s in conversation %s", msg, self.name)

        # log message
        log_msg = self.log("you", msg, own=True)

        # statistics
        self.stats["last_send"] = datetime.datetime.now().timestamp()
        self.stats["num_send"] += 1

        # redraw list_win in case sorting is affected by stats update above
        self.wins.list_win.redraw_pad()

        # check for special commands
        if msg == "/names":
            # TODO: use peers list for this?
            if self.account and self.backend and self.backend.client:
                # create user list command
                msg = "account {} chat users {}".format(self.account.aid,
                                                        self.name)
                # send command message to backend
                self.backend.client.send_command(msg)
            return

        if msg == "/part":
            if self.account and self.backend and self.backend.client:
                # create chat part command
                msg = "account {} chat part {}".format(self.account.aid,
                                                       self.name)
                # send command message to backend
                self.backend.client.send_command(msg)
            return

        if msg.startswith("/invite "):
            parts = msg.split()
            if len(parts) > 1:
                if self.account and self.backend and self.backend.client:
                    # create chat invite command
                    user = parts[1]
                    msg = "account {} chat invite {} {}".format(
                        self.account.aid, self.name, user)
                    # send command message to backend
                    self.backend.client.send_command(msg)
                return

        if msg == "/join":
            # TODO: allow specification of another group chat?
            if self.account and self.backend and self.backend.client:
                # create chat join command
                msg = "account {} chat join {}".format(self.account.aid,
                                                       self.name)
                # send command message to backend
                self.backend.client.send_command(msg)
            return

        # send and log group chat message
        if self.account and self.backend.client:
            self.backend.client.send_group_msg(self.account.aid, self.name,
                                               msg)
        nuqql.history.log(self, log_msg)
