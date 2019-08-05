"""
Nuqql UI Log Windows
"""

from types import SimpleNamespace

import nuqql.inputwin
import nuqql.win


class LogWin(nuqql.win.Win):
    """
    Class for Log Windows
    """

    def __init__(self, config, conversation, title):
        nuqql.win.Win.__init__(self, config, conversation, title)

        # window in zoomed/fullscreen mode
        self.zoomed = False

        # list entries/message log
        self.list = []

        # dialog window for user input
        self.dialog = None

        # string to search for
        self.search_text = ""

        # user's view of the log
        self.view = SimpleNamespace(
            begin=-1,
            cur=-1
        )

    def add(self, entry):
        """
        Add entry to internal list
        """

        # add entry to own list via base class function
        self.list_add(self.list, entry)

    @staticmethod
    def _get_num_log_lines(log_slice, pad_size_x):
        """
        Get number of lines in log, depending on number of messages and how
        many lines each message uses.
        """

        # init line count and start index
        lines = 0

        for msg in log_slice:
            parts = msg.read(mark_read=False).split("\n")
            lines += len(parts) - 1
            for part in parts:
                if len(part) >= pad_size_x:
                    lines += len(part) // pad_size_x

        return lines

    def _get_log_view(self, props):
        """
        Get a slice of the log in the current view of the pad
        """

        if self.view.begin == -1:
            start = len(self.list) - (props.win_size_y - props.pad_y_delta)
            end = len(self.list)
            self.view.cur = start
        else:
            start = self.view.begin
            end = props.win_size_y - props.pad_y_delta
            self.view.cur = start

        log_slice = []
        for index, msg in enumerate(self.list[start:]):
            if index > end:
                break
            log_slice.append(msg)

        return log_slice

    def _print_log(self, props):
        """
        dump log messages and resize pad according to new lines added
        """

        # make sure lines fit into pad
        log_slice = self._get_log_view(props)
        lines = self._get_num_log_lines(log_slice, props.pad_size_x)
        self.pad.resize(lines + 1, props.pad_size_x)

        for index, msg in enumerate(log_slice):
            # set colors and attributes for message:
            if not msg.own:
                # message from buddy
                if msg.is_read:
                    # old message
                    self.pad.attrset(self.config.attr["log_win_text_peer_old"])
                else:
                    # new message
                    self.pad.attrset(self.config.attr["log_win_text_peer_new"])
            else:
                # message from you
                if msg.is_read:
                    # old message
                    self.pad.attrset(self.config.attr["log_win_text_self_old"])
                else:
                    # new message
                    self.pad.attrset(self.config.attr["log_win_text_self_new"])

            # output message
            if index < len(log_slice) - 1:
                self.pad.addstr(msg.read())
            else:
                self.pad.addstr(msg.read()[:-1])

    def _get_properties(self):
        """
        Get window/pad properties, depending on max size and zoom
        """

        props = SimpleNamespace()
        props.max_y, props.max_x = nuqql.win.MAIN_WINS["screen"].getmaxyx()
        if self.zoomed:
            # window is currently zoomed
            props.pos_y, props.pos_x = 0, 0
            props.pos_y_off, props.pos_x_off = 1, 0
            props.win_size_y, props.win_size_x = props.max_y, props.max_x
            props.pad_size_y, props.pad_size_x = (props.max_y - 2, props.max_x)
            props.pad_y_delta, props.pad_x_delta = 2, 0
        else:
            # window is not zoomed
            props.pos_y, props.pos_x = self.config.get_pos()
            props.pos_y_off, props.pos_x_off = 1, 1
            props.win_size_y, props.win_size_x = self.config.get_size()
            # use actual pad size, it will be resized later if necessary
            props.pad_size_y, props.pad_size_x = self.pad.getmaxyx()
            props.pad_y_delta, props.pad_x_delta = 2, 2

        return props

    def _pad_refresh(self, props):
        """
        Helper for running move_pad(), check_borders(), and pad.refresh()
        """
        self._move_pad()
        self._check_borders()
        self.pad.refresh(self.state.pad_y, self.state.pad_x,
                         props.pos_y + props.pos_y_off,
                         props.pos_x + props.pos_x_off,
                         props.pos_y + props.win_size_y - props.pad_y_delta,
                         props.pos_x + props.win_size_x - props.pad_x_delta)

    def redraw_pad(self):
        # if terminal size is invalid, stop here
        if not self.config.is_terminal_valid():
            return

        # screen/pad properties
        props = self._get_properties()

        # if window was resized, resize pad size according to new window size
        if props.pad_size_x != props.win_size_x - props.pad_x_delta:
            props.pad_size_x = props.win_size_x - props.pad_x_delta
            self.pad.resize(props.pad_size_y, props.pad_size_x)
        if props.pad_size_y != props.win_size_y - props.pad_y_delta:
            props.pad_size_y = props.win_size_y - props.pad_y_delta
            self.pad.resize(props.pad_size_y, props.pad_size_x)
            self.state.pad_y = 0  # reset pad position

        # print log
        self.pad.erase()
        self._print_log(props)

        # check if visible part of pad needs to be moved and display it
        self.state.cur_y, self.state.cur_x = self.pad.getyx()
        self._pad_refresh(props)

    def _cursor_top(self, *args):
        # jump to first line in log
        if self.view.cur > 0:
            # view is not at the top yet, so move it there
            self.view.begin = 0
            self.redraw_pad()

        # move cursor to top
        self.state.cur_y, self.state.cur_x = 0, 0
        self.pad.move(self.state.cur_y, self.state.cur_x)
        props = self._get_properties()
        self._pad_refresh(props)

    def _cursor_bottom(self, *args):
        # jump to last line in log
        props = self._get_properties()
        view_size = props.win_size_y - props.pad_y_delta

        if self.view.cur < len(self.list) - view_size:
            # view is not at the bottom yet, so move it there
            self.view.begin = len(self.list) - view_size
            self.redraw_pad()

        # move cursor to bottom
        self.state.cur_y, self.state.cur_x = self.pad.getmaxyx()[0] - 1, 0
        self.pad.move(self.state.cur_y, self.state.cur_x)
        props = self._get_properties()
        self._pad_refresh(props)

    def _cursor_page_up(self, *args):
        # move cursor up one page until first entry in log
        props = self._get_properties()
        view_size = props.win_size_y - props.pad_y_delta

        if self.view.cur > 0:
            # view can be moved further towards top, so move it
            self.view.begin = max(0, self.view.cur - view_size)
            self.redraw_pad()

        # move cursor to top
        self.state.cur_y, self.state.cur_x = 0, 0
        self.pad.move(self.state.cur_y, self.state.cur_x)
        props = self._get_properties()
        self._pad_refresh(props)

    def _cursor_page_down(self, *args):
        # move cursor down one page until last entry in log
        props = self._get_properties()
        view_size = props.win_size_y - props.pad_y_delta

        if self.view.cur < len(self.list) - view_size:
            # view can be moved further towards bottom, so move it
            self.view.begin = min(len(self.list) - view_size,
                                  self.view.cur + view_size)
            self.redraw_pad()

        # move cursor to bottom
        self.state.cur_y, self.state.cur_x = self.pad.getmaxyx()[0] - 1, 0
        self.pad.move(self.state.cur_y, self.state.cur_x)
        props = self._get_properties()
        self._pad_refresh(props)

    def _cursor_up(self, *args):
        # move cursor up until first entry in list
        if self.state.cur_y > 0:
            # inside current view, simply move cursor up
            self.state.cur_y, self.state.cur_x = self.state.cur_y - 1, 0

        elif self.view.cur > 0:
            # at top of current view, move view up
            self.view.begin = self.view.cur - 1
            self.redraw_pad()
            self.state.cur_y, self.state.cur_x = 0, 0

        # move cursor up
        self.pad.move(self.state.cur_y, self.state.cur_x)
        props = self._get_properties()
        self._pad_refresh(props)

    def _cursor_down(self, *args):
        # move cursor down until end of list
        props = self._get_properties()
        lines = self.pad.getmaxyx()[0] - 1
        view_size = props.win_size_y - props.pad_y_delta

        if self.state.cur_y < lines:
            # inside current view, simply move cursor down
            self.state.cur_y, self.state.cur_x = self.state.cur_y + 1, 0

        elif self.view.cur < len(self.list) - view_size:
            # at bottom of current view, move view down
            self.view.begin = self.view.cur + 1
            self.redraw_pad()
            self.state.cur_y, self.state.cur_x = self.pad.getmaxyx()[0] - 1, 0

        # move cursor down
        self.pad.move(self.state.cur_y, self.state.cur_x)
        props = self._get_properties()
        self._pad_refresh(props)

    def _zoom_win(self, *args):
        """
        Zoom in and out of log window
        """

        # get positions and sizes for zoomed and normal mode
        if self.zoomed:
            self.zoomed = False
        else:
            self.zoomed = True
        props = self._get_properties()

        # resize window and pad
        self.resize_win(props.win_size_y, props.win_size_x)
        self.move_win(props.pos_y, props.pos_x)
        self.pad.resize(props.win_size_y - props.pad_y_delta,
                        props.win_size_x - props.pad_x_delta)
        self._move_pad()
        self._check_borders()

        # redraw everything
        if self.zoomed:
            self.redraw()
        else:
            nuqql.win.MAIN_WINS["screen"].clear()
            nuqql.win.MAIN_WINS["screen"].refresh()
            self.conversation.wins.list_win.redraw()
            self.conversation.wins.log_win.redraw()
            self.conversation.wins.input_win.redraw()

    def _go_back(self, *args):
        # if window was zoomed, switch back to normal view
        if self.zoomed:
            self._zoom_win()

        # reactivate input window
        self.state.active = True
        self.conversation.wins.input_win.state.active = True

        # show last messages
        self.view.begin = -1

        # redraw pad to display messages received in the meantime...
        self.redraw_pad()

        # ...and clear notifications for these messages
        self.conversation.clear_notifications()

    def _search(self, *args):
        """
        Search: Start a new search dialog
        """

        self.dialog = nuqql.inputwin.LogDialogInputWin(
            self.conversation.wins.input_win.config, self.conversation,
            "Search History")
        self.dialog.redraw()

    def _process_dialog_input(self, char):
        """
        Process user input in dialog mode
        """

        self.dialog.process_input(char)

    def _search_next(self, *args):
        """
        Search for next match
        """

        # skip this if we are not in search mode
        if self.search_text == "":
            return

        # init
        props = self._get_properties()

        # search views for text until first view
        while self.view.cur >= 0:
            # search current view for text until first line
            while self.state.cur_y >= 0:
                cur_text = self.pad.instr(self.state.cur_y, 0,
                                          self.state.cur_x).decode()
                index = cur_text.rfind(self.search_text)
                if index != -1:
                    # found it, stop here
                    self.pad.move(self.state.cur_y, index)
                    self.state.cur_y, self.state.cur_x = self.pad.getyx()

                    self._pad_refresh(props)
                    return

                # keep searching in next line
                self.state.cur_y -= 1
                self.state.cur_x = props.pad_size_x

            # reached end of view, move view further up
            self._cursor_page_up()
            self.state.cur_y, self.state.cur_x = self.pad.getmaxyx()

    def search_next(self):
        """
        Helper for calling search from other windows
        """

        self._search_next()

    def _search_prev(self, *args):
        """
        Search for previous match
        """

        # skip this if we are not in search mode
        if self.search_text == "":
            return

        # init
        props = self._get_properties()
        view_size = props.win_size_y - props.pad_y_delta

        # if we are already on a match, skip it
        if self.pad.instr(self.state.cur_y, self.state.cur_x,
                          len(self.search_text)).decode() == self.search_text:
            self.state.cur_x += len(self.search_text)

        # search views for text until last view
        while self.view.cur <= len(self.list) - view_size:
            # search current view for text until end of view
            while self.state.cur_y <= self.pad.getmaxyx()[0]:
                cur_text = self.pad.instr(self.state.cur_y, self.state.cur_x,
                                          props.pad_size_x).decode()
                index = cur_text.find(self.search_text)

                # found it, stop here
                if index != -1:
                    self.pad.move(self.state.cur_y, self.state.cur_x + index)
                    self.state.cur_y, self.state.cur_x = self.pad.getyx()

                    self._pad_refresh(props)
                    return

                # keep searching
                self.state.cur_y += 1
                self.state.cur_x = 0    # set it to first position in line

            # reached end of view, move view further down
            if self.view.cur == len(self.list) - view_size:
                # reached bottom already
                break
            self._cursor_page_down()
            self.state.cur_y, self.state.cur_x = 0, 0

    def process_input(self, char):
        """
        Process user input
        """

        self.state.cur_y, self.state.cur_x = self.pad.getyx()

        # dialog mode
        if self.dialog:
            self._process_dialog_input(char)
            return

        # look for special key mappings in keymap
        self.handle_keybinds(char)

        # display changes in the pad
        # TODO: switch this back on and remove redraw code from other methods?
        # self.redraw_pad()