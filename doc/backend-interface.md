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


### Adding a new Account

```
account add <protocol> <user> <password>
```

Add a new account for chat protocol `<protocol>` with user name `<user>` and
the password `<password>`. The supported chat protocol(s) are backend specific.
The user name is chat protocol specific. An account id is assigned to the
account that can be shown with `account list`.


### Deleting an existing Account

```
account <id> delete
```

Delete the account with the account id `<id>`.


## Buddies/Roster

Buddies/roster related commands:


### Showing Buddy List/Roster on an Account

```
account <id> buddies [online]
```

List all buddies on the account with the account id `<id>`. Optionally, show
only online buddies with the extra parameter `online`.


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
