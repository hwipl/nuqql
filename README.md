# nuqql

nuqql is a command line instant messenger inspired by
[centericq](http://thekonst.net/centericq/) and
[centerim](http://www.centerim.org) written in Python and using ncurses.

Currently, nuqql requires [purpled](https://github.com/hwipl/purpled) or
[nuqql-slixmppd](https://github.com/hwipl/nuqql-slixmppd) as a backend. purpled
is a daemon that uses libpurple and allows nuqql to connect to multiple chat
networks. nuqql-slixmppd uses slixmpp and allows nuqql to connect to XMPP chat
networks.


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
afk, off) and their name, e.g., `[on] buddy@jabber.org`. Backend and the nuqql
command conversations are shown with `{` and `}` around them, e.g., `{nuqql}`.

### Controls

Basic controls of nuqql are:

* Navigate the Conversation List with the arrow keys `UP` and `DOWN`
* Press `ENTER` on a conversation to open it
* Press `h` on a conversation to open it and switch to its chat log
* In a conversation:
  * Enter your message/command
  * Send message/command with `CTRL-x`
  * Switch to chat log window with `CTRL-o`
  * Leave conversation with the `ESC` key
* Exit nuqql with the `q` key when you are in no conversation


## Setup

The basic setup of nuqql consists of installing a backend (purpled and/or
nuqql-slixmppd) and adding your instant messaging accounts to it.

### Installing backends

You can use purpled, nuqql-slixmppd, or both to connect to different chat
networks.

#### purpled

nuqql can use purpled to connect to multiple chat networks. If you have not
done already, install purpled with the following steps:

* Download [purpled](https://github.com/hwipl/purpled)
* Build and install purpled with:
  * `meson builddir`
  * `ninja -C builddir install`

(Note: these steps require the [meson](https://mesonbuild.com/) build system.)

#### nuqql-slixmppd

nuqql can use nuqql-slixmppd to connect to XMPP chat networks. If you have not
done already, install nuqql-slixmppd with the following steps:

* Download [nuqql-slixmppd](https://github.com/hwipl/nuqql-slixmppd)
* nuqql looks for nuqql-slixmppd in your $PATH and the current directory. So, a
  good way is symlinking the *slixmppd.py* executable from the nuqql-slixmppd
  folder into your nuqql folder.


### Adding accounts

If you have not done already, you need to add your instant messaging accounts
to your backends. You can do this from nuqql with the following steps:

* Start nuqql.
* Enter the conversation with the backend by pressing the `ENTER` key
  on the entry in the Conversation List (`{backend} purpled` or `{backend}
  slixmppd`).
* Add your accounts (note: send the following commands the backend with the
  `CTRL-X` key combination):
  * for example, you can add a jabber account with this command:
    `account add xmpp user@jabber-server.com users_password`
* List your accounts with the command: `account list`
* If you want to add an extra buddy, you can just send a message to it, for
  example, with this command: `account 0 send user_name@server.com`. Note: `0`
  is the account ID as shown with `account list`.

### Hacky stuff/additional tools

If certain keys do not work, `nuqql-keys.py` is a tool that might help you to
set up or reconfigure the keymaps within the nuqql code.


## Development

Most of the development happens in the *devel* branch. When a new version of
nuqql is released, the *devel* code is merged into the *master* branch. So,
if you want to try the latest code, check out the *devel* branch, otherwise
just use *master*.


## Changes

* devel:
  * Add additional keybinds in Input Window:
    * `ctrl-a`: go to beginning of line
    * `ctrl-e`: go to end of line
    * `ctrl-k`: delete from cursor to end of line
    * `ctrl-u`: delete line
  * Add additional keybinds in List and Log Window:
    * `HOME`: jump to first line
    * `END`: jump to last line
  * Add Log Window zooming with `F9` key when browsing the history
  * Add account status and persistent global status (for all accounts):
    * `global-status get`: get global status
    * `global-status set <status>`: set global status to `<status>`
  * Improve terminal resize handling
  * Code cleanups, fixes and reorganization
* v0.3:
  * Introduce chat history support
  * Add support for the slixmppd backend
  * Rename Buddy List to Conversation List
  * Introduce multiple backend support
    * Each backend is listed as conversation in the Conversation List
  * nuqql command window is now also a conversation in the Conversation List
  * Coding style fixes and code reorganization
  * Requires purpled v0.2 or nuqql-slixmppd v0.1.
* v0.2:
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
* v0.1:
  * First/initial release.
  * Requires purpled v0.1.
