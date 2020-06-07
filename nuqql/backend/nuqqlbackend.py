"""
Dummy Nuqql Backend
"""

import logging

from pathlib import Path
from typing import Callable, List

from .backend import Backend

logger = logging.getLogger(__name__)


class NuqqlBackend(Backend):
    """
    Class for the nuqql dummy backend
    """

    def __init__(self, name: str) -> None:
        Backend.__init__(self, name)
        self.version = ""

        # function for (re)starting backends
        self.restart_func: Callable[[str], None]

    def _handle_nuqql_global_status(self, parts: List[str]) -> None:
        """
        Handle nuqql command: global-status
        Call getter and setter funcions
        """

        if not parts:
            return
        sub_command = parts[0]
        if sub_command == "set":
            if len(parts) < 2:
                return
            self._handle_nuqql_global_status_set(parts[1])
        elif sub_command == "get":
            self._handle_nuqql_global_status_get()

    def _handle_nuqql_global_status_set(self, status: str) -> None:
        """
        Handle nuqql command: global-status set
        Set status and store it in global_status file
        """

        # only use the first word as status
        if not status or status == "":
            return

        logger.debug("setting global status to %s", status)

        # write status
        self._write_global_status(status)

        # set status in all backends and their accounts
        for backend in self.backends.values():
            for acc in backend.accounts.values():
                if backend.client:
                    backend.client.send_status_set(acc.aid, status)

        # log message
        msg = "global-status: " + status
        if self.conversation:
            self.conversation.log("nuqql", msg)

    def _handle_nuqql_global_status_get(self) -> None:
        """
        Handle nuqql command: global-status get
        Read status from global_status file
        """

        logger.debug("getting global status")

        # read status
        status = self.read_global_status()
        if status == "":
            return
        logger.debug("global status is %s", status)

        # log message
        msg = "global-status: " + status
        if self.conversation:
            self.conversation.log("nuqql", msg)

    @staticmethod
    def _write_global_status(status: str) -> None:
        """
        Write global status to global_status file
        """

        logger.debug("writing global status %s to file", status)

        # write status to file
        global_status_dir = str(Path.home()) + "/.config/nuqql"
        Path(global_status_dir).mkdir(parents=True, exist_ok=True)
        global_status_file = global_status_dir + "/global_status"
        line = status + "\n"
        lines = []
        lines.append(line)
        with open(global_status_file, "w+") as status_file:
            status_file.writelines(lines)

    def _handle_stop(self, parts: List[str]) -> None:
        """
        Handle stop command, stop a backend
        """

        if not parts:
            return

        backend_name = parts[0]
        logger.debug("stopping backend %s", backend_name)
        if backend_name in self.backends:
            self.backends[backend_name].stop()

    def _handle_start(self, parts: List[str]) -> None:
        """
        Handle start command, start a backend
        """

        if not parts:
            return

        backend_name = parts[0]
        logger.debug("starting backend %s", backend_name)
        assert self.restart_func
        self.restart_func(backend_name)

    def _handle_restart(self, parts: List[str]) -> None:
        """
        Handle restart command, stop and start a backend
        """

        if not parts:
            return

        backend_name = parts[0]
        logger.debug("restarting backend %s", backend_name)
        self._handle_stop(parts)
        self._handle_start(parts)

    def _handle_quit(self, _parts: List[str]) -> None:
        """
        Handle quit command, quit nuqql
        """

        logger.debug("quitting nuqql")
        if self.conversation:
            self.conversation.wins.input_win.state.active = False
            self.conversation.wins.list_win.state.active = False

    def _handle_version(self, _parts: List[str]) -> None:
        """
        Handle version command, print nuqql version
        """

        # log message
        msg = f"version: nuqql v{self.version}"
        logger.debug("getting nuqql version: %s", msg)
        if self.conversation:
            self.conversation.log("nuqql", msg)

    def handle_nuqql_command(self, msg: str) -> None:
        """
        Handle a nuqql command (from the nuqql conversation)
        """

        logger.debug("handling nuqql command %s", msg)

        # parse message
        parts = msg.split()
        if not parts:
            return

        # check command and call helper functions
        command_map = {
            "global-status": self._handle_nuqql_global_status,
            "stop": self._handle_stop,
            "start": self._handle_start,
            "restart": self._handle_restart,
            "quit": self._handle_quit,
            "version": self._handle_version,
        }
        command = parts[0]
        if command in command_map:
            command_map[command](parts[1:])
