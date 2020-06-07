"""
Backend server
"""

import logging
import subprocess
import threading

from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

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

        # subprocess output logging thread
        self.output_logger: Optional[threading.Thread] = None
        self.stop_logger = threading.Event()

    def _start_logging(self) -> None:
        """
        Start logging the backend server's output to the nuqql log
        """

        name = self.server_cmd.split()[0]

        def proc_logger() -> None:
            assert self.proc and self.proc.stdout
            while not self.stop_logger.is_set():
                try:
                    for line in iter(self.proc.stdout.readline, b''):
                        logger.debug("got backend subprocess %s output:\n %s",
                                     name, line.decode())
                except OSError:
                    logger.error("error reading subprocess %s output (read)",
                                 name)
                    return
        self.output_logger = threading.Thread(target=proc_logger)
        self.output_logger.start()

    def start(self) -> None:
        """
        Start the backend's server process
        """

        logger.debug("starting server")

        # make sure server's working directory exists
        Path(self.server_path).mkdir(parents=True, exist_ok=True)

        # if logging is enabled for subprocess use pipes
        stdout = subprocess.DEVNULL
        stderr = subprocess.DEVNULL
        if SUBPROCESS_LOGGING:
            stdout = subprocess.PIPE
            stderr = subprocess.STDOUT

        # start server process
        self.proc = subprocess.Popen(
            self.server_cmd,
            shell=True,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,     # dont send SIGINT from nuqql to
                                        # subprocess
        )

        if SUBPROCESS_LOGGING:
            self._start_logging()

    def stop(self) -> None:
        """
        Stop the backend's server process
        """

        logger.debug("stopping server")

        # stop running server
        if self.proc:
            self.proc.terminate()

        # stop output logger
        if self.output_logger:
            self.stop_logger.set()
            self.output_logger.join()
