class FilterModule(object):
    '''
    custom jinja2 filters for working with integers
    '''

    def filters(self):
        return {
            'int': self.int
        }

    def int(self, string, radix = None):
        if radix is not None:
            return int(string, radix)
        elif string.startswith("0"):
            return int(string, 8)
        elif string.startswith("0x"):
            return int(string[2:], 16)
        else:
            raise Error("Unable to guess radix of " + string)
