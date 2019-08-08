# nuqql

nuqql is a command line instant messenger inspired by
[centericq](http://thekonst.net/centericq/) and
[centerim](http://www.centerim.org) written in Python and using ncurses.

nuqql uses so-called backends for connecting to chat networks.
Currently, nuqql supports [purpled](https://github.com/hwipl/purpled),
[nuqql-slixmppd](https://github.com/hwipl/nuqql-slixmppd), and
[nuqql-matrixd](https://github.com/hwipl/nuqql-matrixd) as backends.
purpled uses libpurple and allows nuqql to connect to multiple chat networks.
nuqql-slixmppd uses slixmpp and allows nuqql to connect to XMPP chat networks.
nuqql-matrixd uses the Matrix Python SDK and allows nuqql to connect to Matrix
chat networks.


## Usage

After the setup steps (see the "Setup" section), you can start and use nuqql
as described in the following.

### Run

Run nuqql with `./nuqql.py`.

### Overview

The layout of nuqql is as follows:

```
+--------------+----------------+
|              |                |
|              |                |
|              |                |
|              |   Log Window   |
|              |                |
| List Window  |                |
|              |                |
|              +----------------+
|              |                |
|              |  Input Window  |
|              |                |
+--------------+----------------+
```

* List Window: shows the Conversation List
* Log Window: shows the Log of the current Conversation
* Input Window: shows the user's input of the current Conversation

The Conversation List shows your buddies and special conversations for your
backend commands and nuqql commands. Buddies are shown with their status (on,
afk, off) and their name, e.g., `[on] buddy@jabber.org`. Group chats and
invites to group chats are shown with `[grp]` and `[grp_invite]` as a special
status. The nuqql and backend command conversations are shown as `{nuqql}` and
with `{backend}` in front of their name, e.g., `{backend} slixmppd`.

### Controls

Basic controls of nuqql are:

* Navigate the Conversation List with the arrow keys `UP` and `DOWN`
* Press `ENTER` on a conversation to open it
* Press `h` on a conversation to open it and switch to its chat log
* In a conversation:
  * Enter your message/command
  * Send message/command with `CTRL-x`
  * Switch to chat log window with `CTRL-o`
    * Search chat log with `/`
    * Zoom chat log with `F9`
  * Leave conversation with the `ESC` key
* Exit nuqql with the `q` key when you are in no conversation

See [controls](doc/controls.md) for more information about nuqql's controls.

## Setup

The basic setup consist of installing one or more backends and adding your
instant messaging  accounts to them. See [setup](doc/setup.md) for more
information about how to setup nuqql.

## Development

Most of the development happens in the *devel* branch. When a new version of
nuqql is released, the *devel* code is merged into the *master* branch. So,
if you want to try the latest code, check out the *devel* branch, otherwise
just use *master*.


## Changes

See [changelog](CHANGELOG.md) for changes in each version.
