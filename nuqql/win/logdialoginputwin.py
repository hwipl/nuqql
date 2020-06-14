"""
Log Dialog Input Window
"""

from typing import TYPE_CHECKING, Any

from .inputwin import InputWin

if TYPE_CHECKING:   # imports for typing
    # pylint: disable=cyclic-import
    from nuqql.config import WinConfig  # noqa
    from nuqql.conversation import Conversation  # noqa


class LogDialogInputWin(InputWin):
    """
    Class for dialog input from user
    """

    def __init__(self, config: "WinConfig", conversation: "Conversation",
                 title: str) -> None:
        InputWin.__init__(self, config, conversation, title)

        # init displayed msg to last search text
        # TODO: this needs some extra work to properly display the msg
        # self.msg = conversation.wins.log_win.search_text

    def _go_back(self, *args: Any) -> None:
        # do not use window any more
        self.conversation.wins.log_win.dialog = None

        # clear pad and redraw other windows
        self.pad.clear()
        self.conversation.wins.input_win.redraw()
        self.conversation.wins.log_win.redraw()

    def _send_msg(self, *args: Any) -> None:
        # set search string
        self.conversation.wins.log_win.search_text = self.msg

        # go back to log window
        self._go_back()

        # do not search for empty text
        if self.msg == "":
            return

        # jump to first match
        self.conversation.wins.log_win.search_next()
