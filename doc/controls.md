# Controls

This file contains the default keybinds and special commands in nuqql.

## Conversation List (ListWin)

These are the special keys you can use when browsing the conversation list
(inside the ListWin):

* `UP` or `k`: move cursor up one line
* `DOWN` or `j`: move cursor down one line
* `PAGE UP`: move cursor up one page
* `PAGE DOWN`: move cursor down one page
* `HOME`: move cursor up to first line
* `END`: move cursor down to last line
* `/` or `CTRL-V`: search/filter conversation list

* `ENTER`: open conversation (-> InputWin)
* `h`: open conversation and switch to its history (-> LogWin)
* `CTRL-N`: open next unread or more recently used conversation (-> InputWin)
* `CTRL-B`: open previously used conversation (-> InputWin)

* `q`: quit nuqql

## Conversation (InputWin)

These are the special keys you can use when inside a conversation (inside an
InputWin):

* `UP`: move cursor up one line
* `DOWN`: move cursor down one line
* `RIGHT`: move cursor right one character
* `LEFT`: move cursor left one character
* `PAGE UP` or `CTRL-A`: move cursor to beginning of line
* `PAGE DOWN` or `CTRL-E`: move cursor to end of line
* `HOME`: move cursor up to first line
* `END`: move cursor down to last line

* `CTRL-K`: delete from cursor to end of line
* `CTRL-U`: delete line

* `CTRL-X`: send message/command
* `CTRL-O`: switch to conversation's history (-> LogWin)

* `CTRL-N`: open next unread or more recently used conversation (-> InputWin)
* `CTRL-B`: open previously used conversation (-> InputWin)
* `CTRL-V`: go back to conversation list and search/filter conversation list
  (-> ListWin)

* `F10`: open conversation's history, search for URL starting with http, and
  switch to zoomed view

* `ESC`: Leave conversation (-> ListWin)

Special commands only in group chat conversations:

* `/names`: get list of users in current group chat
* `/invite <user>`: invite \<user\> to current group chat
* `/join`: join the current group chat (after getting invited)
* `/part`: leave current group chat

Special commands only in the `{nuqql}` conversation:

* `global-status get`: get global status
* `global-status set <status>`: set global status to \<status\>

##  Conversation History (LogWin)

These are the special keys you can use when browsing a conversation's history
(inside a LogWin):

* TODO
