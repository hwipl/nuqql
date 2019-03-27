"""
Main part of nuqql.
"""

#############
# Main Part #
#############

import datetime
import curses
import signal

import nuqql.backend
import nuqql.ui


###############
# MAIN (LOOP) #
###############

def main_loop(stdscr):
    """
    Main loop of nuqql.
    """

    # initialize UI
    nuqql.ui.init(stdscr)

    # init and start all backends
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = nuqql.ui.LogMessage(now, "nuqql", "Start backends.")
    nuqql.ui.LOG_WIN.add(log_msg)
    nuqql.backend.start_backends()
    for backend in nuqql.backend.BACKENDS.values():
        # collect accounts from this backend
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = nuqql.ui.LogMessage(
            now, "nuqql", "Collecting accounts for \"{0}\".".format(
                backend.name))
        nuqql.ui.LOG_WIN.add(log_msg)
        backend.client.send_accounts()

    # start main loop
    while True:
        # wait for user input and get timeout or character to process
        char = nuqql.ui.read_input()

        # check size and redraw windows if necessary
        nuqql.ui.resize_main_window()

        # update buddies
        nuqql.backend.update_buddies()

        # handle network input
        nuqql.backend.handle_network()

        # handle user input
        if char is None:
            # NO INPUT, keep waiting for input...
            continue

        # pass user input to active conversation
        conv_active = False
        for conv in nuqql.ui.CONVERSATIONS:
            if conv.input_win.active:
                conv.input_win.process_input(char)
                conv_active = True
                break
        # if no conversation is active pass input to command or list window
        if not conv_active:
            if nuqql.ui.INPUT_WIN.active:
                # command mode
                nuqql.ui.INPUT_WIN.process_input(char)
            elif nuqql.ui.LIST_WIN.active:
                # list window navigation
                # TODO: improve ctrl window handling?
                nuqql.ui.INPUT_WIN.redraw()
                nuqql.ui.LOG_WIN.redraw()
                nuqql.ui.LIST_WIN.process_input(char)
            else:
                # list window is also inactive -> user quit
                nuqql.backend.stop_backends()
                break


# main entry point
def run():
    """
    Main entry point of nuqql
    """

    # ignore SIGINT
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    curses.wrapper(main_loop)
