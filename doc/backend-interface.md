# Nuqql Backend Interface

This file contains the description of nuqql's backend interface. It is a
text-based protocol spoken between nuqql backends and nuqql (or a user
connecting via, e.g., telnet to a running standalone backend). In the
following, all commands and their descriptions are listed:


## Account Management

Account management related commands:


### Listing existing Accounts

```
account list
```

List all accounts and their account ids.


#### Reply

```
account: <id> <name> <protocol> <user> <status>
```

For each account, the backend replies with an `account` message that contains
the account's id `<id>`, name `<name>`, chat protocol `<protocol>`, user name
`<user>`, and status `<status>`.


#### Examples

nuqql-slixmppd:

```
account list
account: 0 () xmpp someuser@jabber.org [online]
account: 1 () xmpp other@somexmpp.com [online]
```

nuqql-matrixd:

```
account list
account: 0 () matrix someuser@matrix.org [online]
account: 1 () matrix otheruser@matrix.org [online]
```


### Adding a new Account

```
account add <protocol> <user> <password>
```

Add a new account for chat protocol `<protocol>` with user name `<user>` and
the password `<password>`. The supported chat protocol(s) are backend specific.
The user name is chat protocol specific. An account id is assigned to the
account that can be shown with `account list`.


#### Reply

The backend does not have to reply with anything. Optionally, it may return an
`info` message like

```
info: new account added.
```


#### Examples

nuqql-slixmppd:

```
account add xmpp someuser@jabber.org somepassword
info: new account added.
account add xmpp other@somexmpp.com otherpass1
info: new account added.
```

nuqql-matrixd:

```
account add matrix someuser@matrix.org somepassword
info: new account added.
account add matrix otheruser@matrix.org otherpass1
info: new account added.
```


### Deleting an existing Account

```
account <id> delete
```

Delete the account with the account id `<id>`.


#### Reply

The backend does not have to reply with anything. Optionally, it may return an
`info` message like

```
info: account <id> deleted.
```


#### Examples

```
account 0 delete
info: account 0 deleted.
account 1 delete
info: account 1 deleted.
```


## Buddies/Roster

Buddies/roster related commands:


### Showing Buddy List/Roster on an Account

```
account <id> buddies [online]
```

List all buddies on the account with the account id `<id>`. Optionally, show
only online buddies with the extra parameter `online`.


#### Reply

```
buddy: <acc_id> status: <status> name: <name> alias: [alias]
```

For each buddy, the backend replies with a `buddy` message that contains the
account id `<acc_id>`, the availability status `<status>`, the user name
`<name>`, and an optional alias `[alias]`.


#### Examples

```
account 0 buddies
buddy: 0 status: away name: someuser@anyjabber.org alias:
buddy: 0 status: offline name: alwaysoff@otherxmpp.com alias: alwaysoff
buddy: 0 status: offline name: friend@otherjabber.org alias: friend
buddy: 0 status: available name: onalot@alwaysxmpp.net alias:
buddy: 0 status: away name: likes2afk@somejabber.net alias: likes2afk
```


### Adding a User to the Buddy List/Roster

When sending a message to an user that is not on the buddy list, the backend
automatically adds the user to the buddy list.


## Message Receiving and Sending

Message receiving/sending related commands:

### Collecting old Messages

```
account <id> collect
```

Collect all messages received on the account with the account id `<id>`.


### Sending a Message to another User

```
account <id> send <user> <msg>
```

Send a message to the user `<user>` on the account with the account id `<id>`.


## Account Status

Account status related commands:

### Getting an Account's Status

```
account <id> status get
```

Get the status of the account with the account id `<id>`.


### Setting an Account's Status

```
account <id> status set <status>
```

Set the status of the account with the account id `<id>` to `<status>`.


## Group Chats

Group chat related commands:


### Listing joined Group Chats

```
account <id> chat list
```

List all group chats on the account with the account id `<id>`.


### Joining a Group Chat

```
account <id> chat join <chat>
```

Join the group chat <chat> on the account with the account id `<id>`.


### Leaving a Group Chat

```
account <id> chat part <chat>
```

Leave the group chat `<chat>` on the account with the account id `<id>`.


### Sending a Message to a Group Chat

```
account <id> chat send <chat> <msg>
```

Send the message <msg> to the group chat `<chat>` on the account with the
account id `<id>`.


### Listing users in a Group Chat

```
account <id> chat users <chat>
```

List the users in the group chat `<chat>` on the account with the
account id `<id>`.


### Inviting a User to a Group Chat

```
account <id> chat invite <chat> <user>
```

Invite the user `<user>` to the group chat `<chat>` on the account with the
account id `<id>`.


## Backend Related

Backend related commands:


### Disconnecting from a Backend

```
bye
```

Disconnect from the backend


### Quitting a Backend

```
quit
```

Quit the backend


### Showing Backend Help

```
help
```

Show list of commands and their description.
