"""
History: (file) logging for nuqql conversations
"""

import datetime
import logging
import pathlib
import os

from typing import List, Optional, TYPE_CHECKING

from .logmessage import LogMessage

if TYPE_CHECKING:   # imports for typing
    # pylint: disable=cyclic-import
    from .conversation import Conversation  # noqa

logger = logging.getLogger(__name__)

HISTORY_FILE = "/history"
LASTREAD_FILE = "/lastread"


class History:
    """
    Message history
    """

    def __init__(self, conv: "Conversation") -> None:
        self.conv = conv
        self.conv_path = ""
        self.log: List[LogMessage] = []
        self.logger: Optional[logging.Logger] = None
        self.log_file = ""
        # self.lastread_file = None

    def _get_conv_path(self) -> str:
        """
        Get path for conversation history as a string and make sure it exists
        """

        # construct directory path
        assert self.conv.backend and self.conv.account
        conv_dir = str(pathlib.Path.home()) + \
            "/.config/nuqql/conversation/{}/{}/{}".format(
                self.conv.backend.name, self.conv.account.aid, self.conv.name)

        # make sure directory exists
        pathlib.Path(conv_dir).mkdir(parents=True, exist_ok=True)

        return conv_dir

    @staticmethod
    def _get_logger(name, file_name: str) -> logging.Logger:
        """
        Create a logger for a conversation
        """

        # create logger
        conv_logger = logging.getLogger(name)
        conv_logger.propagate = False
        conv_logger.setLevel(logging.DEBUG)

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
        if not conv_logger.hasHandlers():
            conv_logger.addHandler(fileh)

        # return logger to caller
        return conv_logger

    def init_logger(self) -> None:
        """
        Init logger for a conversation
        """

        logger.debug("initializing logger of conversation %s", self.conv.name)

        # get log dir and make sure it exists
        assert self.conv.backend and self.conv.account
        self.conv_path = self._get_conv_path()

        # create logger with log name and log file
        log_name = "nuqql.history.{}.{}.{}".format(self.conv.backend.name,
                                                   self.conv.account.aid,
                                                   self.conv.name)
        self.log_file = self.conv_path + HISTORY_FILE
        self.logger = self._get_logger(log_name, self.log_file)

    @staticmethod
    def _parse_log_line(line: str) -> LogMessage:
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

    @staticmethod
    def _create_log_line(log_msg: LogMessage) -> str:
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

    def get_lastread(self) -> Optional[LogMessage]:
        """
        Get last read message from "lastread" file of the conversation
        """

        logger.debug("getting lastread of conversation %s", self.conv.name)
        lastread_file = self.conv_path + LASTREAD_FILE
        try:
            with open(lastread_file, newline="\r\n") as in_file:
                for line in in_file:
                    log_msg = self._parse_log_line(line)
                    log_msg.is_read = True
                    return log_msg
                logger.debug("lastread file of conversation %s is empty",
                             self.conv.name)
                return None
        except FileNotFoundError:
            logger.debug("lastread file of conversation %s not found",
                         self.conv.name)
            return None

    def set_lastread(self, log_msg: LogMessage) -> None:
        """
        Set last read message in "lastread" file of the conversation
        """

        logger.debug("setting lastread of conversation %s", self.conv.name)

        # create log line and write it to lastread file
        line = self._create_log_line(log_msg) + "\r\n"
        lines = []
        lines.append(line)

        lastread_file = self.conv_path + LASTREAD_FILE
        with open(lastread_file, "w+") as out_file:
            out_file.writelines(lines)

    def get_last_log_line(self) -> Optional[LogMessage]:
        """
        Read last LogMessage from log file
        """

        logger.debug("getting last log line of conversation %s",
                     self.conv.name)
        history_file = self.conv_path + HISTORY_FILE
        try:
            # negative seeking requires binary mode
            with open(history_file, "rb") as in_file:
                # check if file contains at least 2 bytes
                in_file.seek(0, os.SEEK_END)
                if in_file.tell() < 3:
                    logger.debug("log of conversation %s seems to be empty",
                                 self.conv.name)
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
                log_msg = self._parse_log_line(last_line.decode())
                return log_msg
        except FileNotFoundError:
            logger.debug("log file of conversation %s not found",
                         self.conv.name)
            return None

    def init_log_from_file(self) -> None:
        """
        Initialize a conversation's log from the conversation's log file
        """

        logger.debug("initializing log of conversation %s from file %s",
                     self.conv.name, self.log_file)

        # get last read log message
        last_read = self.get_lastread()
        is_read = True

        with open(self.log_file, newline="\r\n") as in_file:
            prev_msg = None
            for line in in_file:
                # parse log line and create log message
                log_msg = self._parse_log_line(line)
                log_msg.is_read = is_read

                # check if date changed between two messages, and print event
                if prev_msg and \
                   prev_msg.tstamp.date() != log_msg.tstamp.date():
                    date_change_msg = LogMessage(
                        log_msg.tstamp,
                        "<event>", "<Date changed to {}>".format(
                            log_msg.tstamp.date()), own=True)
                    date_change_msg.is_read = True
                    self.log.append(date_change_msg)
                prev_msg = log_msg

                # add log message to the conversation's log
                self.log.append(log_msg)

                # if this is the last read message, following message will be
                # marked as unread
                if last_read and last_read.is_equal(log_msg):
                    is_read = False
        if self.log:
            # if there were any log messages in the log file, put a marker in
            # the log where the new messages start
            tstamp = datetime.datetime.now()
            new_conv_msg = "<Started new conversation at {}.>".format(
                tstamp.strftime("%Y-%m-%d %H:%M:%S"))
            log_msg = LogMessage(tstamp, "<event>", new_conv_msg, own=True)
            log_msg.is_read = True
            self.log.append(log_msg)

    def log_to_file(self, log_msg: LogMessage) -> None:
        """
        Write LogMessage to history log file and set lastread message
        """

        logger.debug("logging msg to log file of conversation %s: %s",
                     self.conv.name, log_msg)
        # create line and write it to history
        line = self._create_log_line(log_msg)
        assert self.logger
        self.logger.info(line)

        # assume user read all previous messages when user sends a message and
        # set lastread accordingly
        if log_msg.own:
            self.set_lastread(log_msg)
