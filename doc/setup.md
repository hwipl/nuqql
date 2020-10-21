# Installation

If you have not done already, you can install nuqql with the following command:

```console
$ pip install --user nuqql
```

(Note: make sure the directory where pip installs executables (`~/.local/bin`)
is in your PATH)

# Setup

The basic setup of nuqql consists of installing a backend (nuqql-slixmppd,
nuqql-matrixd, and/or purpled) and adding your instant messaging accounts
to it.

## Installing backends

You can use nuqql-slixmppd, slixmppd-matrixd, and/or purpled to connect to
different chat networks.

### nuqql-slixmppd

nuqql can use nuqql-slixmppd to connect to XMPP chat networks. If you have not
done already, you can install nuqql-slixmppd with the following command:

```console
$ pip install --user nuqql-slixmppd
```

### nuqql-matrixd

nuqql can use nuqql-matrixd to connect to Matrix chat networks. If you have not
done already, you can install nuqql-matrixd with the following command:

```console
$ pip install --user nuqql-matrixd
```

### purpled

nuqql can use purpled to connect to multiple chat networks. If you have not
done already, install purpled with the following steps:

* Download [purpled](https://github.com/hwipl/purpled)
* Build and install purpled with:
  * `meson builddir`
  * `ninja -C builddir install`

(Note: these steps require the [meson](https://mesonbuild.com/) build system.)

## Adding accounts

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

## Hacky stuff/additional tools

If certain keys do not work, `nuqql-keys` is a tool that might help you to
set up or reconfigure the keymaps within the nuqql code.
