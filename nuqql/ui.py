"""
User Interface part of nuqql
"""

import curses
import curses.ascii
import datetime
import logging

from typing import TYPE_CHECKING, Any, Callable, Optional

import nuqql.config
import nuqql.conversation

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from nuqql.buddy import Buddy  # noqa

logger = logging.getLogger(__name__)


def handle_message(*args: Any) -> None:
    """
    Handle message from backend
    """

    # parse args
    backend, acc_id, chat, tstamp, sender, msg = args

    # convert timestamp
    tstamp = datetime.datetime.fromtimestamp(tstamp)

    # look for an existing conversation and use it
    for conv in nuqql.conversation.CONVERSATIONS:
        if conv.backend is backend and \
           conv.account and conv.account.aid == acc_id and \
           conv.name == chat:
            # log message
            logger.debug("found conversation %s for message", conv.name)
            log_msg = conv.log(sender, msg, tstamp=tstamp)
            conv.history.log_to_file(log_msg)

            # if window is not already active notify user
            if not conv.is_input_win_active():
                conv.notify()
            return

    # nothing found, log to main window
    # or create temporary conversation
    account = backend.get_account(acc_id)
    if account is None:
        logger.debug("no conversation found for message")
        backend.conversation.log(sender, msg, tstamp=tstamp)
    else:
        # create buddy conversation
        conv = nuqql.conversation.BuddyConversation(backend, account, chat)
        conv.temporary = True
        conv.wins.list_win.add(conv)
        conv.wins.list_win.redraw_pad()
        logger.debug("created temporary conversation %s", conv.name)

        # log message
        log_msg = conv.log(sender, msg, tstamp=tstamp)
        conv.history.log_to_file(log_msg)

        # if window is not already active notify user
        if not conv.is_input_win_active():
            conv.notify()


def handle_chat_message(*args: Any) -> bool:
    """
    Handle chat message from backend
    """

    # parse args
    backend, acc_id, ctype, chat, nick, alias, status = args

    for conv in nuqql.conversation.CONVERSATIONS:
        if conv.backend is backend and \
           conv.account and conv.account.aid == acc_id and \
           conv.name == chat:
            # log chat message/event
            if alias == nick:
                log_msg = conv.log(chat, "{} {} [{}]".format(ctype, nick,
                                                             status))
            else:
                log_msg = conv.log(chat, "{} {} ({}) [{}]".format(
                    ctype, alias, nick, status))
            conv.history.log_to_file(log_msg)

            # if window is not already active notify user
            if not conv.is_input_win_active():
                conv.notify()
            logger.debug("handled chat message")
            return True

    # did not handle the message, return False
    logger.debug("chat message not handled")
    return False


def update_buddy(buddy: "Buddy") -> None:
    """
    Update buddy in UI
    """

    # look for existing buddy
    for conv in nuqql.conversation.CONVERSATIONS:
        if not isinstance(conv, nuqql.conversation.BuddyConversation):
            continue
        if conv.temporary:
            continue

        conv_buddy = conv.peers[0]
        if conv_buddy is buddy:
            conv.wins.list_win.redraw_pad()
            logger.debug("updated buddy %s in ui", buddy.name)
            return

    logger.debug("buddy %s not updated", buddy.name)


def add_buddy_to_temporary_conv(buddy: "Buddy") -> \
        Optional[nuqql.conversation.BuddyConversation]:
    """
    Try to find a temporary conversation for this buddy and add the buddy to it
    """

    for conv in nuqql.conversation.CONVERSATIONS:
        if not isinstance(conv, nuqql.conversation.BuddyConversation):
            continue
        if not conv.temporary:
            continue

        if conv.backend == buddy.backend and \
           conv.account == buddy.account and \
           conv.name == buddy.name:
            conv.peers.append(buddy)
            # conversation/buddy is now in backend, remove temporary flag
            conv.temporary = False
            logger.debug("added buddy %s to temporary conversation %s",
                         buddy.name, conv.name)
            return conv

    # nothing found, tell caller
    logger.debug("no temporary conversation found for buddy %s", buddy.name)
    return None


def add_buddy(buddy: "Buddy") -> None:
    """
    Add a new buddy to UI
    """

    # add new conversation for the buddy if necessary
    conv = add_buddy_to_temporary_conv(buddy)
    if not conv:
        # no temporary conversation found, add new one
        conv = nuqql.conversation.BuddyConversation(buddy.backend,
                                                    buddy.account,
                                                    buddy.name)
        conv.peers.append(buddy)
        conv.wins.list_win.add(conv)
        logger.debug("added conversation for buddy %s", buddy.name)

    # redraw list to show update
    conv.wins.list_win.redraw_pad()

    # check if there are unread messages for this new buddy in the history
    last_log_msg = conv.history.get_last_log_line()
    last_read_msg = conv.history.get_lastread()
    if last_log_msg:
        if not last_read_msg or not last_log_msg.is_equal(last_read_msg):
            # there are unread messages, notify user if
            # conversation is inactive
            if not conv.is_active():
                conv.notify()

    logger.debug("added buddy %s to ui", buddy.name)


def remove_buddy(buddy: "Buddy") -> None:
    """
    Remove a buddy from the UI
    """

    for index, conv in enumerate(nuqql.conversation.CONVERSATIONS):
        if not isinstance(conv, nuqql.conversation.BuddyConversation):
            continue
        if conv.temporary:
            # skip temporary conversations/buddies
            return

        conv_buddy = conv.peers[0]
        if conv_buddy is buddy:
            # if log window or input window are active, close them first
            if conv.is_log_win_active():
                # note: this activates the input window
                conv.wins.log_win.go_back()
            if conv.is_input_win_active():
                conv.wins.input_win.go_back()

            # remove conversation
            del nuqql.conversation.CONVERSATIONS[index]
            conv.wins.list_win.redraw()
            logger.debug("removed buddy %s from ui", buddy.name)
            return

    logger.debug("buddy %s not found/removed", buddy.name)


def read_input() -> str:
    """
    Read user input and return it to caller
    """

    # try to get input from user (timeout set in init())
    try:
        wch = nuqql.win.MAIN_WINS["screen"].get_wch()
    except curses.error:
        # no user input...
        wch = None

    return wch


def show_terminal_warning() -> None:
    """
    Show a warning that the terminal size is invalid, if it fits on screen
    """

    # clear terminal
    nuqql.win.MAIN_WINS["screen"].clear()

    # check if terminal is big enough for at least one character
    max_y, max_x = nuqql.win.MAIN_WINS["screen"].getmaxyx()
    if max_y < 1:
        return
    if max_x < 1:
        return

    # print as much of the error message as possible
    msg = "Invalid terminal size. Please resize."[:max_x - 1]
    nuqql.win.MAIN_WINS["screen"].addstr(0, 0, msg)
    logger.debug("showed terminal size invalid warning")


def is_input_valid(char: str) -> bool:
    """
    Helper that checks if input is valid
    """

    # is there a char at all?
    if char is None:
        return False

    # check for embedded 0 byte
    if char == "\0":
        return False

    return True


def handle_input() -> bool:
    """
    Read and handle user input
    """

    # list window is inactive -> user quit
    if not nuqql.win.MAIN_WINS["list"].state.active:
        return False

    # wait for user input and get timeout or character to process
    char = read_input()

    # handle user input
    if not is_input_valid(char):
        # No valid input, keep waiting for input
        return True

    # if terminal size is not valid, stop here
    if not nuqql.config.WinConfig.is_terminal_valid():
        show_terminal_warning()
        return True

    # if terminal resized, resize and redraw active windows
    if char == curses.KEY_RESIZE:
        nuqql.conversation.resize_main_window()
        return True

    # pass user input to active conversation
    for conv in nuqql.conversation.CONVERSATIONS:
        if conv.is_active():
            conv.process_input(char)
            return True

    # if no conversation is active pass input to active list window for
    # list window navigation
    nuqql.win.MAIN_WINS["list"].process_input(char)
    return True


def start(stdscr: Any, func: Callable) -> str:
    """
    Start UI and run provided function
    """

    logger.debug("starting ui")

    # save stdscr
    nuqql.win.MAIN_WINS["screen"] = stdscr

    # configuration
    stdscr.timeout(10)

    # clear everything
    stdscr.clear()
    stdscr.refresh()

    # disable cursor
    curses.curs_set(0)

    # make sure configs are loaded
    nuqql.config.init(stdscr)

    # create main windows, if terminal size is valid, otherwise just stop here
    if not nuqql.config.WinConfig.is_terminal_valid():
        logger.error("terminal size invalid")
        return "Terminal size invalid."

    # run function provided by caller
    return func()


def init(func: Callable) -> None:
    """
    Initialize UI
    """

    logger.debug("initializing ui")
    retval = curses.wrapper(start, func)
    if retval and retval != "":
        print(retval)
