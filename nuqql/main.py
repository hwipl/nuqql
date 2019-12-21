"""
Main part of nuqql.
"""

#############
# Main Part #
#############

import argparse
import signal

import nuqql.backend
import nuqql.ui

VERSION = "0.8"


###############
# MAIN (LOOP) #
###############

def parse_args() -> None:
    """
    Parse command line arguments.
    """

    # if we add more, consider moving it to config or somewhere else
    parser = argparse.ArgumentParser(
        description="Run nuqql command line instant messenger.")
    parser.add_argument("--version", action="version", version=VERSION)
    parser.parse_args()


def main_loop() -> str:
    """
    Main loop of nuqql.
    """

    try:
        # init and start all backends
        nuqql.backend.start_backends(VERSION)

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
    parse_args()

    # ignore SIGINT
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # initialize ui and run main_loop
    nuqql.ui.init(main_loop)
