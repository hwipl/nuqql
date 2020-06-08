"""
Nuqql account
"""

import logging
import time

from typing import List, TYPE_CHECKING

import nuqql.ui

from nuqql.buddy import Buddy

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from nuqql.backend import Backend

logger = logging.getLogger(__name__)

# update buddies only every BUDDY_UPDATE_TIMER seconds
BUDDY_UPDATE_TIMER = 5


class Account:
    """
    Class for Accounts
    """

    def __init__(self, aid: str, prot: str, user: str) -> None:
        self.aid = aid
        self.name = user
        self.type = prot
        self.buddies: List[Buddy] = []
        self.buddies_update = 0
        logger.debug("created new account: aid %s, name %s, type %s",
                     self.aid, self.name, self.type)

    def update_buddies(self) -> bool:
        """
        Update the buddy list of this account.
        Return True if an update is pending, False otherwise.
        """

        # update only once every BUDDY_UPDATE_TIMER seconds
        if time.time() - self.buddies_update <= BUDDY_UPDATE_TIMER:
            return False
        self.buddies_update = int(time.time())

        # remove buddies, that have not been updated for a while
        for rem in [buddy for buddy in self.buddies if not buddy.updated]:
            nuqql.ui.remove_buddy(rem)
            logger.debug("removed buddy %s from account %s on backend %s",
                         rem.name, self.aid, rem.backend.name)
        self.buddies = [buddy for buddy in self.buddies if buddy.updated]

        # set update pending in buddy
        for buddy in self.buddies:
            buddy.updated = False

        return True

    def update_buddy(self, backend: "Backend", name: str, alias: str,
                     status: str) -> None:
        """
        Update a single buddy of this account. Could be a new buddy.
        """

        # look for existing buddy
        for buddy in self.buddies:
            if buddy.name == name:
                if buddy.update(status, alias):
                    # tell ui about the update
                    nuqql.ui.update_buddy(buddy)

                # found existing buddy; stop here
                return

        # new buddy
        new_buddy = Buddy(backend, self, name)
        new_buddy.update(status, alias)
        self.buddies.append(new_buddy)
        logger.debug("added new buddy %s to account %s on backend %s",
                     name, self.aid, backend.name)

        # tell ui there is a new buddy
        nuqql.ui.add_buddy(new_buddy)
