# nuqql

nuqql is a command line instant messenger inspired by
[centericq](http://thekonst.net/centericq/) and
[centerim](http://www.centerim.org) written in Python and using ncurses.

Currently, nuqql requires [purpled](https://github.com/hwipl/purpled) v0.1 as
a back-end. purpled is a daemon that uses libpurple and allows nuqql to
connect to multiple chat networks.

## Configuration

Unfortunately, the setup of the current nuqql version is a bit complicated. It
requires the following steps.

### Add accounts to purpled

If you have not done already, you need to add your instant messaging accounts
in purpled (see also the purpled documentation):

* Start purpled with: `purpled -i`
* In another terminal connect to purpled with telnet: `telnet localhost 32000`
* In the telnet session:
  * add your accounts; for example a jabber account with: `account add xmpp
    user@jabber-server.com users_password`
  * you can list your accounts with: `account list`
  * remember the IDs (first number in account list output) of the accounts you
    want to use in nuqql. You need to use them in the nuqql.conf later.
* Close the telnet session
* Terminate purpled

### Setup nuqql and add accounts from purpled

In order to use nuqql, you have to make the purpled binary available to nuqql
and add the purpled accounts:

* Enter the nuqql directory
* Link/copy the purpled binary into the nuqql directory
* Copy/rename nuqql.conf-example to nuqql.conf
* Add your purpled account(s) to nuqql.conf:
  * Add your account user name in the [] brackets, e.g.:
    `[user@jabber-server.com]`
  * Add the ID of your purpled account (as shown by `account list` in
    purpled; see above) in the `id` field
  * Tell nuqql the type of the account in the `type` field. Currently, only
    `xmpp` and `icq` types are implemented.
  * If you want to add extra buddies, you can do that in the `buddies` field

## Usage

After the previous steps, you should finally be able to use nuqql.

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

### Hacky stuff/additional tools

If certain keys do not work, nuqql-keys.py is a tool that might help you to set
up or reconfigure the keymaps within the nuqql code.
