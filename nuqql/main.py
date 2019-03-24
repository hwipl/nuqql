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

    def addAccount(self, account):
        self.account[account.name] = account

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
    max_y, max_x = stdscr.getmaxyx()
    stdscr.timeout(10)

    stdscr.clear()
    stdscr.refresh()

    # load config
    config = Config()
    config.readConfig()

    # create main windows
    list_win, log_win, input_win = nuqql.ui.createMainWindows(config, stdscr,
                                                              max_y, max_x)

    # start purpled
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = nuqql.ui.LogMessage(log_win, now, None, "nuqql", True,
                                  "Start purpled.")
    log_win.add(log_msg)
    nuqql.backend.initBackends(config)
    # server = nuqql.backend.PurpledServer()
    backend = nuqql.backend.backends["purpled"]
    # server.start()
    backend.startServer()

    # start purpled client
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = nuqql.ui.LogMessage(log_win, now, None, "nuqql", True,
                                  "Start client.")
    log_win.add(log_msg)
    # client = nuqql.backend.PurpledClient(config)
    # client.initClient()
    backend.initClient()

    # collect accounts from purpled
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = nuqql.ui.LogMessage(log_win, now, None, "nuqql", True,
                                  "Collecting accounts.")
    log_win.add(log_msg)
    # client.accountsClient()
    backend.accountsClient()

    # start main loop
    while True:
        # wait for user input
        try:
            ch = stdscr.get_wch()
        except curses.error:
            # no user input...
            ch = None

        # check size and redraw windows if necessary
        max_y, max_x = nuqql.ui.resizeMainWindow(stdscr, list_win, log_win,
                                                 input_win,
                                                 nuqql.ui.conversation, max_y,
                                                 max_x)

        # update buddies
        # nuqql.backend.updateBuddies(config, client, log_win)
        nuqql.backend.updateBuddies(config, backend, log_win)

        # handle network input
        # nuqql.backend.handleNetwork(config, client, nuqql.ui.conversation,
        nuqql.backend.handleNetwork(config, backend, nuqql.ui.conversation,
                                    list_win, log_win)

        # handle user input
        if ch is None:
            # NO INPUT, keep waiting for input...
            continue

        # pass user input to active conversation
        conv_active = False
        for conv in nuqql.ui.conversation:
            if conv.input_win.active:
                # conv.input_win.processInput(ch, client)
                conv.input_win.processInput(ch, backend)
                conv_active = True
                break
        # if no conversation is active pass input to list window
        if not conv_active:
            if input_win.active:
                # input_win.processInput(ch, client)
                input_win.processInput(ch, backend)
            elif list_win.active:
                # TODO: improve ctrl window handling?
                input_win.redraw()
                log_win.redraw()
                list_win.processInput(ch)
            else:
                # list window is also inactive -> user quit
                # client.exitClient()
                # server.stop()
                backend.exitClient()
                backend.stopServer()
                break


# main entry point
def run():
    # ignore SIGINT
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    curses.wrapper(main_loop)
