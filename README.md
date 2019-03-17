# nuqql

nuqql is a command line instant messenger inspired by
[centericq](http://thekonst.net/centericq/) and
[centerim](http://www.centerim.org) written in Python and using ncurses.

Currently, nuqql requires [purpled](https://github.com/hwipl/purpled) as
a back-end. purpled is a daemon that uses libpurple and allows nuqql to
connect to multiple chat networks.

## Setup

The basic setup of nuqql consists of installing purpled and adding your instant
messaging accounts.

### Installing purpled

nuqql needs purpled to connect to chat networks. If you have not done already,
install purpled with the following steps:

* Download [purpled](https://github.com/hwipl/purpled)
* Build and install purpled with:
  * `meson builddir`
  * `ninja -C builddir install`

(Note: these steps require the [meson](https://mesonbuild.com/) build system.)

### Adding purpled accounts

If you have not done already, you need to add your instant messaging accounts
in purpled (see also the purpled documentation). You can do this from nuqql
with the following steps:

* Start nuqql.
* Enter the command window with the `:` key (in the command window, send the
  following commands to purpled with the `CTRL-X` key combination).
* Add your accounts in the command window:
  * for example, you can add a jabber account with this command:
    `account add xmpp user@jabber-server.com users_password`
* List your accounts with the command: `account list`
* If you want to add an extra buddy, you can just send a message to it, for
  example, with this command: `account 0 send user_name@server.com`. Note: `0`
  is the account ID as shown with `account list`.

## Usage

After the previous setup steps, you should finally be able to use nuqql.

### Run

Run nuqql with `./nuqql.py`.

### Controls

Basic controls of nuqql are:

* Navigate the buddy list with the arrow keys `UP` and `DOWN`
* Press `ENTER` on a buddy to start a conversation with it
* In a conversation:
  * Send message with `CTRL-X`
  * Leave conversation with the `ESC` key
* Exit nuqql with the `q` key when you are in no conversation
* Enter a special conversation named the command window with the `:` key when
  you are in no conversation

### Hacky stuff/additional tools

If certain keys do not work, nuqql-keys.py is a tool that might help you to set
up or reconfigure the keymaps within the nuqql code.

## Changes
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
