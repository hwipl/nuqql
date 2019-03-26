"""
Main part of nuqql.
"""

#############
# Main Part #
#############

import configparser
import datetime
import curses
import signal

import nuqql.backend
import nuqql.ui


####################
# CONFIG FILE PART #
####################

class Config:
    """
    Class for configuration.
    """
    # TODO: decide where to put this and if it should stay like this

    def __init__(self, config_file="nuqql.conf"):
        # init parser for config file
        self.config = configparser.ConfigParser()
        self.config_file = config_file

        # key mapping/binding
        self.keymap = {}
        self.keybind = {}

        # init keybinds
        self.keybind["list_win"] = {}
        self.keybind["input_win"] = {}
        self.keybind["log_win"] = {}

        # accounts
        self.account = {}

    def del_account(self, account):
        """
        Delete an account
        """

        del self.account[account.name]

    def add_keymap(self, key, name):
        """
        Add a keymap.
        """

        self.keymap[key] = name

    def del_keymap(self, key):
        """
        Delete a keymap.
        """

        del self.keymap[key]

    def add_keybind(self, context, name, action):
        """
        Add a Keybind.
        """

        self.keybind[context][name] = action

    def del_keybind(self, context, name):
        """
        Delete a keybind.
        """

        del self.keybind[context][name]

    def read_config(self):
        """
        Read config from file.
        """

        self.config.read(self.config_file)
        for section in self.config.sections():
            if section == "list_win":
                pass
            elif section == "log_win":
                pass
            elif section == "input_win":
                pass
            elif section == "purpled":
                pass
            else:
                # everything else is treated as account settings
                pass

    def write_config(self):
        """
        Write config to file.
        """

        with open(self.config_file, "w") as configfile:
            self.config.write(configfile)


###############
# MAIN (LOOP) #
###############


def main_loop(stdscr):
    """
    Main loop of nuqql.
    """

    # load config
    config = Config()
    config.read_config()

    # initialize UI
    nuqql.ui.init(stdscr)

    # init and start all backends
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = nuqql.ui.LogMessage(now, "nuqql", "Start backends.")
    nuqql.ui.LOG_WIN.add(log_msg)
    nuqql.backend.start_backends()
    for backend in nuqql.backend.BACKENDS.values():
        # start this backend's server
        # now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # log_msg = nuqql.ui.LogMessage(now, "nuqql",
        #                               "Start backend \"{0}\".".format(
        #                                   backend.name))
        # nuqql.ui.LOG_WIN.add(log_msg)
        # backend.start_server()

        # start this backend's client
        # now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # log_msg = nuqql.ui.LogMessage(now, "nuqql", "Start client.")
        # nuqql.ui.LOG_WIN.add(log_msg)
        # backend.init_client()

        # collect accounts from this backend
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = nuqql.ui.LogMessage(now, "nuqql", "Collecting accounts.")
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
