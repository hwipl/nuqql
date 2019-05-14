#!/usr/bin/env python3

import curses
import curses.ascii

CHAR = ""


def main(stdscr):
    while True:
        global CHAR
        CHAR = stdscr.get_wch()
        ch = CHAR
        if type(ch) is not str:
            msg = "int: " + str(ch) + "\n"
        else:
            if ch == "\0":
                continue
            msg = "char: " + ch
            msg += " ord: " + str(ord(ch))
            msg += " ascii: " + curses.ascii.ascii(ch)
            msg += " crtl: " + curses.ascii.ctrl(ch)
            msg += " alt: " + curses.ascii.alt(ch) + "\n"
        stdscr.addstr(msg)


try:
    curses.wrapper(main)
except Exception as e:
    print("last input: \"{}\"".format(CHAR))
    print(e)
