class ClapException(Exception):
    """The base exception for all clap-related exceptions"""


class CommandRegistrationError(ClapException):
    """There was a problem adding a command to the parser"""


class OptionRegistrationError(ClapException):
    """There was a problem adding an option to the parser"""


class ArgumentError(ClapException):
    """Represents an error that will be shown to the end user"""
