"""
Main part of nuqql.
"""

#############
# Main Part #
#############

import datetime
import signal

import nuqql.backend
import nuqql.ui


###############
# MAIN (LOOP) #
###############

def main_loop():
    """
    Main loop of nuqql.
    """

    # init and start all backends
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = nuqql.ui.LogMessage(now, "nuqql", "Start backends.")
    nuqql.ui.LOG_WIN.add(log_msg)
    nuqql.backend.start_backends()

    # loop as long as user does not quit
    while nuqql.ui.handle_input():
        # update buddies
        nuqql.backend.update_buddies()

        # handle network input
        nuqql.backend.handle_network()


# main entry point
def run():
    """
    Main entry point of nuqql
    """

    # ignore SIGINT
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # initialize ui and run main_loop
    nuqql.ui.init(main_loop)
