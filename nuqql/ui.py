"""
User Interface part of nuqql
"""

#######################
# USER INTERFACE PART #
#######################

import curses
import curses.ascii
import datetime

import nuqql.config
import nuqql.conversation
import nuqql.history


def handle_message(backend, acc_id, tstamp, sender, msg):
    """
    Handle message from backend
    """

    # look for an existing conversation and use it
    for conv in nuqql.conversation.CONVERSATIONS:
        if conv.backend is backend and \
           conv.account and conv.account.aid == acc_id and \
           conv.name == sender:
            # log message
            tstamp = datetime.datetime.fromtimestamp(tstamp)
            log_msg = conv.log(conv.name, msg, tstamp=tstamp)
            nuqql.history.log(conv, log_msg)

            # if window is not already active notify user
            if not conv.is_active():
                conv.notify()
            return

    # nothing found, log to main window
    backend.conversation.log(sender, msg, tstamp=tstamp)


def update_buddy(buddy):
    """
    Update buddy in UI
    """

    # look for existing buddy
    for conv in nuqql.conversation.CONVERSATIONS:
        if conv.type != "buddy":
            continue

        conv_buddy = conv.peers[0]
        if conv_buddy is buddy:
            conv.list_win.redraw()


def add_buddy(buddy):
    """
    Add a new buddy to UI
    """

    # add a new conversation for the new buddy
    conv = nuqql.conversation.Conversation(buddy.backend, buddy.account,
                                           buddy.name)
    conv.peers.append(buddy)
    conv.list_win.add(conv)
    conv.list_win.redraw()

    # check if there are unread messages for this new buddy in the history
    last_log_msg = nuqql.history.get_last_log_line(conv)
    last_read_msg = nuqql.history.get_lastread(conv)
    if last_log_msg:
        if not last_read_msg or not last_log_msg.is_equal(last_read_msg):
            # there are unread messages, notify user if
            # conversation is inactive
            if not conv.is_active():
                conv.notify()


def read_input():
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


def handle_input():
    """
    Read and handle user input
    """

    # wait for user input and get timeout or character to process
    char = read_input()

    # handle user input
    if char is None:
        # NO INPUT, keep waiting for input..
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

    # if no conversation is active pass input to active list window
    if nuqql.win.MAIN_WINS["list"].active:
        # list window navigation
        nuqql.win.MAIN_WINS["input"].redraw()
        nuqql.win.MAIN_WINS["log"].redraw()
        nuqql.win.MAIN_WINS["list"].process_input(char)
        return True

    # list window is also inactive -> user quit
    return False


def start(stdscr, func):
    """
    Start UI and run provided function
    """

    # save stdscr
    nuqql.win.MAIN_WINS["screen"] = stdscr

    # configuration
    stdscr.timeout(10)

    # clear everything
    stdscr.clear()
    stdscr.refresh()

    # make sure window config is loaded
    nuqql.config.init_win()

    # create main windows
    nuqql.conversation.create_main_windows()

    # run function provided by caller
    func()


def init(func):
    """
    Initialize UI
    """

    curses.wrapper(start, func)
