class DevBoxInventoryCmdParser(object):

    def __init__(self, bot_name, cmd_list, arg_list):

        assert len(bot_name) > 0
        assert isinstance(cmd_list, list)
        assert isinstance(arg_list, list)

        self._bot_name = '<@{0}>'.format(bot_name)
        self._cmd_list = cmd_list
        self._machine_name = None
        self._arg_list = dict()
        for arg_name in arg_list:
            self._arg_list[arg_name] = None
        self._cmd = None
        self._reminder = None
        self._error = None

    def has_error(self):
        return self._error is not None

    def has_cmd(self):
        return self._cmd in self._cmd_list

    def has_machine_name(self):
        return self._machine_name is not None and len(self._machine_name) > 0

    def has_reminder(self):
        return self._reminder is not None and len(self._reminder) > 0

    @property
    def cmd(self):
        return self._cmd

    @property
    def error(self):
        return self._error

    @property
    def reminder(self):
        return self._reminder

    @property
    def machine_name(self):
        return self._machine_name

    def has_arg(self, arg_name):

        try:
            return True if self._arg_list[arg_name] is not None else False
        except KeyError:
            return False

    def get_arg(self, arg_name):

        if self.has_arg(arg_name):
            return self._arg_list[arg_name]
        else:
            return None

    def _reset_state(self):

        for key in self._arg_list:
            self._arg_list[key] = None

        self._machine_name = None
        self._reminder = None
        self._cmd = None
        self._error = None

    def _read_bot_name(self, cmd_line):

        cmd_line = cmd_line.strip()

        if cmd_line.startswith('{0} '.format(self._bot_name)) or \
                        cmd_line.startswith(self._bot_name) and len(cmd_line) == len(self._bot_name):
                return True, cmd_line[len(self._bot_name):].strip()

        return False, cmd_line

    def _read_command(self, cmd_line):

        cmd_line = cmd_line.strip()
        if not cmd_line:
            return True, ''

        cmd = cmd_line.split(' ', 1)[0]

        if cmd not in self._cmd_list:
            raise Exception('unknown command {0}'.format(cmd))

        self._cmd = cmd

        return True, cmd_line[len(cmd):].strip()

    def _read_machine_name(self, cmd_line):

        cmd_line = cmd_line.strip()

        if not cmd_line:
            return True, ''

        self._machine_name = cmd_line.split(' ', 1)[0]

        return True, cmd_line[len(self._machine_name):].strip()

    def _read_argument_name(self, cmd_line):

        self._current_arg = ''

        cmd_line = cmd_line.strip()
        if not cmd_line:
            return True, ''

        self._current_arg = cmd_line.split(':', 1)[0]

        if self._current_arg not in self._arg_list:
            raise Exception('unknown argument name {0}'.format(self._current_arg))

        self._arg_list[self._current_arg] = ''

        return True, cmd_line[len(self._current_arg) + 1:]

    def _read_argument_value(self, cmd_line):

        if not cmd_line:
            return True, ''

        if cmd_line.startswith('"'):

            cmd_line = cmd_line[1:]

            try:
                idx = cmd_line.index('"')
                self._arg_list[self._current_arg] = cmd_line[:idx]

                return True, cmd_line[len(self._arg_list[self._current_arg]) + 1:].strip()

            except ValueError:
                raise Exception('invalid quotation of argument value for argument {0}.'.format(self._current_arg))

        else:
            if cmd_line.startswith(' '):
                self._arg_list[self._current_arg] = ''
                return True, cmd_line[1:].strip()

            self._arg_list[self._current_arg] = cmd_line.split(' ', 1)[0]
            return True, cmd_line[len(self._arg_list[self._current_arg]):].strip()

    def parse(self, cmd_line):

        self._reset_state()
        cmd_line = cmd_line.strip().replace('\t', ' ')
        self._reminder = cmd_line

        rc, self._reminder = self._read_bot_name(cmd_line)
        if rc is False:
            return False
        if not self._reminder:
            return True

        rc, self._reminder = self._read_command(self._reminder)
        if rc is False:
            return False

        rc, self._reminder = self._read_machine_name(self._reminder)

        if rc is False:
            return False

        while self._reminder:

            rc, self._reminder = self._read_argument_name(self._reminder)
            if not rc:
                return False

            rc, self._reminder = self._read_argument_value(self._reminder)
            if not rc:
                return False

        return True
