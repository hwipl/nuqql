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

    def delAccount(self, account):
        del self.account[account.name]

    def addKeymap(self, key, name):
        self.keymap[key] = name

    def delKeymap(self, key):
        del self.keymap[key]

    def addKeybind(self, context, name, action):
        self.keybind[context][name] = action

    def delKeybind(self, context, name):
        del self.keybind[context][name]

    def readConfig(self):
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

    def writeConfig(self):
        with open(self.config_file, "w") as configfile:
            self.config.write(configfile)


###############
# MAIN (LOOP) #
###############


def main_loop(stdscr):
    # load config
    config = Config()
    config.readConfig()

    # initialize UI
    nuqql.ui.init(stdscr)

    # init and start all backends
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = nuqql.ui.LogMessage(now, "nuqql", "Start backends.")
    nuqql.ui.log_win.add(log_msg)
    nuqql.backend.initBackends()
    for backend in nuqql.backend.backends.values():
        # start this backend's server
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = nuqql.ui.LogMessage(now, "nuqql",
                                      "Start backend \"{0}\".".format(
                                          backend.name))
        nuqql.ui.log_win.add(log_msg)
        backend.startServer()

        # start this backend's client
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = nuqql.ui.LogMessage(now, "nuqql", "Start client.")
        nuqql.ui.log_win.add(log_msg)
        backend.initClient()

        # collect accounts from this backend
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = nuqql.ui.LogMessage(now, "nuqql", "Collecting accounts.")
        nuqql.ui.log_win.add(log_msg)
        backend.accountsClient()

    # start main loop
    while True:
        # # wait for user input
        ch = nuqql.ui.readInput()

        # check size and redraw windows if necessary
        nuqql.ui.resizeMainWindow()

        # update buddies
        nuqql.backend.updateBuddies()

        # handle network input
        nuqql.backend.handleNetwork()

        # handle user input
        if ch is None:
            # NO INPUT, keep waiting for input...
            continue

        # pass user input to active conversation
        conv_active = False
        for conv in nuqql.ui.conversations:
            if conv.input_win.active:
                # conv.input_win.processInput(ch, client)
                conv.input_win.processInput(ch)
                conv_active = True
                break
        # if no conversation is active pass input to list window
        if not conv_active:
            if nuqql.ui.input_win.active:
                # input_win.processInput(ch, client)
                nuqql.ui.input_win.processInput(ch)
            elif nuqql.ui.list_win.active:
                # TODO: improve ctrl window handling?
                nuqql.ui.input_win.redraw()
                nuqql.ui.log_win.redraw()
                nuqql.ui.list_win.processInput(ch)
            else:
                # list window is also inactive -> user quit
                nuqql.backend.stopBackends()
                break


# main entry point
def run():
    # ignore SIGINT
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    curses.wrapper(main_loop)
