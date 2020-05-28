"""
Nuqql Buddy
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:   # imports for typing
    # pylint: disable=cyclic-import
    from nuqql.backend import Backend  # noqa
    from nuqql.account import Account  # noqa


class Buddy:
    """
    Class for Buddies
    """

    def __init__(self, backend: "Backend", account: "Account",
                 name: "str") -> None:
        self.backend = backend
        self.account = account
        self.name = name
        self.alias = name
        self.status = "off"     # use short status name
        self.updated = True

    # dictionary for mapping status names to shorter version (key: lower case)
    status_map = {
        "offline": "off",
        "available": "on",
        "away": "afk",
        "group_chat": "grp",
        "group_chat_invite": "grp_invite",
    }

    def set_status(self, status: str) -> None:
        """
        Set status of buddy; convert status to something shorter
        """

        try:
            self.status = Buddy.status_map[status.lower()]
        except KeyError:
            self.status = status

    def update(self, status: str, alias: str) -> bool:
        """
        Update Buddy
        """

        # save old status and alias to check if buddy has changed
        old_status = self.status
        old_alias = self.alias

        # set new values
        self.updated = True
        self.set_status(status)
        self.alias = alias

        # check if buddy has changed
        if old_status != self.status or old_alias != self.alias:
            return True

        # has not changed
        return False
