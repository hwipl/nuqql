"""
Nuqql UI Windows
"""

import curses
import re

import nuqql.win


class ListWin(nuqql.win.Win):
    """
    Class for List Windows
    """

    def __init__(self, config, conversation, title):
        nuqql.win.Win.__init__(self, config, conversation, title)

        # filter for conversation list
        self.filter = ""

        # list entries/message log
        self.list = []

    def add(self, entry):
        """
        Add entry to internal list
        """

        # add entry to own list via base class function
        self.list_add(self.list, entry)

    def _match_filter(self, name):
        """
        check if name matches the currently active filter
        """

        # no filter -> everything matches
        if not self.filter:
            return True

        # construct regurlar expression
        regex = ".*"
        for char in self.filter[1:].lower():
            regex += "{}.*".format(char)

        # check if any words in name match regular expression
        for word in name.lower().split():
            if re.match(regex, word):
                return True

        return False

    def redraw_pad(self):
        """
        Redraw pad in window
        """

        # if terminal size is invalid, stop here
        if not self.config.is_terminal_valid():
            return

        # screen/pad properties
        pos_y, pos_x = self.config.get_pos()
        win_size_y, win_size_x = self.win.getmaxyx()
        pad_size_y, pad_size_x = self.pad.getmaxyx()
        self.state.cur_y, self.state.cur_x = self.pad.getyx()

        # make sure pad has correct width (after resize)
        if pad_size_x != win_size_x - 2:
            self.pad.resize(pad_size_y, win_size_x - 2)
            pad_size_x = win_size_x - 2

        # store last selected entry
        if self.state.cur_y >= len(self.list):
            # make sure cur_y is still "within" the list. Length difference
            # should be only 1, because buddies get removed individually
            self.state.cur_y = max(0, self.state.cur_y - 1)
        last_selected = self.list[self.state.cur_y]

        # sort list
        self.list.sort()

        # make sure all names fit into pad
        if len(self.list) > pad_size_y - 1:
            self.pad.resize(len(self.list) + 1, pad_size_x)

        # if there is an active conversation or last selected conversation was
        # moved, move cursor to it
        for index, conv in enumerate(self.list):
            if conv.is_active() or conv is last_selected:
                self.state.cur_y = index

        # is there a zoomed log window?
        zoomed_log_win = None

        # print names in list window
        for index, conv in enumerate(self.list):
            # get name of element; cut if it's too long
            name = conv.get_name()
            name = name[:pad_size_x-1] + "\n"

            # set colors depending on backend name
            if conv.backend:
                self.pad.attrset(self.config.attr["list_win_text"][
                    conv.backend.name])
            else:
                self.pad.attrset(self.config.attr["list_win_text"]["default"])

            # print name
            if index == self.state.cur_y:
                # cursor is on conversation, highlight it in list
                self.pad.addstr(index, 0, name, curses.A_REVERSE)
            else:
                # just show the conversation in list
                if self._match_filter(conv.get_name()):
                    self.pad.addstr(index, 0, name)
                else:
                    self.pad.addstr(index, 0, name, curses.A_DIM)

            # check if there is a zoomed conversation
            # TODO: move this into a separate helper?
            if conv.wins.log_win and conv.wins.log_win.zoomed:
                zoomed_log_win = conv.wins.log_win

        # move cursor back to original or active conversation's position
        self.pad.move(self.state.cur_y, self.state.cur_x)

        # check if visible part of pad needs to be moved and display it
        self._move_pad()
        self._check_borders()
        if zoomed_log_win:
            return
        self.pad.refresh(self.state.pad_y, self.state.pad_x,
                         pos_y + 1, pos_x + 1,
                         pos_y + win_size_y - 2,
                         pos_x + win_size_x - 2)

        # if in filter mode, show the filter string as well
        if self.filter:
            self._process_filter_show()

    def _cursor_top(self, *args):
        # jump to first conversation
        if self.state.cur_y > 0:
            self.pad.move(0, 0)

    def _cursor_bottom(self, *args):
        # jump to last conversation
        lines = len(self.list)
        if self.state.cur_y < lines - 1:
            self.pad.move(lines - 1, self.state.cur_x)

    def _cursor_page_up(self, *args):
        # move cursor up one page until first entry in log
        win_size_y, unused_win_size_x = self.win.getmaxyx()

        if self.state.cur_y > 0:
            if self.state.cur_y - (win_size_y - 2) >= 0:
                self.pad.move(self.state.cur_y - (win_size_y - 2),
                              self.state.cur_x)
            else:
                self.pad.move(0, self.state.cur_x)

    def _cursor_page_down(self, *args):
        # move cursor down one page until last entry in log
        win_size_y, unused_win_size_x = self.win.getmaxyx()

        lines = len(self.list)
        if self.state.cur_y < lines:
            if self.state.cur_y + win_size_y - 2 < lines:
                self.pad.move(self.state.cur_y + win_size_y - 2,
                              self.state.cur_x)
            else:
                self.pad.move(lines - 1, self.state.cur_x)

    def _cursor_up(self, *args):
        # move cursor up until first entry in list
        if self.state.cur_y > 0:
            self.pad.move(self.state.cur_y - 1, self.state.cur_x)

    def _cursor_down(self, *args):
        # move cursor down until end of list
        if self.state.cur_y < len(self.list) - 1:
            self.pad.move(self.state.cur_y + 1, self.state.cur_x)

    def _go_next(self, *args):
        # find a new(er) conversation and jump into it
        set_last_used = True
        conv = self.conversation.get_new()
        if not conv:
            conv = self.list[self.state.cur_y].get_next()
            set_last_used = False
        if not conv:
            return
        self.jump_to_conv(conv, set_last_used=set_last_used)

    def _go_prev(self, *args):
        # find older conversation and jump into it
        prev = self.list[self.state.cur_y].get_prev()
        if not prev:
            return

        # deactivate this and switch to other conversation
        prev.wins.list_win.jump_to_conv(prev, set_last_used=False)

    def _go_conv(self, *args):
        # filter conversations and find specific conversation
        self.filter = "/"

    def go_conv(self):
        """
        Helper for other windows for setting the window in filter mode
        """

        self._go_conv()
        self.redraw_pad()

    def _go_log(self, *args):
        # go to conversation's log
        # create windows, if they do not exists
        if not self.list[self.state.cur_y].has_windows():
            self.list[self.state.cur_y].create_windows()
        # activate conversation's history
        self.list[self.state.cur_y].activate_log()

    def _enter(self, *args):
        # enter conversation
        # create windows, if they do not exists
        if not self.list[self.state.cur_y].has_windows():
            self.list[self.state.cur_y].create_windows()
        # activate conversation
        self.list[self.state.cur_y].activate()
        # reset filter
        self.filter = ""

    def _quit(self, *args):
        # quit nuqql
        self.state.active = False   # Exit the while loop

    def _process_filter_up(self):
        # move cursor up to next filter match
        conv_index = self.state.cur_y
        for index, conv in enumerate(self.list[:self.state.cur_y]):
            if self._match_filter(conv.get_name()):
                conv_index = index

        self.pad.move(conv_index, self.state.cur_x)

    def _process_filter_down(self):
        # move cursor down to next filter match
        for index, conv in enumerate(self.list[self.state.cur_y + 1:]):
            if self._match_filter(conv.get_name()):
                self.pad.move(index + self.state.cur_y + 1, self.state.cur_x)
                return

    def _process_filter_nearest(self):
        # move cursor do nearest filter match
        above = -1
        below = -1

        # find matches
        for index, conv in enumerate(self.list):
            if index <= self.state.cur_y and \
               self._match_filter(conv.get_name()):
                above = index
            if index > self.state.cur_y and \
               self._match_filter(conv.get_name()):
                below = index

        # is there a match above current cursor position?
        if above != -1:
            if below == -1:
                self.pad.move(above, self.state.cur_x)
            else:
                # matches above and below, what is nearer to current cursor?
                above_diff = above - self.state.cur_y
                below_diff = self.state.cur_y - below
                if above_diff < below_diff:
                    self.pad.move(above, self.state.cur_x)
                else:
                    self.pad.move(below, self.state.cur_x)
            return

        # nothing above current cursor position, below?
        if below != -1:
            self.pad.move(below, self.state.cur_x)

    def _process_filter_show(self):
        """
        Show current filter string
        """

        if not self.filter:
            # show window border again
            self.redraw()
            return

        # TODO: use config get_size or something?
        max_y, max_x = self.win.getmaxyx()
        show = self.filter.ljust(max_x - 4, " ")
        self.win.addnstr(max_y - 1, 2, show, max_x - 4)
        self.win.refresh()

    def _process_filter_input(self, char):
        """
        Process input from user in filter mode
        """

        # look for special key mappings in keymap or process as text
        # TODO: add another keybind dict or spawn a special listwin instance
        # or something?
        if char == curses.KEY_UP:
            # go to next match above
            self._process_filter_up()

        elif char == curses.KEY_DOWN:
            # go to next match below
            self._process_filter_down()

        elif char == chr(curses.ascii.ESC):
            # reset filter
            self.filter = ""
            self._process_filter_show()

        elif char == "\n":
            # create windows, if they do not exists
            if not self.list[self.state.cur_y].has_windows():
                self.list[self.state.cur_y].create_windows()

            # activate conversation
            self.list[self.state.cur_y].activate()

            # reset filter
            self.filter = ""
            self._process_filter_show()

        elif char == chr(curses.ascii.DEL):
            # delete character from filter
            self.filter = self.filter[:-1]
            self._process_filter_nearest()
            if not self.filter:
                # if filter is now empty, make sure it is not shown any more
                self._process_filter_show()

        else:
            # add character to filter
            try:
                self.filter += char
                self._process_filter_nearest()
                # self._process_filter_show()
            except (ValueError, TypeError):
                pass

        # display changes in the pad
        self.redraw_pad()

    def process_input(self, char):
        """
        Process input from user (character)
        """

        self.state.cur_y, self.state.cur_x = self.pad.getyx()

        # check if we are in filter mode
        if self.filter:
            self._process_filter_input(char)
            return

        # look for special key mappings in keymap
        self.handle_keybinds(char)

        # display changes in the pad
        self.redraw_pad()

    def jump_to_conv(self, conversation, set_last_used=True):
        """
        Jump directly into specified conversation
        """

        # create conversation's windows if necessary
        if not conversation.has_windows():
            conversation.create_windows()

        # move cursor to this conversation
        for index, conv in enumerate(self.list):
            if conv is conversation:
                self.state.cur_y = index
                self.pad.move(self.state.cur_y, self.state.cur_x)

        # finally, activate conversation
        conversation.activate(set_last_used=set_last_used)
