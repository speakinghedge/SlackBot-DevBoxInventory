# rationale

A team I working in uses slack and shares some development/test boxes (dev boxes). Every n hours (n>0)
someone needs to ask _'who is using box foo'_ or _'can I have box bar'_ or _'can I kick box rob out of the rack'_ and sooner or later someone or all devs react - or not.

Integrating the management of the dev box ownership in slack is a big plus as it may safe time, prevents FUD, is transparent and you don't need to fire up an additional tool...

# required environment

This bot uses the python SlackClient (tested with version: 1.0.1). You may install it by running

```
> sudo pip install SlackClient
```

To be able to run the bot the following environment variables must be set:

|name | content|
|---|---|
slack_inventory_bot_name | name of the bot as configured in slack
slack_inventory_token  | slack access token assigned to this bot 
inventory_file_path | path to store the inventory file (needs create/write permissions)

you may place all of these variables in a small shell script that prepares the env and starts the bot:

```
#!/bin/bash

slack_inventory_bot_name='inventory'
export slack_inventory_bot_name
slack_inventory_token='token-as-created-by-slack'
export slack_inventory_token
slack_inventory_file_path='/tmp/inventory'
export slack_inventory_file_path

python ./DevBoxInventorySlackBot.py
```

# the bot

..is currently really simple and only fulfills our basic requirements: manage the ownership of dev boxes. For being able to do this it offers some basic commands:

## show [\<shell-style-wildcard filter\>]

*show* a list of all dev boxes + visible attributes, e.g.:

```
hecke> @inventory show

randy          hecke          10.0.0.1            do not power off - long time test over the weekend
lorde          free
```

The filter supports the pattern * and ?.

 ```
hecke> @inventory show ran*

randy          hecke          10.0.0.1            do not power off - long time test over the weekend
```

## add \<box-name\> [ip:\<address\>] [comment:\<text\>]

*add* a new box to the inventory. You may add an IP address or a comment by using the tags *ip:* and *comment:*.

Note: the comment option is greedy - it eats all following text

``` 
hecke> @inventory add lorde

inventoryBOT> Box *lorde* added to inventory.

hecke > @inventory add timmy ip:10.0.0.17 comment: don't power off - file-server!!!

inventoryBOT> Box *timmy* added to inventory.

hecke> @inventory show

lorde          free                            
timmy          free           10.0.0.17            don't power off - file-server!!!
```

## update \<box-name\> [ip:\<address\>] [comment:\<text\>]

*update* ip or comment for a given box.

If ip or comment is given but empty the associated attribute is cleared.

```
hecke> @inventory show

randy          hecke          10.0.0.1            do not power off - long time test over the weekend

hecke> @inventory update randy ip:10.0.0.254 comment:

inventoryBOT> Box *randy* updated.

hecke> @inventory show

randy          hecke          10.0.0.254
```

## del \<box-name\>

*del*ete box given by name.

```
hecke> @inventory show

randy          hecke          10.0.0.254          
lorde          free

hecke> @inventory del randy

inventoryBOT> Box *randy* removed from inventory.

hecke> @inventory show

lorde          free
```

## take \<box-name\> [comment:\<comment\>}

*take* ownership of box given by name. 

```
hecke> @inventory show

lorde          free
timmy          free           10.0.0.17            don't power off - file-server!!!

hecke> @inventory take lorde

inventoryBOT> Box *lorde* now in use by *hecke*.

hecke> @inventory show

lorde          hecke                              
timmy          free           10.0.0.17            don't power off - file-server!!!
```

If given, the comment is set.

## occupy <box-name> [comment:\<comment\>}

*occupy* a box that is currently in use by another user. This is the unfriendly way. Asking the current owner is the
preferred way...

```
tester1> @inventory show

lorde          hecke                              
timmy          free           10.0.0.17            don't power off - file-server!!!

tester1> @inventory take lorde

inventoryBOT> *ERROR:* Box in use by *hecke*. You may force ownership by using the command occupy... USA!

tester1> @inventory occupy lorde

inventoryBOT> Box *lorde* *STOLEN* from *hecke* now in use by *tester1*.

tester1> @inventory show

lorde          tester1                            
timmy          free           10.0.0.17            don't power off - file-server!!!
```

If given, the comment is set.

## put \<box-name\>

*put* the ownership of the box given by name back to the pool.

```

hecke> @inventory show

lorde          tester1                            
timmy          hecke          10.0.0.17            don't power off - file-server!!!

hecke> @inventory put timmy

inventoryBOT> *hecke* dropped ownership for box *timmy*.

hecke> @inventory show

lorde          tester1                            
timmy          free           10.0.0.17            don't power off - file-server!!!
```

## _restart

..is a private command used to restart the inventory bot. This should be run after new users joined the
slack as the bot needs to learn the user names (yes, we could do this as required in the background... see TODO)


# TODO

- restart bot as soon as we hit a new unknown user automatically -or- rework the name resolution mechanic