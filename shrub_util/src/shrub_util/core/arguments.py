import sys


class Arguments:
    """Purpose: Consistent argument parsing. Not using default packages to also switch
        to other configuration later on.
    Author: Mando van der Waarden
    Date: 2020/04/17
    Intro : Commandline arguments are passed to a python script when it is
        executed. The arguments can be accessed by the argv list in the sys package.
        Another name for these arguments are switches or options.
        This class assumes that the arguments are passed in a key/value way, where
        the key (argument name) is indicated with a switch character '-' and the
        value is the next argument. F.e.
        - commandline :
            > python test_args.py -key1 value1 -key2 value2
        - sys.argv :
            ['test_args.py', '-key1', 'value1', '-key2', 'value2']
        - python code
            arg = Argument()
            arg.get_arg('key1') = 'value1'
            arg.get_arg('key2') = 'value2'
    """

    def __init__(self, argv=None, switch_char="-"):
        if argv is None:
            self.argv = sys.argv
        else:
            self.argv = argv
        self.switch_char = switch_char

    def get_arg(self, name, default=None):
        """Get the argument by name. If not found the default value is used"""
        result = default
        i = 0
        # find the argument
        for arg in self.argv:
            if arg == self.switch_char + name:
                break
            i += 1
        # check for value following the argument
        if i < len(self.argv) - 1:
            result = self.argv[i + 1]
        # convert to integer if appropriate
        if type(default) is int:
            result = int(result)
        # convert to boolean if appropriate
        elif result is not None and type(default) is bool and type(result) is not bool:
            result = True if result == "true" else False

        return result

    def has_arg(self, name):
        """Check íf a command line argument exists"""
        if self.switch_char + name in self.argv:
            result = True
        else:
            result = False
        return result
