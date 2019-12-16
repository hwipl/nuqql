"""
History: (file) logging for nuqql conversations
"""

import datetime
import logging
import pathlib
import os

from typing import TYPE_CHECKING, Optional, Tuple
if TYPE_CHECKING:   # imports for typing
    from nuqql.conversation import Conversation

HISTORY_FILE = "/history"
LASTREAD_FILE = "/lastread"


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


####################
# Helper Functions #
####################


def get_conv_path(conv: "Conversation") -> str:
    """
    Get path for conversation history as a string and make sure it exists
    """

    # construct directory path
    assert conv.account
    conv_dir = str(pathlib.Path.home()) + \
        "/.config/nuqql/conversation/{}/{}/{}".format(conv.backend.name,
                                                      conv.account.aid,
                                                      conv.name)
    # make sure directory exists
    pathlib.Path(conv_dir).mkdir(parents=True, exist_ok=True)

    return conv_dir


def get_logger(name, file_name: str) -> logging.Logger:
    """
    Create a logger for a conversation
    """

    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # create handler
    fileh = logging.FileHandler(file_name)
    fileh.setLevel(logging.DEBUG)
    fileh.terminator = "\r\n"

    # create formatter
    formatter = logging.Formatter(
        # fmt="%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s",
        fmt="%(message)s",
        datefmt="%s")

    # add formatter to handler
    fileh.setFormatter(formatter)

    # add handler to logger
    if not logger.hasHandlers():
        logger.addHandler(fileh)

    # return logger to caller
    return logger


def init_logger(conv: "Conversation") -> Tuple[logging.Logger, str]:
    """
    Init logger for a conversation
    """

    # get log dir and make sure it exists
    assert conv.account
    log_dir = get_conv_path(conv)

    # create logger with log name and log file
    log_name = "{} {} {}".format(conv.backend.name, conv.account.aid,
                                 conv.name)
    log_file = log_dir + HISTORY_FILE
    logger = get_logger(log_name, log_file)

    # return the ready logger and the log file to caller
    return logger, log_file


def parse_log_line(line: str) -> LogMessage:
    """
    Parse line from log file and return a LogMessage
    """

    # parse line
    parts = line.split(sep=" ", maxsplit=3)
    # tstamp = parts[0]
    direction = parts[1]
    is_own = False
    if direction == "OUT":
        is_own = True
    sender = parts[2]
    msg = parts[3][:-2]
    tstamp = datetime.datetime.fromtimestamp(int(parts[0]))

    # create and return LogMessage
    log_msg = LogMessage(tstamp, sender, msg, own=is_own)
    return log_msg


def create_log_line(log_msg: LogMessage) -> str:
    """
    Create a line for the log files from a LogMessage
    """

    # determine log line contents
    tstamp = round(log_msg.tstamp.timestamp())
    direction = "IN"
    sender = log_msg.sender
    if log_msg.own:
        direction = "OUT"
        sender = "you"
    msg = log_msg.msg

    return "{} {} {} {}".format(tstamp, direction, sender, msg)


def get_lastread(conv: "Conversation") -> Optional[LogMessage]:
    """
    Get last read message from "lastread" file of the conversation
    """

    # get lastread dir and make sure it exists
    lastread_dir = get_conv_path(conv)
    lastread_file = lastread_dir + LASTREAD_FILE

    try:
        with open(lastread_file, newline="\r\n") as in_file:
            for line in in_file:
                log_msg = parse_log_line(line)
                log_msg.is_read = True
                return log_msg
            return None
    except FileNotFoundError:
        return None


def set_lastread(conv: "Conversation", log_msg: LogMessage) -> None:
    """
    Set last read message in "lastread" file of the conversation
    """

    # get lastread dir and make sure it exists
    lastread_dir = get_conv_path(conv)
    lastread_file = lastread_dir + LASTREAD_FILE

    # create log line and write it to lastread file
    line = create_log_line(log_msg) + "\r\n"
    lines = []
    lines.append(line)
    with open(lastread_file, "w+") as out_file:
        out_file.writelines(lines)


def get_last_log_line(conv: "Conversation") -> Optional[LogMessage]:
    """
    Read last LogMessage from log file
    """

    # get history dir and make sure it exists
    history_dir = get_conv_path(conv)
    history_file = history_dir + HISTORY_FILE

    try:
        # negative seeking requires binary mode
        with open(history_file, "rb") as in_file:
            # check if file contains at least 2 bytes
            in_file.seek(0, os.SEEK_END)
            if in_file.tell() < 3:
                return None

            # try to find last line
            in_file.seek(-3, os.SEEK_END)
            while in_file.read(2) != b"\r\n":
                try:
                    in_file.seek(-3, os.SEEK_CUR)
                except IOError:
                    in_file.seek(-2, os.SEEK_CUR)
                    if in_file.tell() == 0:
                        break

            # read and return last line as LogMessage
            last_line = in_file.read()
            log_msg = parse_log_line(last_line.decode())
            return log_msg
    except FileNotFoundError:
        return None


def init_log_from_file(conv: "Conversation") -> None:
    """
    Initialize a conversation's log from the conversation's log file
    """

    # get last read log message
    last_read = get_lastread(conv)
    is_read = True

    with open(conv.history.log_file, newline="\r\n") as in_file:
        prev_msg = None
        for line in in_file:
            # parse log line and create log message
            log_msg = parse_log_line(line)
            log_msg.is_read = is_read

            # check if date changed between two messages, and print event
            if prev_msg and prev_msg.tstamp.date() != log_msg.tstamp.date():
                date_change_msg = LogMessage(
                    log_msg.tstamp, "<event>", "<Date changed to {}>".format(
                        log_msg.tstamp.date()), own=True)
                date_change_msg.is_read = True
                conv.history.log.append(date_change_msg)
            prev_msg = log_msg

            # add log message to the conversation's log
            conv.history.log.append(log_msg)

            # if this is the last read message, following message will be
            # marked as unread
            if last_read and last_read.is_equal(log_msg):
                is_read = False
    if conv.history.log:
        # if there were any log messages in the log file, put a marker in the
        # log where the new messages start
        tstamp = datetime.datetime.now()
        new_conv_msg = "<Started new conversation at {}.>".format(
            tstamp.strftime("%Y-%m-%d %H:%M:%S"))
        log_msg = LogMessage(tstamp, "<event>", new_conv_msg, own=True)
        log_msg.is_read = True
        conv.history.log.append(log_msg)


def log(conv, log_msg: LogMessage) -> None:
    """
    Write LogMessage to history log file and set lastread message
    """

    # create line and write it to history
    line = create_log_line(log_msg)
    conv.history.logger.info(line)

    # assume user read all previous messages when user sends a message and set
    # lastread accordingly
    if log_msg.own:
        set_lastread(conv, log_msg)
