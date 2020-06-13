"""
Main part of nuqql.
"""

import signal

import nuqql.backend
import nuqql.config
import nuqql.ui



# main loop of nuqql
def main_loop() -> str:
    """
    Main loop of nuqql.
    """

    try:
        # init and start all backends
        nuqql.backend.start_backends()

        # loop as long as user does not quit
        while nuqql.ui.handle_input():
            # update buddies
            nuqql.backend.update_buddies()

            # handle network input
            nuqql.backend.handle_network()
    finally:
        # shut down backends
        nuqql.backend.stop_backends()

    # quit nuqql
    return ""


# main entry point
def run() -> None:
    """
    Main entry point of nuqql
    """

    # parse command line arguments
    nuqql.config.parse_args()

    # ignore SIGINT
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # initialize ui and run main_loop
    nuqql.ui.init(main_loop)
