#!/usr/bin/env python3

import curses
import curses.ascii


def main(stdscr):
    while True:
        ch = stdscr.get_wch()
        if type(ch) is not str:
            msg = "int: " + str(ch) + "\n"
        else:
            msg = "char: " + ch
            msg += " ord: " + str(ord(ch))
            msg += " ascii: " + curses.ascii.ascii(ch)
            msg += " crtl: " + curses.ascii.ctrl(ch)
            msg += " alt: " + curses.ascii.alt(ch) + "\n"
        stdscr.addstr(msg)


curses.wrapper(main)
