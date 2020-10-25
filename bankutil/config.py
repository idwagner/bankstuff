
import logging
from configparser import ConfigParser
from os import path, environ

DEFAULT_CONFIG = '~/.config/bankstuff.ini'

def load_config(filename):
    user_path = path.expanduser(filename)

    parser = ConfigParser()
    parser.read(user_path)
    return parser


class BankConfig(object):

    def __init__(self):

        self._configfile = DEFAULT_CONFIG
        if path.isfile(path.expanduser(self._configfile)):
            self._config = load_config(path.expanduser(self._configfile))

            env_section = environ.get('BANKSTUFF_CONFIG')
            self._section = env_section if env_section else self._config.default_section
        else:
            self._config = None
            self._section = None

    def get(self, option, *args, **kwargs):
        if not self._config:
            raise Exception('Config not loaded')

        return self._config.get(self._section, option, *args, **kwargs)

    def set(self, option, value):
        if not self._config:
            raise Exception('Config not loaded')

        self._config.set(self._section, option, value)
        with open(path.expanduser(self._configfile), 'w') as configfile:
            self._config.write(configfile)

    def has_option(self, option):
        if not self._config:
            raise Exception('Config not loaded')

        return self._config.has_option(self._section, option)

    def remove(self, option):
        self._config.remove_option(self._section, option)

    def reload(self, section=None, config_file=None):
        self._configfile = config_file if config_file else DEFAULT_CONFIG
        self._config = load_config(self._configfile)

        if section:
            if not self._config.has_section(section):
                raise Exception('Config does not have section %s', section)
            self._section = section
        else:
            section = self._config.default_section

CONF = BankConfig()
