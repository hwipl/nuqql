"""
Backend helpers
"""

import logging
import shutil
import os
import time

from pathlib import Path
from typing import Dict, List, Optional

import nuqql.config
import nuqql.conversation
from nuqql import VERSION

from .backend import Backend
from .nuqqlbackend import NuqqlBackend

logger = logging.getLogger(__name__)

# how long should we wait for backends (in seconds) before starting clients
BACKENDS_WAIT_TIME = 1

# disable the python backends' own history?
BACKEND_DISABLE_HISTORY = True

# let backend push accounts to us?
BACKEND_PUSH_ACCOUNTS = True

# filenames that should not get started as backends
BACKEND_BLACKLIST = ["nuqql-keys", "nuqql-based"]

# dictionary for all active backends
BACKENDS: Dict[str, "Backend"] = {}


def update_buddies() -> None:
    """
    Helper for updating buddies on all backends
    """

    for backend in dict(BACKENDS).values():
        backend.update_buddies()


def handle_network() -> None:
    """
    Helper for handling network events on all backends
    """

    for backend in dict(BACKENDS).values():
        backend.handle_network()


def start_backend(backend_name: str, backend_exe: str, backend_path: str,
                  backend_cmd_fmt: str,
                  backend_sockfile: str) -> Optional[Backend]:
    """
    Helper for starting a backend
    """

    logger.debug("starting backend: name %s, exe %s, path %s, cmd_fmt %s, "
                 "sockfile %s", backend_name, backend_exe, backend_path,
                 backend_cmd_fmt, backend_sockfile)

    # check if backend exists in path
    exe = shutil.which(backend_exe, path=os.getcwd())
    if exe is None:
        exe = shutil.which(backend_exe)
    if exe is None:
        # does not exist, stop here
        return None

    backend_cmd = backend_cmd_fmt.format(exe, backend_path)

    backend = Backend(backend_name)
    backend.backends = BACKENDS
    backend.start_server(cmd=backend_cmd, path=backend_path)
    backend.init_client(sock_file=backend_sockfile)

    BACKENDS[backend_name] = backend

    # add conversation and show it in list window
    conv = nuqql.conversation.BackendConversation(backend, None, backend.name)
    conv.create_windows()
    nuqql.conversation.CONVERSATIONS.append(conv)
    backend.conversation = conv
    conv.wins.list_win.redraw()

    # log backend start
    log_msg = "Starting backend \"{0}\".".format(backend.name)
    nuqql.conversation.log_nuqql_conv(log_msg)

    # return the backend
    return backend


def start_purpled() -> Optional[Backend]:
    """
    Helper for starting the "purpled" backend
    """

    logger.debug("trying to find backend purpled")

    # check if purpled exists in path
    exe = shutil.which("purpled", path=os.getcwd())
    if exe is None:
        exe = shutil.which("purpled")
    if exe is None:
        # does not exist, stop here
        return None
    logger.debug("found backend purpled in file %s", exe)

    ###########
    # purpled #
    ###########

    logger.debug("starting backend purpled")

    backend_name = "purpled"
    backend_exe = "purpled"
    backend_path = str(Path.home()) + "/.config/nuqql/backend/purpled"
    backend_cmd_fmt = "{0} -u -w{1}"
    backend_sockfile = backend_path + "/purpled.sock"

    return start_backend(backend_name, backend_exe, backend_path,
                         backend_cmd_fmt, backend_sockfile)


def start_backend_from_path(filename) -> Optional[Backend]:
    """
    Helper for starting a single backend found in PATH.
    """

    logger.debug("starting backend found in PATH")

    backend_name = filename[6:]
    backend_exe = filename
    backend_path = str(Path.home()) + f"/.config/nuqql/backend/{backend_name}"
    backend_cmd_fmt = "{0} --af unix --dir {1} --sockfile " + \
        f"{backend_name}.sock"
    if BACKEND_DISABLE_HISTORY:
        backend_cmd_fmt += " --disable-history"
    if BACKEND_PUSH_ACCOUNTS:
        backend_cmd_fmt += " --push-accounts"
    loglevel = nuqql.config.get("loglevel")
    if loglevel:
        backend_cmd_fmt += f" --loglevel {loglevel}"
    backend_sockfile = backend_path + f"/{backend_name}.sock"

    return start_backend(backend_name, backend_exe, backend_path,
                         backend_cmd_fmt, backend_sockfile)


def get_backends_from_path() -> List[str]:
    """
    Get a list of backends found in PATH.
    """

    backends: List[str] = []
    for path_dir in os.get_exec_path():
        if not os.path.isdir(path_dir):
            # PATH may contain directories that do not exist, skip them
            continue
        with os.scandir(path_dir) as path:
            for entry in path:
                if entry.is_file() and \
                   entry.name.startswith("nuqql-") and \
                   entry.name not in BACKEND_BLACKLIST and \
                   entry.name not in backends:
                    backends.append(entry.name)
    return backends


def start_backends_from_path() -> None:
    """
    Helper for starting all backends found in PATH.
    These backends are expected to have the same command line arguments.
    """

    logger.debug("trying to find backends in PATH")

    for filename in get_backends_from_path():
        logger.debug("found backend file %s in PATH", filename)
        start_backend_from_path(filename)


def start_backend_client(backend: Backend) -> None:
    """
    Helper for starting a single backend client
    """

    logger.debug("starting backend client for backend %s", backend.name)

    # let user know we are connecting
    log_msg = "Starting client for backend \"{0}\".".format(backend.name)
    nuqql.conversation.log_nuqql_conv(log_msg)

    # start backend client and connect to backend server
    backend.start_client()

    # make sure the connection to the backend was successful
    if not backend.client or not backend.client.sock:
        log_msg = "Could not connect to backend \"{0}\".".format(backend.name)
        logger.error("could not connect to backend %s", backend.name)
        nuqql.conversation.log_nuqql_conv(log_msg)
        backend.stop()
        return

    # request accounts from backend
    backend.client.send_accounts()

    # log it
    log_msg = "Collecting accounts for \"{0}\".".format(backend.name)
    if backend.conversation:
        backend.conversation.log("nuqql", log_msg)


def start_backend_clients() -> None:
    """
    Helper for starting all backend clients
    """

    logger.debug("starting backend clients")

    # give backend servers some time
    time.sleep(BACKENDS_WAIT_TIME)

    for backend in dict(BACKENDS).values():
        start_backend_client(backend)


def restart_backend(backend_name: str) -> None:
    """
    (Re)start a backend and the client connection. Called from NuqqlBackend
    """

    logger.debug("restarting backend %s", backend_name)

    if backend_name in BACKENDS:
        # backend already running
        return

    # try to start backend
    backend = None

    # extra check for purpled, other backends are started from PATH
    if backend_name == "purpled":
        backend = start_purpled()
    else:
        for filename in get_backends_from_path():
            # ignore "nuqql-" in filename
            if backend_name == filename[6:]:
                backend = start_backend_from_path(filename)
                break

    # start the backend client
    if backend:
        # give backend server some time
        time.sleep(BACKENDS_WAIT_TIME)
        start_backend_client(backend)


def start_nuqql() -> None:
    """
    Start the nuqql dummy backend
    """

    logger.debug("starting nuqql backend")

    # create backend
    backend = NuqqlBackend("nuqql")
    backend.version = VERSION
    backend.backends = BACKENDS
    backend.restart_func = restart_backend

    # add conversation and show it in list window
    conv = nuqql.conversation.NuqqlConversation(backend, None, backend.name)
    conv.create_windows()
    backend.conversation = conv
    conv.wins.list_win.redraw()
    nuqql.conversation.log_nuqql_conv(f"Started nuqql v{VERSION}.")
    logger.debug("started nuqql backend version %s", VERSION)


def start_backends() -> None:
    """
    Helper for starting all backends
    """

    logger.debug("starting all available backends")

    # start nuqql dummy backend
    start_nuqql()

    # start backends
    nuqql.conversation.log_nuqql_conv("Starting backends.")
    start_purpled()
    start_backends_from_path()

    # start backend clients
    start_backend_clients()


def stop_backends() -> None:
    """
    Helper for stopping all backends
    """

    logger.debug("stopping all backends")
    for backend in dict(BACKENDS).values():
        backend.stop()  # changes BACKENDS
