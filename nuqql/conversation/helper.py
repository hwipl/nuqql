"""
nuqql conversation helpers
"""

import datetime
import logging

from typing import TYPE_CHECKING

import nuqql.win

from .conversation import CONVERSATIONS
from .logmessage import LogMessage

if TYPE_CHECKING:   # imports for typing
    # pylint: disable=cyclic-import
    from nuqql.backend import Backend  # noqa

logger = logging.getLogger(__name__)


def remove_backend_conversations(backend: "Backend") -> None:
    """
    Remove all conversations beloning to the backend
    """

    logger.debug("removing all conversations of backend %s", backend.name)
    for conv in CONVERSATIONS[:]:
        if conv.backend == backend:
            CONVERSATIONS.remove(conv)
            conv.wins.list_win.redraw()
            logger.debug("removed conversation %s of backend %s",
                         conv.name, backend.name)


def log_main_window(msg: str) -> None:
    """
    Log message to main windows
    """

    logger.debug("logging message to main window: %s", msg)
    now = datetime.datetime.now()
    log_msg = LogMessage(now, "nuqql", msg)
    nuqql.win.MAIN_WINS["log"].add(log_msg)


def log_nuqql_conv(msg: str) -> None:
    """
    Log message to the nuqql conversation
    """

    logger.debug("logging message to nuqql conversation: %s", msg)
    for conv in CONVERSATIONS:
        if conv.name == "nuqql":
            conv.log("nuqql", msg)
            return


def resize_main_window() -> None:
    """
    Resize main window
    """

    logger.debug("resizing main window")

    # get main win
    screen = nuqql.win.MAIN_WINS["screen"]

    # get new maxima
    max_y, max_x = screen.getmaxyx()

    # redraw main windows
    screen.clear()
    screen.refresh()

    # redraw conversation windows
    found_active = False
    for conv in CONVERSATIONS:
        # resize and move conversation windows
        if conv.wins.list_win:
            size_y, size_x = conv.wins.list_win.config.get_size()
            conv.wins.list_win.resize_win(size_y, size_x)
        if conv.wins.log_win:
            # TODO: move zoom/resizing to win.py?
            if conv.wins.log_win.state.zoomed:
                size_y, size_x = max_y, max_x
                pos_y, pos_x = 0, 0
                conv.wins.log_win.state.pad_y = 0  # reset pad position
            else:
                size_y, size_x = conv.wins.log_win.config.get_size()
                pos_y, pos_x = conv.wins.log_win.config.get_pos()
            conv.wins.log_win.resize_win(size_y, size_x)
            conv.wins.log_win.move_win(pos_y, pos_x)
        if conv.wins.input_win:
            size_y, size_x = conv.wins.input_win.config.get_size()
            conv.wins.input_win.resize_win(size_y, size_x)
            pos_y, pos_x = conv.wins.input_win.config.get_pos()
            conv.wins.input_win.move_win(pos_y, pos_x)
        # redraw active conversation windows
        if conv.is_active():
            found_active = True
            conv.wins.list_win.redraw()
            conv.wins.input_win.redraw()
            conv.wins.log_win.redraw()

    # if there are no active conversations, redraw nuqql main windows
    if not found_active:
        # list win
        list_win = nuqql.win.MAIN_WINS["list"]
        size_y, size_x = list_win.config.get_size()

        list_win.resize_win(size_y, size_x)
        list_win.redraw()

        # log main win
        log_win = nuqql.win.MAIN_WINS["log"]
        size_y, size_x = log_win.config.get_size()
        pos_y, pos_x = log_win.config.get_pos()

        log_win.resize_win(size_y, size_x)
        log_win.move_win(pos_y, pos_x)
        log_win.redraw()
