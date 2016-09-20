import fnmatch
import os
import time
import syslog
from datetime import datetime
from slackclient import SlackClient
from DevBoxInventory import DevBoxInventory, DevBox

from DevBoxInventoryCmdParser import DevBoxInventoryCmdParser


class DevBoxInventorySlackBot:
    def __init__(self, bot_name, bot_token, inventory_file):

        self.slack_client = SlackClient(bot_token)
        self.bot_user_name = bot_name

        self._build_users_list()
        self.bot_client_id = None

        for user_id in self.slack_users:
            if self.slack_users[user_id] == bot_name:
                self.bot_client_id = user_id

        if self.bot_client_id is None:
            raise Exception('Bot user {0} not found.'.format(bot_name))

        self.inventory = DevBoxInventory(inventory_file)

        self._cmd_routes = {
            'help': self._cmd_help,
            'h': self._cmd_help,
            'halp': self._cmd_help,
            '?': self._cmd_help,
            'show': self._cmd_show,
            'add': self._cmd_add,
            'del': self._cmd_del,
            'update': self._cmd_update,
            'take': self._cmd_take,
            'occupy': self._cmd_occupy,
            'put': self._cmd_put,
            '_restart': self._cmd_restart
        }

        self._cmd_parser = DevBoxInventoryCmdParser(self.bot_client_id,
                                                    [i for i in self._cmd_routes], ['ip', 'comment'])

        self._running = False

    def _build_users_list(self):

        self.slack_users = {}

        api_call = self.slack_client.api_call("users.list")

        if api_call.get('ok'):
            # retrieve all users so we can find our bot
            users = api_call.get('members')
            for user in users:
                if 'name' in user:
                    self.slack_users[user.get('id')] = user.get('name')

        return len(self.slack_users)

    def _user_name_by_id(self, id):

        for user_id in self.slack_users:
            if user_id == id:
                return self.slack_users[id]

        return None

    def _cmd_help(self, channel_id, user_name):

        msg = u'```\n' \
              u'arguments:\n' \
              u'name                                  name of the dev box to work on\n' \
              u'meta                                  can be given in any order and multiple times (last arg rules)\n' \
              u'                                      format: <meta-name>:[<meta-value>, "<meta-values>"]\n' \
              u'                                      currently supported: ip, comment\n' \
              u'commands:\n' \
              u'show [<shell-style-wildcard filter>]  list dev boxes - apply optional filter\n' \
              u'add <name> [<meta-arg>]               add a box having name <name> and optional meta info\n' \
              u'del <name>                            delete a box having name <name>\n' \
              u'update <name> [<meta-arg>]            update a box having name <name> using given meta info\n' \
              u'take <name> [<meta-arg>]              take ownership of box <name>, set optional meta info\n' \
              u'occupy <name> [<meta-arg>]            take ownership of box <name> that is currently in use\n' \
              u'put <name>                            drop ownership of box <name>\n' \
              u'_restart                              restart bot (re-read user list)\n' \
              u'```'

        return True, msg

    def _cmd_show(self, channel_id, user_name):

        msg = u''
        hdr = u'{0:25}{1:15}{2:25}{3:20}{4}\n'.format('box name',
                                                      'owner',
                                                      'time taken',
                                                      'address',
                                                      'comment')
        for name, ip, user, comment, ts_taken in self.inventory.box_datas():

            if self._cmd_parser.has_machine_name() and not fnmatch.fnmatch(name, self._cmd_parser.machine_name):
                continue

            ts_taken_str = datetime.fromtimestamp(ts_taken).strftime('%d.%m.%Y %H:%M:%S') if ts_taken and user else '-'
            msg += u'{0:25}{1:15}{2:25}{3:20}{4}\n'.format(name,
                                                           user if user else 'free',
                                                           ts_taken_str,
                                                           ip if ip else '-',
                                                           comment if comment else '-')

        if not msg:
            if self._cmd_parser.has_machine_name():
                return True, u'No matching boxes in inventory ;-('
            else:
                return True, u'No boxes in inventory ;-('
        else:
            return True, u'```\n' + hdr + msg + '```'

    def _cmd_add(self, channel_id, user_name):

        if not self._cmd_parser.has_machine_name():
            return False, u'Missing box name. You may check the halp.'

        box_name = self._cmd_parser.machine_name

        ret = self.inventory.box_add(box_name,
                                     ip=self._cmd_parser.get_arg('ip'),
                                     user=None,
                                     comment=self._cmd_parser.get_arg('comment'))
        if ret is 0:
            return False, u'Failed to add box *{0}*. Name already in use?'.format(box_name)
        else:
            return True, u'Box *{0}* added to inventory.'.format(box_name)

    def _cmd_del(self, channel_id, user_name):

        if not self._cmd_parser.has_machine_name():
            return False, u'Missing box name. You may check the halp.'

        box_name = self._cmd_parser.machine_name

        ret = self.inventory.box_del(box_name)
        if ret:
            return True, u'Box *{0}* removed from inventory.'.format(box_name)
        else:
            return False, u'Failed to delete box *{0}* - name not known.'.format(box_name)

    def _cmd_update(self, channel_id, user_name):

        if not self._cmd_parser.has_machine_name():
            return False, u'Missing box name. You may check the halp.'

        box_name = self._cmd_parser.machine_name

        ret = self.inventory.box_data_set(box_name,
                                          ip=self._cmd_parser.get_arg('ip'),
                                          user=None,
                                          comment=self._cmd_parser.get_arg('comment'))
        if ret is 0:
            return False, u'Failed to update box *{0}*. Wrong name?'.format(box_name)
        else:
            return True, u'Box *{0}* updated.'.format(box_name)

    def _cmd_set_box_ownership(self, channel_id, user_name, force):

        if not self._cmd_parser.has_machine_name():
            return False, u'Missing box name. You may check the halp.'

        box_name, ip, box_user, comment = self.inventory.box_data_get(self._cmd_parser.machine_name)

        if not box_name:
            return False, u'Failed to take over box *{0}* - unknown or invalid box name.'.format(
                self._cmd_parser.machine_name)

        old_user = None
        if not force:
            if box_user and box_user != user_name:
                return False, u'Box in use by *{0}*. You may force ownership by using the command occupy... USA!'.format(
                    box_user)

            if box_user == user_name:
                return False, u'Maybe you forgot about it - but you are already the owner of *{0}*.'.format(box_name)
        else:
            if box_user and box_user != user_name:
                old_user = box_user

        ip = self._cmd_parser.get_arg('ip') if self._cmd_parser.has_arg('ip') else ip
        comment = self._cmd_parser.get_arg('comment') if self._cmd_parser.has_arg('comment') else comment
        ret = self.inventory.box_data_set(box_name,
                                          ip,
                                          user_name,
                                          comment)
        if ret:
            if old_user:
                return True, u'Box *{0}* *STOLEN* from *{1}* now in use by *{2}*.'.format(box_name, old_user, user_name)
            else:
                return True, u'Box *{0}* now in use by *{1}*.'.format(box_name, user_name)
        else:
            return False, u'Failed to assign ownership of box *{0}* to *{1}*.'.format(box_name, user_name)

    def _cmd_take(self, channel_id, user_name):

        return self._cmd_set_box_ownership(channel_id, user_name, False)

    def _cmd_occupy(self, channel_id, user_name):

        return self._cmd_set_box_ownership(channel_id, user_name, True)

    def _cmd_put(self, channel_id, user_name):

        if not self._cmd_parser.has_machine_name():
            return False, u'Missing box name. You may check the halp.'

        box_name, ip, box_user, comment = self.inventory.box_data_get(self._cmd_parser.machine_name)

        if not box_name:
            return False, u'Failed to drop ownership for box *{0}* - unknown or invalid box name.'.format(
                self._cmd_parser.machine_name)

        if (box_user and box_user != user_name) or not box_user:
            return False, u'Failed to drop ownership for box *{0}* cause you are not the current user.'.format(box_name)

        ret = self.inventory.box_data_set(box_name, ip, '', comment)
        if ret:
            return True, u'*{0}* dropped ownership for box *{1}*.'.format(user_name, box_name)
        else:
            return False, u'Failed to drop ownership of box *{0}* by *{1}*.'.format(box_name, user_name)

    def _cmd_restart(self, channel_id, user_name):

        self._running = False
        return True, u'Inventory bot restarted by *{0}*.'.format(user_name)

    def _parse_command(self, command, user_name, channel_id):

        tokens = command.split(' ', 1)
        cmd = tokens[0]
        args = None
        if len(tokens) > 1:
            args = tokens[1]

        try:
            ret, msg = self._cmd_routes[cmd.lower()](channel_id, user_name, args)
            if ret:
                self._slack_msg(channel_id, msg)
            else:
                self._slack_msg(channel_id, u'*ERROR:* {0}'.format(msg))
        except KeyError as Err:
            self._slack_msg(channel_id, u'*ERROR*: Unknown command _{0}_. You may check the halp.'.format(cmd.lower()))

    def _slack_msg(self, channel, msg):
        self.slack_client.api_call('chat.postMessage', channel=channel, text=msg, as_user=True)

    def parse_slack_output(self, slack_rtm_output):

        bot_at_token = "<@" + self.bot_client_id + ">"
        output_list = slack_rtm_output

        # print output_list
        if output_list and len(output_list) > 0:
            for output in output_list:
                if output and 'text' in output and \
                                'user' in output and 'channel' in output and bot_at_token in output['text']:

                    channel_id = output['channel']
                    user = output['user']

                    try:
                        rc = self._cmd_parser.parse(output['text'])

                        if rc is True:

                            if self._cmd_parser.has_cmd():

                                try:
                                    rc, msg = self._cmd_routes[self._cmd_parser.cmd](channel_id,
                                                                                     self._user_name_by_id(user))
                                    if msg:
                                        if rc is True:
                                            self._slack_msg(channel_id, msg)
                                        else:
                                            self._slack_msg(channel_id,
                                                            u'*ERROR*: _{0}_ You may check the halp.'.format(msg))
                                except KeyError:
                                    self._slack_msg(channel_id,
                                                    u'*ERROR*: Unknown command _{0}_. You may check the halp.'.format(
                                                        self._cmd_parser.cmd))

                    except Exception as error:
                        self._slack_msg(output['channel'],
                                        u'*ERROR*: _{0}_. You may check the halp.'.format(error.message))

    def run(self):
        self._running = True

        if self.slack_client.rtm_connect():
            syslog.syslog(syslog.LOG_INFO, 'slack-bot {0} started.'.format(self.bot_user_name))
            while self._running:
                self.parse_slack_output(self.slack_client.rtm_read())

                '''
                if command and channel_id:
                    user_name = self._user_name_by_id(user_id)
                    self._parse_command(command, user_name, channel_id)
                '''
                time.sleep(0.5)
        else:
            syslog.syslog(syslog.LOG_ERR, 'slack-bot {0} failed to connect to slack. check token and bot name.'.format(
                self.bot_user_name))


def env_get(name):
    val = os.environ.get(name)
    if val is None:
        raise Exception('missing environment variable: {0}'.format(name))

    return val


if __name__ == '__main__':

    bot_name = env_get('slack_inventory_bot_name')
    bot_access_token = env_get('slack_inventory_token')
    inventory_file_path = env_get('slack_inventory_file_path')

    try:
        while True:
            DBISB = DevBoxInventorySlackBot(bot_name, bot_access_token, inventory_file_path)
            DBISB.run()
    except KeyboardInterrupt:
        pass
