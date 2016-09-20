# rationale

A team I working in uses slack and shares some development/test boxes (dev boxes). Every n hours (n>0)
someone needs to ask _'who is using box foo'_ or _'can I have box bar'_ or _'can I kick box rob out of the rack'_ and sooner or later someone or all devs react - or not.

Integrating the management of the dev box ownership in slack is a big plus as it may safe time, prevents FUD, is transparent and you don't need to fire up an additional tool...

# environment

Dependencies: see requirements.txt

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

..is currently really simple and only fulfills our basic requirements: manage the ownership of dev boxes. Most if the commands allow optional meta-information arguments to be added.
A argument is build using its name as prefix followed by a colon. The value of the argument is build
- consuming the next word up to the next whitespace character or
- consuming the next word group enclosed by double quotes, e.g.

```
@inventory update randy comment:the-blues
```
sets the comment of randy to _the-blues_ while
```
@inventory update randy comment:"I still got the blues" ip:1.2.3.4
```
sets the comment to _I still got the blues_ and the IP to _1.2.3.4_.

If the character after the colon is a whitespace the value of the argument is set to an empty string, e.g.
```
@inventory update randy commen:
```
will delete the comment.

Currently the arguments _ip_ and _comment_ are supported.

## show [\<shell-style-wildcard filter\>]

*show* a list of all dev boxes + visible attributes, e.g.:

```
hecke> @inventory show

box name                 owner          time taken               address             comment
harry                    hecke          20.09.2016 21:05:12      192.168.1.110       what the hell is that
lorde                    free           -                        10.10.0.1           -
```

The filter supports the pattern * and ?.

 ```
hecke> @inventory show har*

box name                 owner          time taken               address             comment
harry                    hecke          20.09.2016 21:05:12      192.168.1.110       what the hell is that
```

## add \<box-name\> [\<meta arg\>]

*add* a new box to the inventory. You may add an IP address or a comment by using the args *ip:* and *comment:*.

``` 
hecke> @inventory add lorde

inventoryBOT> Box *lorde* added to inventory.

hecke > @inventory add timmy ip:10.0.0.17 comment:"don't power off - file-server!!!"

inventoryBOT> Box *timmy* added to inventory.

hecke> @inventory show

box name                 owner          time taken               address             comment
lorde                    free           -                        -                   -
timmy                    free           -                        10.0.0.17           don't power off - file-server!!!
```

## update \<box-name\> [\<meta arg\>]

*update* ip or comment for a given box.

```
hecke> @inventory show

box name                 owner          time taken               address             comment
randy                    hecke          20.09.2016 21:05:12      10.0.0.1            do not power off - long time test over the weekend

hecke> @inventory update randy ip:10.0.0.254 comment:

inventoryBOT> Box *randy* updated.

hecke> @inventory show

box name                 owner          time taken               address             comment
randy                    hecke          20.09.2016 21:05:12      10.0.0.254          -
```

## del \<box-name\>

*del*ete box given by name.

```
hecke> @inventory show

box name                 owner          time taken               address             comment
randy                    hecke          20.09.2016 21:05:12      10.0.0.254          -
lorde                    free           -                        -                   -

hecke> @inventory del randy

inventoryBOT> Box *randy* removed from inventory.

hecke> @inventory show

lorde          free
```

## take \<box-name\> [\<meta arg\>]

*take* ownership of box given by name. 

```
hecke> @inventory show

box name                 owner          time taken               address             comment
lorde                    free           -                        -                   - 
timmy                    free           -                        10.0.0.17           don't power off - file-server!!!

hecke> @inventory take lorde

inventoryBOT> Box *lorde* now in use by *hecke*.

hecke> @inventory show

box name                 owner          time taken               address             comment
lorde                    hecke          20.09.2016 21:05:12      -                   -
timmy                    free           -                        10.0.0.17           don't power off - file-server!!!
```

## occupy \<box-name\> [\<meta arg\>]

*occupy* a box that is currently in use by another user. This is the unfriendly way. Asking the current owner is the
preferred way...

```
tester1> @inventory show

box name                 owner          time taken               address             comment
lorde                    hecke          20.09.2016 21:05:12      -                   -
timmy                    free           -                        10.0.0.17           don't power off - file-server!!!

tester1> @inventory take lorde

inventoryBOT> *ERROR:* Box in use by *hecke*. You may force ownership by using the command occupy... USA!

tester1> @inventory occupy lorde

inventoryBOT> Box *lorde* *STOLEN* from *hecke* now in use by *tester1*.

tester1> @inventory show

box name                 owner          time taken               address             comment
lorde                    tester1        20.09.2016 21:07:23      -                   -
timmy                    free           -                        10.0.0.17           don't power off - file-server!!!
```

## put \<box-name\>

*put* the ownership of the box given by name back to the pool.

```

hecke> @inventory show

box name                 owner          time taken               address             comment
lorde                    hecke          20.09.2016 21:05:12      -                   -
timmy                    free           -                        10.0.0.17           don't power off - file-server!!!

hecke> @inventory put lorde

inventoryBOT> *hecke* dropped ownership for box *lorde*.

hecke> @inventory show

box name                 owner          time taken               address             comment
lorde                    free           -                        -                   -
timmy                    free           -                        10.0.0.17           don't power off - file-server!!!
```

## _restart

..is a private command used to restart the inventory bot. This should be run after new users joined the
slack as the bot needs to learn the user names (yes, we could do this as required in the background... see TODO)


# TODO

- restart bot as soon as we hit a new unknown user automatically -or- rework the name resolution mechanic