# Installation

If you have not done already, you can install nuqql with the following command:

```console
$ pip install --user nuqql
```

(Note: make sure the directory where pip installs executables (`~/.local/bin`)
is in your PATH)

# Setup

The basic setup of nuqql consists of installing a backend (nuqql-slixmppd,
nuqql-matrixd-nio, nuqql-matrixd, nuqql-mattermostd, and/or purpled) and adding
your instant messaging accounts to it.

## Installing backends

You can use nuqql-slixmppd, nuqql-matrixd-nio, nuqql-matrixd,
nuqql-mattermostd, and/or purpled to connect to different chat networks.

### nuqql-slixmppd

nuqql can use nuqql-slixmppd to connect to XMPP chat networks. If you have not
done already, you can install nuqql-slixmppd with the following command:

```console
$ pip install --user nuqql-slixmppd
```

(Note: make sure the directory where pip installs executables (`~/.local/bin`)
is in your PATH)

### nuqql-matrixd-nio

nuqql can use nuqql-matrixd-nio to connect to Matrix chat networks. If you have
not done already, you can install nuqql-matrixd-nio with the following command:

```console
$ pip install --user nuqql-matrixd-nio
```

(Note: make sure the directory where pip installs executables (`~/.local/bin`)
is in your PATH)

### nuqql-matrixd

nuqql can use nuqql-matrixd to connect to Matrix chat networks. If you have not
done already, you can install nuqql-matrixd with the following command:

```console
$ pip install --user nuqql-matrixd
```

(Note: make sure the directory where pip installs executables (`~/.local/bin`)
is in your PATH)

### nuqql-mattermostd

nuqql can use nuqql-mattermostd to connect to Mattermost servers. If you have
not done already, you can install nuqql-mattermostd as follows:

If you just want the latest version, you can install nuqql-mattermostd with its
dependencies with the following command:

```console
$ go get -u github.com/hwipl/nuqql-mattermostd/cmd/nuqql-mattermostd
```

If you want to install a specific version, you can install it with the
following steps:

* Download [nuqql-mattermostd](https://github.com/hwipl/nuqql-mattermostd)
* Build and install nuqql-mattermostd with:
  * `go get -u ./cmd/nuqql-mattermostd`

(Note: make sure your GOPATH/GOBIN is in your PATH)

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
  on the entry in the Conversation List (e.g.,`{backend} purpled` or `{backend}
  slixmppd`).
* Add your accounts (note: send the following commands the backend with the
  `CTRL-X` key combination):
  * for example, you can add a jabber account with this command:
    `account add xmpp user@jabber-server.com users_password`
* List your accounts with the command: `account list`
* If you want to add an extra buddy, you can just send a message to it, for
  example, with this command: `account 0 send user_name@server.com`. Note: `0`
  is the account ID as shown with `account list`.

The details are backend and chat network/protocol specific. See below for more
information about XMPP/Jabber, Matrix and Mattermost accounts.

### XMPP/Jabber accounts

You can add a XMPP/Jabber account with the following command:

```
account add xmpp <account> <password>
```

The format of xmpp accounts in nuqql-slixmppd is `<username>@<jabberserver>`,
e.g., `dummy_user@jabber.org`

Example:

```
account add xmpp user@jabber-server.com users_password
```

### Matrix accounts

You can add a Matrix account with the following command:

```
account add matrix <account> <password>
```

The format of matrix accounts in nuqql-matrixd is `<username>@<homeserver>`,
e.g., `dummy_user@matrix.org`.

Example:

```
account add matrix dummy_user@matrix.org users_password
```

### Mattermost accounts

You can add a Mattermost account with the following command:

```
account add mattermost <account> <password>
```

The format of mattermost accounts in nuqql-mattermostd is
`<username>@<server>`, e.g., `dummy_user@yourserver.org:8065`.

Example:

```
account add mattermost dummy_user@yourserver.org:8065 users_password
```

## Hacky stuff/additional tools

If certain keys do not work, `nuqql-keys` is a tool that might help you to
set up or reconfigure the keymaps within the nuqql code.
