# Changelog

This file contains the changes in each nuqql version:

## v0.8:
* Add version information
  * Add `--version` command line argument
  * Add `version` command to the nuqql conversation
* Backend changes:
  * Change expected names of python backend executables to `nuqql-based`,
    `nuqql-matrixd`, and `nuqql-slixmppd`
  * Do not run `nuqql-based` by default any more
  * Disable additional message history in python backends
* Improve backspace and quit handling
* Improve LogWin zooming and searching
  * Add jumping and zooming from InputWin with `F9`
  * Search for next match with `F10`
* Rename `nuqql.py` helper script to `run.py`
* Add `setup.py` for installation and package distribution
* Move nuqql-keys into the `tools/` subfolder and install it as `nuqql-keys`
  with `setup.py`
* Add python type annotations
* Fixes and improvements
* Requires nuqql-slixmppd v0.5, nuqql-matrixd v0.3, or purpled v0.5

## v0.7:
* Improve backend handling
  * Add "stop", "start", and "restart" commands to nuqql conversation for
    stopping, starting, and restarting a backend
  * Handle "bye" and "quit" backend commands in nuqql
  * Improve backend error handling
* Improve Log Window scrolling and message printing
* Add and use "chat msg" message format for group chat messages
* Add documentation of
  * nuqql controls in `doc/controls.md`
  * nuqql backend interface in `doc/backend-interface.md`
* Cleanups, fixes, and improvements.
* Requires purpled v0.5, nuqql-slixmppd v0.4, or nuqql-matrixd v0.2

## v0.6:
* Rework history viewing code in log window
* Add additional keybinds to conversation list and input windows:
  * `ctrl-n`: go to next unread or more recently used conversation
  * `ctrl-b`: go back to previously used conversation
  * `ctrl-v`: search/filter conversation list
* Additional conversation list keybinds:
  * `j`, `k`: move cursor down, up
  * `/`: search/filter conversation list
* Add most recently used sorting of the conversation list
* Add configuration file for setting ui layout, colors, keybinds, keymap,
  window titles, conversation list sorting
* Improve nuqql-keys to work with nuqql config file
* Improve backend start and reduce wait time
* Code cleanups, fixes, and improvements

## v0.5:
* Add group chat support and helper commands for group chats:
  * `/names`: get list of users in current group chat
  * `/invite <user>`: invite user to current group chat
  * `/join`: join the current group chat (after getting invited)
  * `/part`: leave current group chat
* Add history searching: search the history with `/` and then jump to next
  match with `n` and previous match with `p`
* Add `F10` hotkey to jump from a conversation to first URL starting with
  http in its history and also switch to zoomed view
* Add support for the nuqql-matrixd backend
* Cleanups, fixes, and improvements
* Requires purpled v0.4, nuqql-slixmppd v0.3, or nuqql-matrixd v0.1

## v0.4:
* Add additional keybinds in Input Window:
  * `ctrl-a`: go to beginning of line
  * `ctrl-e`: go to end of line
  * `ctrl-k`: delete from cursor to end of line
  * `ctrl-u`: delete line
* Add additional keybinds in List and Log Window:
  * `HOME`: jump to first line
  * `END`: jump to last line
* Add Log Window zooming with `F9` key when browsing the history
* Add account status and persistent global status (for all accounts) in
  `{nuqql}` conversation:
  * `global-status get`: get global status
  * `global-status set <status>`: set global status to `<status>`
* Improve terminal resize handling
* Improve conversation list focus and conversation history behaviour
* Code cleanups, fixes and reorganization
* Requires purpled v0.3 or nuqql-slixmppd v0.2

## v0.3:
* Introduce chat history support
* Add support for the slixmppd backend
* Rename Buddy List to Conversation List
* Introduce multiple backend support
  * Each backend is listed as conversation in the Conversation List
* nuqql command window is now also a conversation in the Conversation List
* Coding style fixes and code reorganization
* Requires purpled v0.2 or nuqql-slixmppd v0.1.

##  v0.2:
* Make nuqql configuration easier:
  * Look for purpled in $PATH
  * Retrieve accounts from purpled
  * Allow sending commands to purpled directly from nuqql using the command
    window
* Restructure code.
* Introduce `.config/nuqql` in your home directory as working directory.
  purpled sock file, config, logs, etc. are stored in
  `.config/nuqql/backend/purpled`
* Requires purpled v0.2.

## v0.1:
* First/initial release.
* Requires purpled v0.1.
