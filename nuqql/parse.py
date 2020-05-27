"""
Nuqql message parsing
"""

import time
import html
import re

from typing import Tuple


def parse_error_msg(orig_msg: str) -> Tuple:
    """
    Parse "error" message received from backend

    Format:
        "error: %s\r\n"
    """

    error = orig_msg[7:]
    return "error", error


def parse_info_msg(orig_msg: str) -> Tuple:
    """
    Parse "info" message received from backend

    Format:
        "info: %s\r\n"
    """

    info = orig_msg[6:]

    # filter known messages that would spam the log. TODO: change this and/or
    # other message formats/protocol behaviour
    if info.startswith("got buddies for account "):
        # filter got buddies info spam
        return ("", )

    return "info", info


def parse_account_msg(orig_msg: str) -> Tuple:
    """
    Parse "account" message received from backend

    Format:
        "account: %d %s %s %s [%s]\r\n"
    """

    orig_msg = orig_msg[9:]
    part = orig_msg.split(" ")
    acc_id = part[0]
    acc_alias = part[1]
    acc_prot = part[2].lower()
    acc_user = part[3]
    acc_status = part[4]    # ignore [ and ] for now
    return "account", acc_id, acc_alias, acc_prot, acc_user, acc_status


def parse_collect_msg(orig_msg: str) -> Tuple:
    """
    Parse "collect" message received from backend
    """

    # collect response and message have the same message format
    return parse_message_msg(orig_msg)


def parse_message_msg(orig_msg: str) -> Tuple:
    """
    Parse "message" message received from backend
    """

    orig_msg = orig_msg[9:]
    part = orig_msg.split(" ")
    acc = part[0]
    acc_name = part[1]
    tstamp = part[2]
    sender = part[3]
    msg = " ".join(part[4:])
    msg = "\n".join(re.split("<br/?>", msg, flags=re.IGNORECASE))
    msg = html.unescape(msg)

    return "message", acc, acc_name, int(tstamp), sender, msg


def parse_buddy_msg(orig_msg: str) -> Tuple:
    """
    Parse "buddy" message received from backend
    """

    orig_msg = orig_msg[7:]
    # <acc> status: <Offline/Available> name: <name> alias: <alias>
    part = orig_msg.split(" ")
    acc = part[0]
    status = part[2]
    name = part[4]
    alias = part[6]
    return "buddy", acc, status, name, alias


def parse_status_msg(orig_msg: str) -> Tuple:
    """
    Parse "status" message received from backend
    """

    orig_msg = orig_msg[8:]
    # account <acc> status: <status>
    part = orig_msg.split(" ")
    acc = part[1]
    status = part[3]

    return "status", acc, status


def parse_chat_msg(orig_msg: str) -> Tuple:
    """
    Parse "chat" message received from backend
    """

    orig_msg = orig_msg[6:]
    # list: <acc> <chat> <chat_alias> <nick>
    # user: <acc> <chat> <user> <user_alias> <status>
    part = orig_msg.split(" ")
    if len(part) < 5:
        # TODO: return a parsing error or something similar?
        return ("", )

    # common entries
    ctype = part[0]
    acc = part[1]
    chat = part[2]

    # list message
    if ctype == "list:":
        chat_alias = part[3]
        nick = part[4]
        return "chat", ctype, acc, chat, chat_alias, nick

    # user message
    if ctype == "user:" and len(part) >= 6:
        user = part[3]
        user_alias = part[4]
        status = part[5]
        return "chat", ctype, acc, chat, user, user_alias, status

    # msg message
    # TODO: remove duplicate code?
    if ctype == "msg:" and len(part) >= 6:
        tstamp = part[3]
        sender = part[4]
        msg = " ".join(part[5:])
        msg = "\n".join(re.split("<br/?>", msg, flags=re.IGNORECASE))
        msg = html.unescape(msg)
        return "chat", ctype, acc, chat, int(tstamp), sender, msg

    return ("", )


# dictionary for parsing functions, used by parse_msg()
PARSE_FUNCTIONS = {
    "message:": parse_message_msg,
    "collect:": parse_collect_msg,
    "buddy:": parse_buddy_msg,
    "account:": parse_account_msg,
    "status:": parse_status_msg,
    "chat:": parse_chat_msg,
    "info:": parse_info_msg,
    "error:": parse_error_msg,
}


def parse_msg(orig_msg: str) -> Tuple:
    """
    Parse message received from backend,
    calls more specific parsing functions
    """

    # extract message type and then call respectice parsing function
    msg_type = orig_msg.split(maxsplit=1)[0]
    try:
        return PARSE_FUNCTIONS[msg_type](orig_msg)
    except KeyError:
        # return this as parsing error
        acc = "-1"
        acc_name = "error"
        tstamp = int(time.time())
        sender = "<backend>"
        msg = "Error parsing message: " + orig_msg
        return "parsing error", acc, acc_name, tstamp, sender, msg
