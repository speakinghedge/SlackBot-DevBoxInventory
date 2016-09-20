from DevBoxInventoryCmdParser import DevBoxInventoryCmdParser


def test_detect_bot_name():

    cp = DevBoxInventoryCmdParser('inventory', [], [])

    assert cp.parse('<@inventory>') == True  # cmd list is empty - only check for the name
    assert cp.parse('<@XinventoryX>') == False
    assert cp.parse('<@inventoryX>') == False
    assert cp.parse('    <@inventory>') == True
    assert cp.parse('\t<@inventory>') == True
    assert cp.parse('XXX <@XinventoryX>') == False


def test_detect_command():

    cp = DevBoxInventoryCmdParser('inventory', ['help', 'list', 'add'], [])

    assert cp.parse('<@inventory>') == True  # missing the cmd
    assert cp.has_cmd() == False
    assert cp.has_reminder() == False

    assert cp.parse('<@inventory> help') == True
    assert cp.cmd == 'help'

    assert cp.parse('<@inventory>            help') == True
    assert cp.cmd == 'help'
    assert cp.has_reminder() == False

    assert cp.parse('<@inventory>\thelp') == True
    assert cp.cmd == 'help'

    assert cp.parse('<@inventory>\tadd    ') == True
    assert cp.cmd == 'add'

    try:
        assert cp.parse('<@inventory> XXX') == False
    except Exception as error:
        assert error.message == 'unknown command XXX'
    assert cp.has_cmd() == False
    assert cp.has_reminder() == True
    assert cp.reminder == 'XXX'
    assert cp.cmd is None


def test_detect_machine_name():

    cp = DevBoxInventoryCmdParser('inventory', ['help', 'list', 'add'], [])

    assert cp.parse('<@inventory> add  ') == True
    assert cp.has_machine_name() == False

    assert cp.parse('<@inventory> add foo') == True
    assert cp.has_cmd() == True
    assert cp.cmd == 'add'
    assert cp.has_machine_name() == True
    assert cp.machine_name == 'foo'

    assert cp.parse('<@inventory> add  ') == True
    assert cp.has_machine_name() == False

    assert cp.parse('<@inventory> list bar') == True
    assert cp.has_machine_name() == True
    assert cp.machine_name == 'bar'
    assert cp.has_reminder() == False


def test_detect_arguments():

    cp = DevBoxInventoryCmdParser('inventory', ['help', 'list', 'add'], ['ip', 'comment'])

    cp.parse('<@inventory> add foo ip:')
    assert cp.has_cmd() == True
    assert cp.cmd == 'add'
    assert cp.has_arg('ip') == True
    assert len(cp.get_arg('ip')) == 0
    assert cp.has_arg('comment') == False

    cp.parse('<@inventory> add bar ip:1.2.3.4')
    assert cp.has_arg('ip') == True
    assert cp.get_arg('ip') == '1.2.3.4'
    assert cp.has_arg('comment') == False
    assert cp.has_reminder() == False

    cp.parse('<@inventory> add baz ip:1.2.3.4     ')
    assert cp.has_arg('ip') == True
    assert cp.get_arg('ip') == '1.2.3.4'
    assert cp.has_arg('comment') == False
    assert cp.has_reminder() == False

    try:
        cp.parse('<@inventory> add bob ip:1.2.3.4    XXX')
    except Exception as error:
        assert error.message == 'unknown argument name XXX'
    assert cp.has_arg('ip') == True
    assert cp.get_arg('ip') == '1.2.3.4'
    assert cp.has_arg('comment') == False
    assert cp.has_reminder() == True
    assert cp.reminder == 'XXX'

    cp.parse('<@inventory> add fum ip:1.2.3.4 ip:')
    assert cp.has_arg('ip') == True
    assert cp.get_arg('ip') == ''
    assert cp.has_arg('comment') == False
    assert cp.has_reminder() == False

    cp.parse('<@inventory> add fre ip: ip:1.2.3.4')
    assert cp.has_arg('ip') == True
    assert cp.get_arg('ip') == '1.2.3.4'
    assert cp.has_arg('comment') == False
    assert cp.has_reminder() == False

    cp.parse('<@inventory> add fre ip: ip:1.2.3.4 comment:foobar')
    assert cp.has_arg('ip') == True
    assert cp.get_arg('ip') == '1.2.3.4'
    assert cp.has_arg('comment') == True
    assert cp.get_arg('comment') == 'foobar'
    assert cp.has_reminder() == False

    cp.parse('<@inventory> add fre ip: ip:1.2.3.4 comment:foobar ip:4.3.2.1')
    assert cp.has_arg('ip') == True
    assert cp.get_arg('ip') == '4.3.2.1'
    assert cp.has_arg('comment') == True
    assert cp.get_arg('comment') == 'foobar'
    assert cp.has_reminder() == False

    cp.parse('<@inventory> add fre ip: ip:1.2.3.4 comment:foobar ip:4.3.2.1 comment:')
    assert cp.has_arg('ip') == True
    assert cp.get_arg('ip') == '4.3.2.1'
    assert cp.has_arg('comment') == True
    assert cp.get_arg('comment') == ''
    assert cp.has_reminder() == False

    cp.parse('<@inventory> add fre comment:foobar')
    assert cp.has_arg('ip') == False
    assert cp.has_arg('comment') == True
    assert cp.get_arg('comment') == 'foobar'
    assert cp.has_reminder() == False

    cp.parse('<@inventory> add fre comment:"foo bar baz" ')
    assert cp.has_arg('ip') == False
    assert cp.has_arg('comment') == True
    assert cp.get_arg('comment') == 'foo bar baz'
    assert cp.has_reminder() == False

    cp.parse('<@inventory> add fre comment:"foo bar baz" ip:1.2.3.4')
    assert cp.has_arg('ip') == True
    assert cp.get_arg('ip') == '1.2.3.4'
    assert cp.has_arg('comment') == True
    assert cp.get_arg('comment') == 'foo bar baz'
    assert cp.has_reminder() == False

    cp.parse('<@inventory> add fre comment:"" ip:1.2.3.4')
    assert cp.has_arg('ip') == True
    assert cp.get_arg('ip') == '1.2.3.4'
    assert cp.has_arg('comment') == True
    assert cp.get_arg('comment') == ''
    assert cp.has_reminder() == False

    cp.parse('<@inventory> add fre comment:"" ip:1.2.3.4 comment:"baz for bar"')
    assert cp.has_arg('ip') == True
    assert cp.get_arg('ip') == '1.2.3.4'
    assert cp.has_arg('comment') == True
    assert cp.get_arg('comment') == 'baz for bar'
    assert cp.has_reminder() == False

    try:
        cp.parse('<@inventory> add fre comment:"" ip:1.2.3.4 comment:"baz for bar"\"')
    except Exception as error:
        assert error.message == 'unknown argument name "'
