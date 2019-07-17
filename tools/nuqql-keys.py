#!/usr/bin/env python3

import curses
import curses.ascii


def go_key_numbers(win):
    """
    Read input key and ouput its number if possible
    """

    # output strings
    key_fmt = "Key number: {}"
    no_key_fmt = "No key number: {}"
    abort_text = "Press CTRL-C to abort and return to menu\n"
    enter_text = "<enter key>"

    # clear old window content
    win.clear()
    win.addstr(abort_text)
    win.addstr(enter_text)

    while True:
        # read next character until keyboard interrupt
        try:
            char = win.get_wch()
        except curses.error:
            continue
        except KeyboardInterrupt:
            return

        # construct ouput message...
        msg = ""
        if isinstance(char, str):
            try:
                msg = key_fmt.format(ord(char))
            except TypeError:
                msg = no_key_fmt.format(char)
        else:
            msg = key_fmt.format(char)

        # ... and print it
        win.clear()
        win.addstr(abort_text)
        win.addstr(msg)


def go_menu(win):
    """
    Print menu to screen
    """

    # text to display
    menu_text = (
        "Menu:",
        "p)  print keys",
        "q)  quit"
    )

    while True:
        try:
            # output menu
            win.clear()
            win.addstr("\n".join(menu_text))

            # get user input
            char = win.get_wch()
        except curses.error:
            continue

        # handle user input
        if char == "p":
            go_key_numbers(win)
        if char == "q":
            return


def main(stdscr):
    """
    Main function
    """

    try:
        go_menu(stdscr)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    curses.wrapper(main)
