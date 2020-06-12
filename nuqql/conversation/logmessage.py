"""
Log message
"""

import datetime


class LogMessage:
    """Class for log messages to be displayed in LogWins"""

    def __init__(self, tstamp: datetime.datetime, sender: str, msg: str,
                 own: bool = False) -> None:
        """
        Initialize log message with timestamp, sender of the message, and
        the message itself
        """

        # timestamp
        self.tstamp = tstamp

        # sender could be us or buddy/other user, as
        # indicated by self.own (helps with coloring etc. later)
        self.sender = sender
        self.own = own

        # the message itself
        self.msg = msg

        # has message been read?
        self.is_read = False

    def get_short_sender(self) -> str:
        """
        Convert name to a shorter version
        """

        # TODO: improve? Save short name in account and buddy instead?
        return self.sender.split("@")[0]

    def read(self, mark_read: bool = True) -> str:
        """
        Format and return log message; mark it as read
        """

        # format message
        msg = "{0} {1}: {2}".format(self.tstamp.strftime("%H:%M:%S"),
                                    self.get_short_sender(),
                                    self.msg)

        # message has now been read
        if mark_read:
            self.is_read = True

        return msg

    def is_equal(self, other: "LogMessage") -> bool:
        """
        Check if this message and the LogMessage "other" match
        """

        if self.tstamp != other.tstamp:
            return False
        if self.sender != other.sender:
            return False
        if self.msg != other.msg:
            return False

        return True
