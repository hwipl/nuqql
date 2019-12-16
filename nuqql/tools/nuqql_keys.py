#!/usr/bin/env python3

"""
Nuqql-keys: helper script for nuqql keymaps and keybinds.
"""

import curses
import curses.ascii
import configparser

from pathlib import Path
from typing import Any, Dict

# default keymap for special keys
DEFAULT_KEYMAP = {
    "KEY_ENTER":        ord("\n"),
    "KEY_ESC":          curses.ascii.ESC,
    "KEY_RIGHT":        curses.KEY_RIGHT,
    "KEY_LEFT":         curses.KEY_LEFT,
    "KEY_DOWN":         curses.KEY_DOWN,
    "KEY_UP":           curses.KEY_UP,
    "KEY_H":            ord("h"),
    "KEY_J":            ord("j"),
    "KEY_K":            ord("k"),
    "KEY_L":            ord("l"),
    "KEY_N":            ord("n"),
    "KEY_P":            ord("p"),
    "KEY_Q":            ord("q"),
    "KEY_TAB":          ord("\t"),
    "KEY_CTRL_A":       ord(curses.ascii.ctrl("a")),
    "KEY_CTRL_B":       ord(curses.ascii.ctrl("b")),
    "KEY_CTRL_E":       ord(curses.ascii.ctrl("e")),
    "KEY_CTRL_K":       ord(curses.ascii.ctrl("k")),
    "KEY_CTRL_N":       ord(curses.ascii.ctrl("n")),
    "KEY_CTRL_O":       ord(curses.ascii.ctrl("o")),
    "KEY_CTRL_U":       ord(curses.ascii.ctrl("u")),
    "KEY_CTRL_V":       ord(curses.ascii.ctrl("v")),
    "KEY_CTRL_X":       ord(curses.ascii.ctrl("x")),
    "KEY_DEL":          curses.ascii.DEL,
    "KEY_DC":           curses.KEY_DC,
    "KEY_HOME":         curses.KEY_HOME,
    "KEY_END":          curses.KEY_END,
    "KEY_PAGE_UP":      curses.KEY_PPAGE,
    "KEY_PAGE_DOWN":    curses.KEY_NPAGE,
    "KEY_F9":           curses.KEY_F9,
    "KEY_F10":          curses.KEY_F10,
    "KEY_/":            ord("/"),
}


def _write_keymap_to_file(keymap: Dict[str, Any]) -> None:
    """
    Write keymap to nuqql keymap configuration file
    """

    # read config file if it exists
    config_file = Path.home() / ".config/nuqql/config.ini"
    config = configparser.ConfigParser()
    config.optionxform = lambda option: option  # type: ignore
    config.read(config_file)

    # write (updated) config to file again
    config["keymap"] = keymap
    with open(config_file, "w+") as configfile:
        config.write(configfile)


def go_restore_default_keymap(win: Any) -> None:
    """
    Restore default nuqql keymap configuration
    """

    win.erase()
    try:
        win.addstr(("<Press any key to restore default keymap, "
                    "CTRL-C to abort>"))
        win.get_wch()
    except (curses.error, KeyboardInterrupt):
        return

    # write keymap to config file
    _write_keymap_to_file(DEFAULT_KEYMAP)


def go_configure_keymap(win: Any) -> None:
    """
    Configure nuqql keymap
    """

    keymap = {}
    for key in DEFAULT_KEYMAP:
        # clear screen and get next key
        win.erase()
        win.addstr("Enter key {}:".format(key))
        try:
            char = win.get_wch()
        except curses.error:
            continue
        except KeyboardInterrupt:
            return

        # get key number if possible
        if isinstance(char, str):
            try:
                key_num = ord(char)
            except TypeError:
                key_num = int(char)
        else:
            key_num = char

        # store key
        keymap[key] = key_num

    # print keymap
    win.erase()
    for key, value in keymap.items():
        try:
            win.addstr("Key {} (default: {}): {}\n".format(
                key, DEFAULT_KEYMAP[key], value))
        except curses.error:
            pass

    # wait for keypress and return
    try:
        win.addstr("<Press any key to write config, CTRL-C to abort>")
        char = win.get_wch()
    except curses.error:
        pass
    except KeyboardInterrupt:
        return

    # write keymap to config file
    _write_keymap_to_file(keymap)


def go_key_numbers(win: Any) -> None:
    """
    Read input key and ouput its number if possible
    """

    # output strings
    key_fmt = "Key number: {}"
    no_key_fmt = "No key number: {}"
    abort_text = "Press CTRL-C to abort and return to menu\n"
    enter_text = "<enter key>"

    # clear old window content
    win.erase()
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
        win.erase()
        win.addstr(abort_text)
        win.addstr(msg)


def go_menu(win: Any) -> None:
    """
    Print menu to screen
    """

    # text to display
    menu_text = (
        "Menu:",
        "p)  print key numbers",
        "c)  configure keymap",
        "r)  restore default keymap",
        "q)  quit"
    )

    while True:
        try:
            # output menu
            win.erase()
            win.addstr("\n".join(menu_text))

            # get user input
            char = win.get_wch()
        except curses.error:
            continue

        # handle user input
        if char == "c":
            go_configure_keymap(win)
        if char == "p":
            go_key_numbers(win)
        if char == "q":
            return
        if char == "r":
            go_restore_default_keymap(win)


def run(stdscr: Any) -> None:
    """
    Run everything, called from curses.wrapper
    """

    curses.curs_set(0)  # invisible cursor
    try:
        go_menu(stdscr)
    except KeyboardInterrupt:
        pass


def main() -> None:
    """
    Main function
    """

    curses.wrapper(run)


if __name__ == "__main__":
    main()
