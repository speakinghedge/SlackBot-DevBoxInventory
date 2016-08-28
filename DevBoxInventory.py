"""
classes to manage development boxes
"""
import pickle
from sys import stderr


class DevBox(object):
    """
    represents a development box
    """
    def __init__(self, name, ip=None, user=None, comment=None):
        self._name = name
        self._ip = ip
        self._user = user
        self._comment = comment

    @property
    def name(self):
        return self._name

    @property
    def ip(self):
        return self._ip

    @ip.setter
    def ip(self, value):
        self._ip = value

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, value):
        self._user = value

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, value):
        self._comment = value


class DevBoxInventory(object):
    """
    manage a set of DevBoxes
    """
    def __init__(self, inventory_file):

        self._inventory_file = inventory_file
        self._inventory = []

        try:
            self._load()
        except IOError as err:
            try:
                self._save()
            except Exception as err:
                stderr.write(str(err))
                exit(1)
        except Exception as err:
            stderr.write(str(err))
            exit(1)

    def _save(self):

        try:
            with open(self._inventory_file, "wb") as inv_file:
                pickle.dump(self._inventory, inv_file)

                return len(self._inventory)

        except Exception as err:
            raise Exception('Failed to create inventory file in `{0}` cause: {1}'.format(self._inventory_file, err))

    def _load(self):

        try:
            with open(self._inventory_file, "rb") as inv_file:
                self._inventory = pickle.load(inv_file)

                return len(self._inventory)
        except IOError as err:
            if err.errno == 2:
                raise IOError('File not found')
            else:
                raise Exception('Failed to load inventory file from `{0}` cause: {1}'.format(self._inventory_file, err))
        except EOFError as err:
            raise Exception(
                'Failed to load inventory file from `{0}` cause file is empty or has invalid format.'.format(
                    self._inventory_file))

        except Exception as err:
            raise Exception('Failed to load inventory file from `{0}` cause: {1}'.format(self._inventory_file, err))

    def box_add(self, name, ip=None, user=None, comment=None):

        for box in self._inventory:
            if box.name == name:
                return 0

        self._inventory.append(DevBox(name, ip, user, comment))
        self._save()

        return 1

    def box_del(self, name):

        for box in self._inventory:

            if box.name == name:
                self._inventory.remove(box)
                self._save()
                return 1

        return 0

    def box_data_get(self, name):

        for box in self._inventory:

            if box.name == name:
                return box.name, box.ip, box.user, box.comment

        return None, None, None, None

    def box_data_set(self, name, ip=None, user=None, comment=None):

        for box in self._inventory:

            if box.name == name:
                if ip is not None:
                    box.ip = ip
                if user is not None:
                    box.user = user
                if comment is not None:
                    box.comment = comment
                self._save()
                return 1

        return 0

    def box_names(self):

        for box in self._inventory:
            yield box.name

    def box_datas(self):

        for box in self._inventory:
            yield box.name, box.ip, box.user, box.comment
