"""
Backend server
"""

import logging
import subprocess

from pathlib import Path
from typing import Optional, TextIO

# enable/disable logging of subprocess output
SUBPROCESS_LOGGING = True


class BackendServer:
    """
    Class for a backend's server process
    """

    def __init__(self, cmd: str = "", path: str = "") -> None:
        # server
        self.proc: Optional[subprocess.Popen] = None
        self.server_path = path
        self.server_cmd = cmd

        # subprocess output logging files
        self.stdout_file: Optional[TextIO] = None
        self.stderr_file: Optional[TextIO] = None

    def start(self) -> None:
        """
        Start the backend's server process
        """

        logging.debug("BackendServer: starting server")

        # make sure server's working directory exists
        Path(self.server_path).mkdir(parents=True, exist_ok=True)

        # if logging is enabled for subprocess output, open log files
        if SUBPROCESS_LOGGING:
            Path(self.server_path + "/logs").mkdir(parents=True, exist_ok=True)
            self.stdout_file = open(self.server_path +
                                    "/logs/backend-stdout.log", "a")
            self.stderr_file = open(self.server_path +
                                    "/logs/backend-stderr.log", "a")

        # start server process
        self.proc = subprocess.Popen(
            self.server_cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,     # dont send SIGINT from nuqql to
                                        # subprocess
        )

    def stop(self) -> None:
        """
        Stop the backend's server process
        """

        logging.debug("BackendServer: stopping server")

        # stop running server
        if self.proc:
            self.proc.terminate()

        # close subprocess log files if logging is enabled
        if SUBPROCESS_LOGGING:
            if self.stdout_file:
                self.stdout_file.close()
            if self.stderr_file:
                self.stderr_file.close()
